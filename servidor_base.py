import random
import time
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)

# Diccionario principal de sensores.
# Cada sensor tiene: valor (numérico) y unidad (string).
# La simulación actualiza los valores cada 5 segundos.
sensores = {
    "temperatura": {"valor": round(random.uniform(15, 35), 1), "unidad": "°C"},
    "humedad": {"valor": round(random.uniform(40, 90), 1), "unidad": "%"},
    "luz": {"valor": round(random.uniform(0, 100), 1), "unidad": "%"},
    "viento": {"valor": round(random.uniform(0, 60), 1), "unidad": "km/h"},
}

# Diccionario de actuadores.
# Cada actuador tiene un estado (ON/OFF, OPEN/CLOSED).
# Se pueden controlar vía POST desde cualquier cliente HTTP.
actuadores = {
    "led": {"estado": "OFF"},
    "ventilador": {"estado": "OFF"},
    "rele": {"estado": "OPEN"},
}


# ============================================================
# ENDPOINTS
# ============================================================


@app.route("/")
def home():
    return "<h1>API IoT - Raspberry Pi Zero</h1><p>Endpoints: /status, /sensores, /sensor/&lt;nombre&gt;, /actuadores, /actuador/&lt;nombre&gt;, /docs</p>"


@app.route("/status")
def status():
    return jsonify({"status": "ok", "dispositivo": "Raspberry Pi Zero W", "clase": 10})


@app.route("/docs")
def documentacion():
    return """
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>API Docs</title></head>
<body style="font-family:Arial;max-width:800px;margin:auto;padding:20px;">
<h1> Documentación de la API</h1>
<p>Base URL: <code>http://&lt;IP-de-la-Pi&gt;:5000</code></p>
<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%;">
<tr style="background:#0f172a;color:white;"><th>Método</th><th>Endpoint</th><th>Descripción</th><th>Ejemplo</th></tr>
<tr><td>GET</td><td>/</td><td>Home HTML</td><td><code>curl http://localhost:5000/</code></td></tr>
<tr><td>GET</td><td>/status</td><td>Estado del servidor</td><td><code>curl http://localhost:5000/status</code></td></tr>
<tr><td>GET</td><td>/sensores</td><td>Todos los sensores</td><td><code>curl http://localhost:5000/sensores</code></td></tr>
<tr><td>GET</td><td>/sensor/temperatura</td><td>Un sensor específico</td><td><code>curl http://localhost:5000/sensor/temperatura</code></td></tr>
<tr><td>GET</td><td>/actuadores</td><td>Todos los actuadores</td><td><code>curl http://localhost:5000/actuadores</code></td></tr>
<tr><td>GET</td><td>/actuador/led</td><td>Estado de un actuador</td><td><code>curl http://localhost:5000/actuador/led</code></td></tr>
<tr><td>POST</td><td>/actuador/led</td><td>Controlar actuador</td><td><code>curl -X POST -H "Content-Type: application/json" -d '{"estado":"ON"}' http://localhost:5000/actuador/led</code></td></tr>
</table>
<h2> Probar desde el navegador</h2>
<p>Abrí http://&lt;IP-de-la-Pi&gt;:5000/sensores en cualquier dispositivo de la misma red.</p>
</body></html>"""


@app.route("/sensores")
def listar_sensores():
    return jsonify(sensores)


@app.route("/sensor/<nombre>")
def leer_sensor(nombre):
    if nombre in sensores:
        return jsonify({"nombre": nombre, **sensores[nombre]})
    return jsonify(
        {
            "error": f"Sensor '{nombre}' no encontrado",
            "sensores_disponibles": list(sensores.keys()),
        }
    ), 404


@app.route("/actuadores")
def listar_actuadores():
    return jsonify(actuadores)


@app.route("/actuador/<nombre>", methods=["GET", "POST"])
def controlar_actuador(nombre):
    if nombre not in actuadores:
        return jsonify(
            {
                "error": f"Actuador '{nombre}' no encontrado",
                "actuadores_disponibles": list(actuadores.keys()),
            }
        ), 404

    if request.method == "POST":
        # Flask convierte automáticamente el JSON del body en un diccionario Python
        datos = request.get_json(silent=True)  # silent=True evita error si no hay JSON

        if datos is None:
            return jsonify(
                {"error": 'El cuerpo debe ser JSON válido. Ej: {"estado": "ON"}'}
            ), 400

        if "estado" not in datos:
            return jsonify(
                {"error": 'Falta el campo \'estado\'. Ej: {"estado": "ON"}'}
            ), 400

        nuevo_estado = datos["estado"].upper()
        # Validar que el estado sea válido según el tipo de actuador
        if nombre == "rele" and nuevo_estado not in ("OPEN", "CLOSED"):
            return jsonify(
                {"error": "Estado inválido para rele. Usá OPEN o CLOSED"}
            ), 400
        if nombre in ("led", "ventilador") and nuevo_estado not in ("ON", "OFF"):
            return jsonify(
                {"error": f"Estado inválido para {nombre}. Usá ON u OFF"}
            ), 400

        actuadores[nombre]["estado"] = nuevo_estado
        print(f" [ACCION] {nombre} -> {nuevo_estado}")

    return jsonify({"nombre": nombre, **actuadores[nombre]})


# ============================================================
# SIMULACION EN SEGUNDO PLANO
# ============================================================
# Esta función corre en un hilo separado (threading).
# Mientras Flask atiende solicitudes HTTP, este hilo actualiza
# los valores de los sensores cada 5 segundos con valores aleatorios.


def simular_sensores():
    while True:
        sensores["temperatura"]["valor"] = round(random.uniform(15, 35), 1)
        sensores["humedad"]["valor"] = round(random.uniform(40, 90), 1)
        sensores["luz"]["valor"] = round(random.uniform(0, 100), 1)
        sensores["viento"]["valor"] = round(random.uniform(0, 60), 1)
        time.sleep(5)


if __name__ == "__main__":
    hilo = threading.Thread(target=simular_sensores, daemon=True)
    hilo.start()
    print("=" * 50)
    print(" Servidor IoT iniciado")
    print("=" * 50)
    print(f"  URL:       http://0.0.0.0:5000")
    print(f"  Sensores:  temperatura, humedad, luz, viento")
    print(f"  Actuadores: led, ventilador, rele")
    print("=" * 50)
    print("  Para probar desde esta misma Pi:")
    print("    curl http://localhost:5000/status")
    print("    curl http://localhost:5000/sensores")
    print("=" * 50)
    print("  Desde OTRO dispositivo en la misma red:")
    print("    http://<IP-de-la-Pi>:5000/dashboard")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000)
