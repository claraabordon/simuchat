# Simple Flask wrapper to serve a friendly web UI for the Relevamiento chat engine
from flask import Flask, render_template, request, jsonify
import os
import json
from motor import procesar_mensaje, crear_sesion_nueva

app = Flask(__name__)

# Sessions stored in memory for simplicity; for production use a persistent store.
SESSIONS_FILE = "sessions.json"

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.json or {}
    telefono = data.get("telefono") or "+5490000000000"
    mensaje = data.get("mensaje", "")

    sessions = load_sessions()
    session = sessions.get(telefono)
    if session is None:
        session = crear_sesion_nueva(telefono)
        sessions[telefono] = session

    # Procesar el mensaje usando el motor
    respuesta = procesar_mensaje(telefono, mensaje, sesion_actual=session)

    # Guardar sesión actualizada
    sessions[telefono] = respuesta.get("datos_sesion", session)
    save_sessions(sessions)

    return jsonify(respuesta)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
