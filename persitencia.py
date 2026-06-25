# persistencia.py — v3 con Clave Compuesta Multi-Barrio
import json
import os




def generar_clave_registro(id_prestador, localidad_detalle):
    """Genera la clave única prestador + barrio/sector."""
    if id_prestador and localidad_detalle:
        return f"{id_prestador}_{localidad_detalle}"
    return None




def guardar_datos(datos):
    """
    Guarda o actualiza las respuestas indexadas por clave compuesta
    f"{id_prestador}_{localidad_detalle}". Antes del Paso 1.1 usa teléfono como fallback.
    """
    archivo = "respuestas_prestadores.json"


    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            try:
                lista_datos = json.load(f)
            except json.JSONDecodeError:
                lista_datos = []
    else:
        lista_datos = []


    clave = datos.get("clave_registro")
    if not clave:
        id_p = datos.get("id_prestador")
        loc = datos.get("localidad_detalle")
        if id_p and loc:
            clave = generar_clave_registro(id_p, loc)
            datos["clave_registro"] = clave


    encontrado = False


    if clave:
        for i, registro in enumerate(lista_datos):
            if registro.get("clave_registro") == clave:
                lista_datos[i].update(datos)
                encontrado = True
                break


    if not encontrado:
        telefono_actual = datos.get("telefono")
        for i, registro in enumerate(lista_datos):
            if registro.get("telefono") == telefono_actual and not registro.get("clave_registro"):
                lista_datos[i].update(datos)
                encontrado = True
                break


    if not encontrado:
        lista_datos.append(datos)


    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(lista_datos, f, ensure_ascii=False, indent=4)
