# motor.py — Máquina de Estados para Bot Conversacional de WhatsApp
# Relevamiento Anual de Prestadores (ANEXO I)
# Versión: 5.0 - Multi-Barrio, Flujo Lineal 0-25, Validaciones Reforzadas


import json
import os
from persistencia import guardar_datos, generar_clave_registro


# ============================================================================
# CONSTANTES Y CONFIGURACIÓN
# ============================================================================


PERFILES_PERSONAL = ["Profesionales", "Técnicos", "Administrativos", "Obreros", "Otros"]
TIPO_SERVICIO_AGUA_SOLO = 1
TIPO_SERVICIO_CLOACAS_SOLO = 2
TIPO_SERVICIO_AMBOS = 3


MSG_NUMERO_NEGATIVO = (
    "❌ El valor no puede ser negativo. Por favor, ingresá un número mayor o igual a cero."
)
MSG_FORMATO_NUMERO = (
    "❌ Formato incorrecto. Por favor, ingresá el dato usando solo números "
    "(por ejemplo: '4' en lugar de 'cuatro')."
)


# Mapeo de casilleros para el resumen de edición (Paso 25)
CASILLEROS_EDICION = {
    "1": ("poblacion_total_localidad", "Población total estimada de la localidad/barrio"),
    "2": ("conexiones_agua", "Conexiones de agua totales de la red"),
    "3": ("habitantes_por_conexion", "Habitantes promedio por hogar/conexión"),
    "4": ("habitantes_agua", "Población servida efectiva con red de agua"),
    "5": ("conexiones_medidas", "Conexiones con medidor domiciliario instalado"),
    "6": ("conexiones_activas", "Conexiones en servicio activo"),
    "7": ("caudal_agua_m3dia", "Caudal diario de agua (m³/día)"),
    "8": ("macromedidores_operativos_agua", "Macro-medidores operativos"),
    "9": ("longitud_red_agua_km", "Longitud total red de agua (km)"),
    "10": ("capacidad_almacenamiento_m3", "Capacidad de almacenamiento (m³)"),
    "11": ("conexiones_cloacas", "Conexiones cloacales residenciales activas"),
    "12": ("conexiones_cloacas_com_ind", "Conexiones cloacales comerciales/industriales/institucionales"),
    "13": ("habitantes_cloacas", "Población servida efectiva con red de cloacas"),
    "14": ("longitud_red_cloacas_km", "Longitud total red colectora cloacal (km)"),
    "15": ("caudal_cloacas_media", "Caudal diario cloacal promedio (m³/día)"),
    "16": ("reclamos_falta_presion", "Reclamos anuales por falta de presión de agua"),
    "17": ("reclamos_escape_calzada_vereda", "Reclamos anuales por escapes/fugas de agua"),
    "18": ("reclamos_medidores_rotos", "Reclamos anuales por medidores rotos/vandalizados"),
    "19": ("reclamos_obstruccion_cloacal", "Reclamos anuales por obstrucciones/desbordes cloacales"),
    "20": ("reclamos_errores_facturacion", "Reclamos anuales por errores en la facturación"),
    "21": ("cortes_servicio_falta_pago", "Cortes del servicio por falta de pago en el año"),
}


MAPEO_CAMPO_PASO = {
    "poblacion_total_localidad": 3,
    "conexiones_agua": 4,
    "habitantes_por_conexion": 4.1,
    "habitantes_agua": 5,
    "conexiones_medidas": 5.1,
    "conexiones_activas": 5.2,
    "caudal_agua_m3dia": 6,
    "macromedidores_operativos_agua": 11,
    "longitud_red_agua_km": 12,
    "capacidad_almacenamiento_m3": 13,
    "conexiones_cloacas": 15,
    "conexiones_cloacas_com_ind": 16,
    "habitantes_cloacas": 17,
    "longitud_red_cloacas_km": 18,
    "caudal_cloacas_media": 19,
    "reclamos_falta_presion": 21,
    "reclamos_escape_calzada_vereda": 22,
    "reclamos_medidores_rotos": 22.1,
    "reclamos_obstruccion_cloacal": 23,
    "reclamos_errores_facturacion": 23.1,
    "cortes_servicio_falta_pago": 24,
}


CAMPOS_SOLO_AGUA = {
    "conexiones_agua", "habitantes_por_conexion", "habitantes_agua",
    "conexiones_medidas", "conexiones_activas", "caudal_agua_m3dia",
    "macromedidores_operativos_agua", "longitud_red_agua_km", "capacidad_almacenamiento_m3",
    "reclamos_falta_presion", "reclamos_escape_calzada_vereda", "reclamos_medidores_rotos",
}


CAMPOS_SOLO_CLOACAS = {
    "conexiones_cloacas", "conexiones_cloacas_com_ind", "habitantes_cloacas",
    "longitud_red_cloacas_km", "caudal_cloacas_media", "reclamos_obstruccion_cloacal",
}




# ============================================================================
# FUNCIONES DE CARGA Y VALIDACIÓN DE PADRÓN
# ============================================================================


def cargar_padron_oficial():
    """Carga el padrón oficial de prestadores desde padron_prestadores.json."""
    archivo = "padron_prestadores.json"
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}




def validar_id_prestador(id_texto):
    """Valida que el ID existe en el padrón oficial."""
    try:
        id_numerico = str(int(id_texto.strip()))
        padron = cargar_padron_oficial()
        if id_numerico in padron:
            return True, padron[id_numerico]
        return False, None
    except ValueError:
        return False, None




def obtener_estado_registro(clave_registro):
    """Verifica el estado de un registro indexado por clave compuesta ID + barrio."""
    archivo = "respuestas_prestadores.json"
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                lista_datos = json.load(f)
                for registro in lista_datos:
                    if registro.get("clave_registro") == clave_registro:
                        return True, registro.get("estado_registro", "Incompleto")
        except (json.JSONDecodeError, IOError):
            pass
    return False, None




def _tiene_agua(tipo_servicio):
    return tipo_servicio in [TIPO_SERVICIO_AGUA_SOLO, TIPO_SERVICIO_AMBOS]




def _tiene_cloacas(tipo_servicio):
    return tipo_servicio in [TIPO_SERVICIO_CLOACAS_SOLO, TIPO_SERVICIO_AMBOS]




def _siguiente_despues_agua(datos):
    """Determina el paso posterior al módulo de agua (13.x)."""
    if _tiene_cloacas(datos["tipo_servicio"]):
        return 15
    return 21




# ============================================================================
# INICIALIZACIÓN DE SESIÓN
# ============================================================================


def crear_sesion_nueva(telefono):
    """Crea un diccionario de sesión inicial. El flujo comienza en paso 0 (PEDIR_ID)."""
    return {
        "telefono": telefono,
        "id_prestador": None,
        "nombre_prestador": None,
        "clave_registro": None,
        "estado_registro": "Incompleto",
        "paso_actual": 0,
        "paso_personal_actual": None,
        "perfil_personal_index": 0,
        "en_modo_edicion": False,
        "paso_edicion_previo": None,
        "bloqueado_por_completitud": False,
        "consulta_soporte": None,


        "localidad": None,
        "localidad_detalle": None,
        "referente": None,
        "poblacion_total_localidad": None,
        "tipo_servicio": None,


        "agua_tarifado": None,
        "cloacas_tarifado": None,


        "personal": {
            "Profesionales": {"dependencia": None, "contratados": None, "afectacion_agua": None, "afectacion_cloacas": None},
            "Técnicos": {"dependencia": None, "contratados": None, "afectacion_agua": None, "afectacion_cloacas": None},
            "Administrativos": {"dependencia": None, "contratados": None, "afectacion_agua": None, "afectacion_cloacas": None},
            "Obreros": {"dependencia": None, "contratados": None, "afectacion_agua": None, "afectacion_cloacas": None},
            "Otros": {"dependencia": None, "contratados": None, "afectacion_agua": None, "afectacion_cloacas": None},
        },


        "conexiones_agua": None,
        "habitantes_por_conexion": None,
        "habitantes_agua": None,
        "conexiones_medidas": None,
        "conexiones_activas": None,
        "caudal_agua_m3dia": None,
        "fuente_captacion_principal": None,
        "tiene_medidores_nuevos_año": None,
        "tiene_analisis_laboratorio_autocontrol": None,
        "tiene_balance_hidrico_mensual": None,
        "macromedidores_operativos_agua": None,
        "longitud_red_agua_km": None,
        "capacidad_almacenamiento_m3": None,
        "tiene_servicio_bidones": None,
        "tiene_tratamiento_agua_bidones": None,


        "conexiones_cloacas": None,
        "conexiones_cloacas_com_ind": None,
        "habitantes_cloacas": None,
        "longitud_red_cloacas_km": None,
        "caudal_cloacas_media": None,
        "tiene_infraestructura_cloacal_compleja": None,


        "reclamos_falta_presion": None,
        "reclamos_escape_calzada_vereda": None,
        "reclamos_medidores_rotos": None,
        "reclamos_obstruccion_cloacal": None,
        "reclamos_errores_facturacion": None,
        "cortes_servicio_falta_pago": None,
    }




# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================


def es_numero_valido(texto, permitir_cero=True):
    """
    Valida número digital estricto (entero o decimal). Rechaza valores negativos.
    Retorna: (es_válido: bool, valor: float o int o None)
    """
    try:
        valor = float(texto.strip())
        if valor < 0:
            return False, None
        if not permitir_cero and valor == 0:
            return False, valor
        return True, valor
    except ValueError:
        return False, None




def obtener_mensaje_error_numero(texto, permitir_cero=True):
    """Retorna el mensaje de error pedagógico correspondiente al input numérico."""
    try:
        valor = float(texto.strip())
        if valor < 0:
            return MSG_NUMERO_NEGATIVO
        if not permitir_cero and valor == 0:
            return "❌ El valor debe ser mayor a cero."
        return None
    except ValueError:
        return MSG_FORMATO_NUMERO




def es_opcion_valida(texto, opciones_validas):
    """Valida si el texto está en la lista de opciones válidas (comparación exacta)."""
    return texto.strip() in opciones_validas




def parsear_si_no(respuesta):
    """
    Acepta números (1/2) o texto libre (sí/si/no) de forma flexible.
    Retorna: (valido: bool, es_si: bool o None)
    """
    r = respuesta.strip().lower()
    if r in ("1", "sí", "si", "yes"):
        return True, True
    if r in ("2", "no"):
        return True, False
    return False, None




def es_saltar(respuesta):
    """Verifica si el usuario quiere saltear esta pregunta."""
    return respuesta.strip().lower() == "siguiente"




def _validar_y_guardar_numero(datos, respuesta, campo, paso_siguiente, permitir_saltar=True):
    """
    Helper interno para campos numéricos con modo edición.
    Retorna: (exito, mensaje_error)
    """
    if permitir_saltar and es_saltar(respuesta):
        datos[campo] = None
    else:
        valido, valor = es_numero_valido(respuesta)
        if not valido:
            return False, obtener_mensaje_error_numero(respuesta)
        datos[campo] = valor


    if datos.get("en_modo_edicion"):
        datos["en_modo_edicion"] = False
        datos["paso_actual"] = 25
    else:
        datos["paso_actual"] = paso_siguiente


    guardar_datos(datos)
    if datos.get("paso_actual") == 25 and not datos.get("en_modo_edicion"):
        return True, "✅ Actualizado. Volvemos al resumen..."
    return True, "✅ Anotado."




# ============================================================================
# FUNCIONES DE FLUJO DE CONVERSACIÓN
# ============================================================================


def obtener_proximo_paso(datos):
    """Calcula el próximo paso del flujo conversacional."""
    paso = datos["paso_actual"]
    tipo_servicio = datos["tipo_servicio"]


    if paso == 0:
        prompt = (
            "¡Hola! 👋 Te damos la bienvenida al asistente virtual para el Relevamiento Anual de Prestadores. "
            "Para empezar, por favor escribí tu *ID numérico de prestador* según el padrón oficial.\n\n"
            "💡 Este ID es fundamental para validar tu institución en nuestro registro."
        )
        return paso, prompt


    elif paso == 0.1:
        nombre = datos.get("nombre_prestador", "Institución")
        prompt = (
            f"¡Validación exitosa! 🎉 Bienvenida institución: *{nombre}*.\n\n"
            "¿Qué deseas hacer hoy?\n"
            "1 - Iniciar o continuar la carga del Relevamiento Anual (ANEXO I)\n"
            "2 - Ponerme en contacto con el equipo técnico (Consultas/Soporte)\n\n"
            "Respondé solo con el número de opción (1 o 2)."
        )
        return paso, prompt


    elif paso == 0.2:
        prompt = (
            "Por favor, escribí tu consulta técnica detallada a continuación. "
            "Un asesor se comunicará con vos a la brevedad: 🛠️"
        )
        return paso, prompt


    elif paso == 1:
        prompt = "¿A qué *Localidad o Paraje* pertenece la institución?"
        return paso, prompt


    elif paso == 1.1:
        prompt = (
            "Escribí el nombre del *Barrio, Paraje o Sector* específico al que corresponden "
            "los datos que vas a cargar en esta sesión (Ej: 'Zona Centro', 'Barrio Malvinas'):"
        )
        return paso, prompt


    elif paso == 2:
        prompt = "¿Cuál es el nombre del *referente o contacto principal* para el relevamiento?"
        return paso, prompt


    elif paso == 3:
        prompt = (
            "¿Cuál es la *población total estimada* de la localidad/barrio "
            "(habitantes totales del área de servicio)?"
        )
        return paso, prompt


    elif paso == 3.1:
        prompt = (
            "¿Qué tipo de servicio brinda la institución?\n"
            "1 - Solo Agua\n"
            "2 - Solo Cloacas\n"
            "3 - Ambos\n\n"
            "Respondé solo con el número."
        )
        return paso, prompt


    elif paso == 3.2:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 3.3
            return obtener_proximo_paso(datos)
        prompt = (
            "¿El servicio de AGUA POTABLE es tarifado?\n"
            "1 - Sí (Medido o Tasa)\n"
            "2 - No (Gratuito/Subvencionado)"
        )
        return paso, prompt


    elif paso == 3.3:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 3.4
            return obtener_proximo_paso(datos)
        prompt = (
            "¿El servicio de DESAGÜES CLOACALES es tarifado?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 3.4:
        if datos["paso_personal_actual"] is None:
            datos["paso_personal_actual"] = "dependencia"
            datos["perfil_personal_index"] = 0
        return obtener_paso_personal(datos)


    elif paso == 4:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Cuántas *conexiones de agua* totales tiene la red actualmente? "
            "(Si no tenés este dato, escribí 'siguiente')."
        )
        return paso, prompt


    elif paso == 4.1:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Cuántos *habitantes promedio por hogar/conexión* estimás? "
            "(Admite decimales, ej: 3.5)"
        )
        return paso, prompt


    elif paso == 5:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = "¿A cuántos *habitantes* abastece efectivamente con la red de agua potable? (Población servida)"
        return paso, prompt


    elif paso == 5.1:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "Del total de conexiones de agua, ¿cuántas cuentan con *medidor domiciliario instalado*? "
            "(Conexiones medidas):"
        )
        return paso, prompt


    elif paso == 5.2:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = "De las conexiones totales, ¿cuántas se encuentran actualmente en *servicio activo*?:"
        return paso, prompt


    elif paso == 6:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = "¿Cuál es el *caudal diario de agua* promedio liberado a la red (en m³/día)?"
        return paso, prompt


    elif paso == 7:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "Elegí el tipo de *Fuente de Captación* principal:\n"
            "1 - Subterránea (Pozos)\n"
            "2 - Superficial (Río / Planta)\n"
            "3 - Compra en bloque / Acueducto\n"
            "4 - Combinada / Otra\n\n"
            "Respondé solo con el número."
        )
        return paso, prompt


    elif paso == 8:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Instalaron medidores domiciliarios nuevos durante el último año?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 9:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Realizan análisis de autocontrol de laboratorio en almacenamiento o red?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 10:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Llevan un registro de Balance Hídrico mensual del sistema?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 11:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántos *macro-medidores operativos* tienen instalados a la salida de las fuentes o plantas?"
        return paso, prompt


    elif paso == 12:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = "¿Cuál es la *longitud total de la red de distribución* de agua (en kilómetros)?"
        return paso, prompt


    elif paso == 13:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15
            return obtener_proximo_paso(datos)
        prompt = (
            "¿Cuál es la *capacidad de almacenamiento total* del sistema "
            "(suma de cisternas y tanques en m³)?"
        )
        return paso, prompt


    elif paso == 13.1:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 15 if _tiene_cloacas(tipo_servicio) else 21
            return obtener_proximo_paso(datos)
        prompt = (
            "¿La institución cuenta con servicio de distribución de agua en bidones?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 13.2:
        if not _tiene_agua(tipo_servicio) or not datos.get("tiene_servicio_bidones"):
            datos["paso_actual"] = _siguiente_despues_agua(datos)
            return obtener_proximo_paso(datos)
        prompt = (
            "Indique si existe un *tratamiento específico del agua* "
            "(ej. remoción de arsénico/flúor o filtrado complejo) previo al retiro en bidones:\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 15:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántas *conexiones cloacales residenciales* activas tiene la red actualmente?"
        return paso, prompt


    elif paso == 16:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántas *conexiones cloacales comerciales, industriales o institucionales* activas tienen?"
        return paso, prompt


    elif paso == 17:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = "¿A cuántos *habitantes* conecta efectivamente la red de desagües cloacales?"
        return paso, prompt


    elif paso == 18:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = "¿Cuál es la *longitud total de la red colectora* cloacal (en kilómetros)?"
        return paso, prompt


    elif paso == 19:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = "¿Cuál es el *caudal diario cloacal* promedio que ingresa a la planta (en m³/día)?"
        return paso, prompt


    elif paso == 20:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 21
            return obtener_proximo_paso(datos)
        prompt = (
            "¿El sistema cuenta con infraestructura compleja como colectores principales, "
            "estaciones de bombeo o planta de tratamiento de líquidos cloacales?\n"
            "1 - Sí\n"
            "2 - No"
        )
        return paso, prompt


    elif paso == 21:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 23
            return obtener_proximo_paso(datos)
        prompt = (
            "Pasamos al módulo de Reclamos y Atención. 📞 "
            "¿Cuántos reclamos anuales registraron por *Falta de presión de agua*?"
        )
        return paso, prompt


    elif paso == 22:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 23
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántos reclamos anuales registraron por *Escapes o Fugas de agua* en calzada o vereda?"
        return paso, prompt


    elif paso == 22.1:
        if not _tiene_agua(tipo_servicio):
            datos["paso_actual"] = 23
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántos reclamos anuales registraron por *Medidores rotos o vandalizados*?"
        return paso, prompt


    elif paso == 23:
        if not _tiene_cloacas(tipo_servicio):
            datos["paso_actual"] = 23.1
            return obtener_proximo_paso(datos)
        prompt = "¿Cuántos reclamos anuales registraron por *Obstrucciones domiciliarias o desbordes cloacales*?"
        return paso, prompt


    elif paso == 23.1:
        prompt = (
            "¿Cuántos reclamos anuales registraron por *Errores en la facturación* "
            "(datos erróneos o montos incorrectos)?"
        )
        return paso, prompt


    elif paso == 24:
        prompt = (
            "Por último, en relación a Facturación comercial: "
            "¿Cuántos *cortes efectivos del servicio por falta de pago* realizaron en el último año?"
        )
        return paso, prompt


    elif paso == 25:
        return generar_resumen_edicion(datos)


    return paso, "Error: paso desconocido."




def obtener_paso_personal(datos):
    """Maneja el módulo dinámico de Personal con Doble Afectación (Paso 3.4)."""
    tipo_servicio = datos["tipo_servicio"]
    perfil_index = datos["perfil_personal_index"]
    paso_personal = datos["paso_personal_actual"]
    perfil_actual = PERFILES_PERSONAL[perfil_index]
    paso_actual_total = 3.4


    if paso_personal == "dependencia":
        prompt = f"*{perfil_actual}*: ¿Cuántos en relación de dependencia (Sueldos/Salarios)?"
        return paso_actual_total, prompt


    elif paso_personal == "contratados":
        prompt = f"*{perfil_actual}*: ¿Cuántos contratados (Honorarios/Prestaciones)?"
        return paso_actual_total, prompt


    elif paso_personal == "afectacion_agua":
        personal_datos = datos["personal"][perfil_actual]
        total_personal = (personal_datos["dependencia"] or 0) + (personal_datos["contratados"] or 0)


        if total_personal == 0:
            datos["personal"][perfil_actual]["afectacion_agua"] = 0
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 0
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
                return obtener_paso_personal(datos)
            datos["paso_actual"] = 4
            datos["paso_personal_actual"] = None
            return obtener_proximo_paso(datos)


        if tipo_servicio == TIPO_SERVICIO_AGUA_SOLO:
            datos["personal"][perfil_actual]["afectacion_agua"] = 100
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 0
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
                return obtener_paso_personal(datos)
            datos["paso_actual"] = 4
            datos["paso_personal_actual"] = None
            return obtener_proximo_paso(datos)


        elif tipo_servicio == TIPO_SERVICIO_CLOACAS_SOLO:
            datos["personal"][perfil_actual]["afectacion_agua"] = 0
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 100
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
                return obtener_paso_personal(datos)
            datos["paso_actual"] = 4
            datos["paso_personal_actual"] = None
            return obtener_proximo_paso(datos)


        prompt = f"*{perfil_actual}*: ¿Qué % de afectación al servicio de AGUA POTABLE? (0-100)"
        return paso_actual_total, prompt


    elif paso_personal == "afectacion_cloacas":
        prompt = f"*{perfil_actual}*: ¿Qué % de afectación al servicio de DESAGÜES CLOACALES? (0-100)"
        return paso_actual_total, prompt


    return paso_actual_total, "Error en módulo de personal."




def procesar_respuesta_personal(datos, respuesta):
    """Procesa la respuesta del usuario en el módulo de Personal (Paso 3.4)."""
    tipo_servicio = datos["tipo_servicio"]
    perfil_index = datos["perfil_personal_index"]
    paso_personal = datos["paso_personal_actual"]
    perfil_actual = PERFILES_PERSONAL[perfil_index]


    if es_saltar(respuesta):
        valor = None
    else:
        valido, valor = es_numero_valido(respuesta)
        if not valido:
            return False, obtener_mensaje_error_numero(respuesta)


    if paso_personal == "dependencia":
        datos["personal"][perfil_actual]["dependencia"] = valor
        datos["paso_personal_actual"] = "contratados"


    elif paso_personal == "contratados":
        datos["personal"][perfil_actual]["contratados"] = valor
        datos["paso_personal_actual"] = "afectacion_agua"


        total_personal = (datos["personal"][perfil_actual]["dependencia"] or 0) + (valor if valor is not None else 0)


        if total_personal == 0:
            datos["personal"][perfil_actual]["afectacion_agua"] = 0
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 0
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
            else:
                datos["paso_actual"] = 4
                datos["paso_personal_actual"] = None


        elif tipo_servicio == TIPO_SERVICIO_AGUA_SOLO:
            datos["personal"][perfil_actual]["afectacion_agua"] = 100
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 0
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
            else:
                datos["paso_actual"] = 4
                datos["paso_personal_actual"] = None


        elif tipo_servicio == TIPO_SERVICIO_CLOACAS_SOLO:
            datos["personal"][perfil_actual]["afectacion_agua"] = 0
            datos["personal"][perfil_actual]["afectacion_cloacas"] = 100
            datos["perfil_personal_index"] += 1
            if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
                datos["paso_personal_actual"] = "dependencia"
            else:
                datos["paso_actual"] = 4
                datos["paso_personal_actual"] = None


    elif paso_personal == "afectacion_agua":
        if valor is not None and (valor < 0 or valor > 100):
            return False, "❌ El porcentaje debe estar entre 0 y 100."
        datos["personal"][perfil_actual]["afectacion_agua"] = valor
        datos["paso_personal_actual"] = "afectacion_cloacas"


    elif paso_personal == "afectacion_cloacas":
        if valor is not None and (valor < 0 or valor > 100):
            return False, "❌ El porcentaje debe estar entre 0 y 100."


        afectacion_agua = datos["personal"][perfil_actual]["afectacion_agua"] or 0
        afectacion_cloacas = valor if valor is not None else 0
        if afectacion_agua + afectacion_cloacas > 100:
            return False, (
                "❌ La suma de las afectaciones supera el 100% de la jornada laboral de este perfil. "
                "Ingresá el % de cloacas correcto."
            )


        datos["personal"][perfil_actual]["afectacion_cloacas"] = valor
        datos["perfil_personal_index"] += 1
        if datos["perfil_personal_index"] < len(PERFILES_PERSONAL):
            datos["paso_personal_actual"] = "dependencia"
        else:
            datos["paso_actual"] = 4
            datos["paso_personal_actual"] = None


    guardar_datos(datos)
    return True, None




def _casillero_aplica(campo, tipo_servicio):
    """Determina si un casillero aplica según el tipo de servicio."""
    if campo in CAMPOS_SOLO_AGUA and not _tiene_agua(tipo_servicio):
        return False
    if campo in CAMPOS_SOLO_CLOACAS and not _tiene_cloacas(tipo_servicio):
        return False
    return True




def generar_resumen_edicion(datos):
    """Genera el resumen consolidado para edición final (Paso 25)."""
    tipo_servicio = datos["tipo_servicio"]
    resumen_lineas = ["📋 *RESUMEN DE DATOS CARGADOS:*\n"]


    if datos.get("localidad_detalle"):
        resumen_lineas.append(f"*Barrio/Sector:* {datos['localidad_detalle']}")


    for num, (campo, descripcion) in CASILLEROS_EDICION.items():
        if not _casillero_aplica(campo, tipo_servicio):
            continue
        val = datos.get(campo)
        resumen_lineas.append(
            f"*Casillero {num}:* {descripcion}: {val if val is not None else '(no cargado)'}"
        )


    resumen_lineas.append("\n¿Los datos son correctos?")
    resumen_lineas.append("👉 Respondé *ENVIAR* para finalizar")
    resumen_lineas.append("👉 O respondé el número del casillero que querés corregir (Ej: 4)")


    return 25, "\n".join(resumen_lineas)




# ============================================================================
# PROCESAMIENTO DE RESPUESTAS
# ============================================================================


def procesar_respuesta(datos, respuesta_usuario):
    """Procesa la respuesta del usuario según el paso actual."""
    paso = datos["paso_actual"]


    if paso == 0:
        es_valido, nombre_oficial = validar_id_prestador(respuesta_usuario)
        if not es_valido:
            return False, (
                "❌ El ID ingresado no existe en el padrón oficial. "
                "Por favor, verificá el número e intentá de nuevo."
            )


        id_numerico = str(int(respuesta_usuario.strip()))
        datos["id_prestador"] = id_numerico
        datos["nombre_prestador"] = nombre_oficial
        datos["paso_actual"] = 0.1
        guardar_datos(datos)
        return True, ""


    elif paso == 0.1:
        if datos.get("bloqueado_por_completitud"):
            if not es_opcion_valida(respuesta_usuario, ["1", "2"]):
                return False, "❌ Por favor, respondé con 1 o 2."
            if respuesta_usuario.strip() == "1":
                datos["paso_actual"] = 0.2
                guardar_datos(datos)
                return True, ""
            return True, "👋 Gracias. Escribí *hola* cuando quieras volver a ingresar."


        if not es_opcion_valida(respuesta_usuario, ["1", "2"]):
            return False, "❌ Por favor, respondé con 1 o 2."


        if respuesta_usuario.strip() == "1":
            datos["paso_actual"] = 1
            guardar_datos(datos)
            return True, "🚀 ¡Excelente! Iniciamos el cuestionario."
        datos["paso_actual"] = 0.2
        guardar_datos(datos)
        return True, ""


    elif paso == 0.2:
        consulta = respuesta_usuario.strip()
        if not consulta:
            return False, "❌ Por favor, escribí tu consulta técnica."


        datos["consulta_soporte"] = consulta
        datos["estado_registro"] = "Consulta_Soporte"
        datos["paso_actual"] = 0.1
        datos["bloqueado_por_completitud"] = False
        guardar_datos(datos)
        return True, (
            "✅ ¡Gracias! Tu consulta ha sido registrada. "
            "Un asesor se comunicará con vos a la brevedad. 📞\n\n"
            "¿Deseas hacer algo más?"
        )


    elif paso == 1:
        localidad = respuesta_usuario.strip()
        if not localidad:
            return False, "❌ Por favor, escribí la localidad."
        datos["localidad"] = localidad
        datos["paso_actual"] = 1.1
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 1.1:
        detalle = respuesta_usuario.strip()
        if not detalle:
            return False, "❌ Por favor, escribí el nombre del barrio, paraje o sector."


        datos["localidad_detalle"] = detalle
        clave = generar_clave_registro(datos["id_prestador"], detalle)
        datos["clave_registro"] = clave


        existe, estado = obtener_estado_registro(clave)
        if existe and estado == "Completo":
            datos["bloqueado_por_completitud"] = True
            datos["paso_actual"] = 0.1
            guardar_datos(datos)
            nombre = datos.get("nombre_prestador", "Institución")
            return True, (
                f"⚠️ El prestador *{nombre}* ya completó el relevamiento para "
                f"*{detalle}* (Localidad: {datos.get('localidad', '')}).\n\n"
                "¿Qué necesitás hacer?\n"
                "1 - Dejar una consulta de soporte/corrección\n"
                "2 - Salir"
            )


        datos["paso_actual"] = 2
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 2:
        referente = respuesta_usuario.strip()
        if not referente:
            return False, "❌ Por favor, escribí el nombre del referente."
        datos["referente"] = referente
        datos["paso_actual"] = 3
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 3:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "poblacion_total_localidad", 3.1, permitir_saltar=False)
        return exito, msg


    elif paso == 3.1:
        if not es_opcion_valida(respuesta_usuario, ["1", "2", "3"]):
            return False, "❌ Por favor, respondé con 1, 2 o 3."
        datos["tipo_servicio"] = int(respuesta_usuario.strip())
        datos["paso_actual"] = 3.2
        guardar_datos(datos)
        return True, "✅ Registrado."


    elif paso == 3.2:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["agua_tarifado"] = 1 if es_si else 2
        datos["paso_actual"] = 3.3
        guardar_datos(datos)
        return True, "✅ Registrado."


    elif paso == 3.3:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["cloacas_tarifado"] = 1 if es_si else 2
        datos["paso_actual"] = 3.4
        guardar_datos(datos)
        return True, "✅ Registrado."


    elif paso == 3.4:
        exito, mensaje = procesar_respuesta_personal(datos, respuesta_usuario)
        if not exito:
            return False, mensaje
        return True, "✅ Anotado."


    elif paso == 4:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "conexiones_agua", 4.1)
        return exito, msg


    elif paso == 4.1:
        if datos.get("en_modo_edicion"):
            if es_saltar(respuesta_usuario):
                datos["habitantes_por_conexion"] = None
            else:
                valido, valor = es_numero_valido(respuesta_usuario)
                if not valido:
                    return False, obtener_mensaje_error_numero(respuesta_usuario)
                datos["habitantes_por_conexion"] = valor
            datos["en_modo_edicion"] = False
            datos["paso_actual"] = 25
            guardar_datos(datos)
            return True, "✅ Actualizado. Volvemos al resumen..."
        if es_saltar(respuesta_usuario):
            datos["habitantes_por_conexion"] = None
        else:
            valido, valor = es_numero_valido(respuesta_usuario)
            if not valido:
                return False, obtener_mensaje_error_numero(respuesta_usuario)
            datos["habitantes_por_conexion"] = valor
        datos["paso_actual"] = 5
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 5:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "habitantes_agua", 5.1)
        return exito, msg


    elif paso == 5.1:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "conexiones_medidas", 5.2)
        return exito, msg


    elif paso == 5.2:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "conexiones_activas", 6)
        return exito, msg


    elif paso == 6:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "caudal_agua_m3dia", 7)
        return exito, msg


    elif paso == 7:
        if not es_opcion_valida(respuesta_usuario, ["1", "2", "3", "4"]):
            return False, "❌ Respondé con 1, 2, 3 o 4."
        datos["fuente_captacion_principal"] = int(respuesta_usuario.strip())
        datos["paso_actual"] = 8
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 8:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_medidores_nuevos_año"] = es_si
        datos["paso_actual"] = 9
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 9:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_analisis_laboratorio_autocontrol"] = es_si
        datos["paso_actual"] = 10
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 10:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_balance_hidrico_mensual"] = es_si
        datos["paso_actual"] = 11
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 11:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "macromedidores_operativos_agua", 12)
        return exito, msg


    elif paso == 12:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "longitud_red_agua_km", 13)
        return exito, msg


    elif paso == 13:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "capacidad_almacenamiento_m3", 13.1)
        return exito, msg


    elif paso == 13.1:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_servicio_bidones"] = es_si
        if es_si:
            datos["paso_actual"] = 13.2
        else:
            datos["tiene_tratamiento_agua_bidones"] = None
            datos["paso_actual"] = _siguiente_despues_agua(datos)
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 13.2:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_tratamiento_agua_bidones"] = es_si
        datos["paso_actual"] = _siguiente_despues_agua(datos)
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 15:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "conexiones_cloacas", 16)
        return exito, msg


    elif paso == 16:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "conexiones_cloacas_com_ind", 17)
        return exito, msg


    elif paso == 17:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "habitantes_cloacas", 18)
        return exito, msg


    elif paso == 18:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "longitud_red_cloacas_km", 19)
        return exito, msg


    elif paso == 19:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "caudal_cloacas_media", 20)
        return exito, msg


    elif paso == 20:
        valido, es_si = parsear_si_no(respuesta_usuario)
        if not valido:
            return False, "❌ Respondé con 1 (Sí) o 2 (No)."
        datos["tiene_infraestructura_cloacal_compleja"] = es_si
        datos["paso_actual"] = 21
        guardar_datos(datos)
        return True, "✅ Anotado."


    elif paso == 21:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "reclamos_falta_presion", 22)
        return exito, msg


    elif paso == 22:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "reclamos_escape_calzada_vereda", 22.1)
        return exito, msg


    elif paso == 22.1:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "reclamos_medidores_rotos", 23)
        return exito, msg


    elif paso == 23:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "reclamos_obstruccion_cloacal", 23.1)
        return exito, msg


    elif paso == 23.1:
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "reclamos_errores_facturacion", 24)
        return exito, msg


    elif paso == 24:
        en_edicion = datos.get("en_modo_edicion")
        exito, msg = _validar_y_guardar_numero(datos, respuesta_usuario, "cortes_servicio_falta_pago", 25)
        if not exito:
            return False, msg
        if en_edicion:
            return True, "✅ Actualizado. Volvemos al resumen..."
        return True, "✅ ¡Perfecto! Vamos al resumen final..."


    elif paso == 25:
        respuesta_limpia = respuesta_usuario.strip().upper()


        if respuesta_limpia == "ENVIAR":
            datos["estado_registro"] = "Completo"
            guardar_datos(datos)
            _, mensaje_final = generar_mensaje_final(datos)
            return True, mensaje_final


        if respuesta_limpia in CASILLEROS_EDICION:
            clave_campo, descripcion = CASILLEROS_EDICION[respuesta_limpia]
            if not _casillero_aplica(clave_campo, datos["tipo_servicio"]):
                return False, "❌ Ese casillero no aplica para tu tipo de servicio."


            paso_original = MAPEO_CAMPO_PASO.get(clave_campo)
            if paso_original:
                datos["en_modo_edicion"] = True
                datos["paso_edicion_previo"] = paso_original
                datos["paso_actual"] = paso_original
                guardar_datos(datos)
                return True, f"✅ Editando: {descripcion}"
            return False, "❌ Casillero no encontrado."


        max_casillero = max(int(k) for k in CASILLEROS_EDICION.keys())
        return False, f"❌ Respondé 'ENVIAR' para finalizar o el número del casillero a corregir (1-{max_casillero})."


    return False, "Error: paso desconocido."




def generar_mensaje_final(datos):
    """Genera el mensaje final de despedida."""
    flags_complejos = [
        datos.get("fuente_captacion_principal") in [2, 3, 4],
        datos.get("tiene_medidores_nuevos_año", False),
        datos.get("tiene_balance_hidrico_mensual", False),
        datos.get("tiene_analisis_laboratorio_autocontrol", False),
        datos.get("tiene_infraestructura_cloacal_compleja", False),
        datos.get("tiene_tratamiento_agua_bidones", False),
    ]


    if any(flags_complejos):
        mensaje = (
            "¡Gracias! 🎉 Los datos del relevamiento anual fueron registrados correctamente.\n\n"
            "Notamos que tu institución cuenta con módulos técnicos detallados "
            "(como balances hídricos, muestreos de laboratorio o plantas de tratamiento). "
            "Para completar el 100% del Anexo I, en las próximas horas nos comunicaremos "
            "con el referente para coordinar el envío de las planillas Excel complementarias. "
            "¡Muchas gracias por tu tiempo y colaboración! 👋"
        )
    else:
        mensaje = (
            "¡Gracias! 🎉 Los datos del relevamiento anual fueron registrados correctamente "
            "en la base de datos. Si necesitás cargar otro barrio o prestador, simplemente escribí *hola* "
            "para volver a comenzar."
        )


    return 25, mensaje




# ============================================================================
# FUNCIÓN PRINCIPAL DEL MOTOR
# ============================================================================


def procesar_mensaje(telefono, mensaje_usuario, sesion_actual=None):
    """Coordina todo el flujo conversacional del bot."""
    if sesion_actual is None:
        sesion_actual = crear_sesion_nueva(telefono)


    paso_actual = sesion_actual["paso_actual"]


    if paso_actual == 0 and mensaje_usuario.strip().lower() in ["hola", "hi", "hey", "inicio", "comenzar"]:
        _, prompt = obtener_proximo_paso(sesion_actual)
        return {
            "exito": True,
            "mensaje_respuesta": "",
            "mensaje_proximo_prompt": prompt,
            "datos_sesion": sesion_actual,
        }


    if paso_actual == 25 and mensaje_usuario.strip().lower() == "hola":
        sesion_actual = crear_sesion_nueva(telefono)
        _, prompt = obtener_proximo_paso(sesion_actual)
        return {
            "exito": True,
            "mensaje_respuesta": "",
            "mensaje_proximo_prompt": prompt,
            "datos_sesion": sesion_actual,
        }


    exito, mensaje_respuesta = procesar_respuesta(sesion_actual, mensaje_usuario)


    if not exito:
        _, prompt = obtener_proximo_paso(sesion_actual)
        return {
            "exito": False,
            "mensaje_respuesta": mensaje_respuesta,
            "mensaje_proximo_prompt": prompt,
            "datos_sesion": sesion_actual,
        }


    if sesion_actual.get("en_modo_edicion") and sesion_actual["paso_actual"] != 25:
        sesion_actual["paso_actual"] = 25
        sesion_actual["en_modo_edicion"] = False
        guardar_datos(sesion_actual)


    _, proximo_prompt = obtener_proximo_paso(sesion_actual)


    return {
        "exito": True,
        "mensaje_respuesta": mensaje_respuesta,
        "mensaje_proximo_prompt": proximo_prompt,
        "datos_sesion": sesion_actual,
    }
