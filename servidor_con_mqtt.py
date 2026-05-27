import random
import time
import threading
from flask import Flask, jsonify, request
import paho.mqtt.client as mqtt

app = Flask(__name__)

BROKER = "test.mosquitto.org"
TOPIC_BASE = "clase10/servidor"

sensores = {
    "temperatura": {"valor": round(random.uniform(15, 35), 1), "unidad": "°C"},
    "humedad": {"valor": round(random.uniform(40, 90), 1), "unidad": "%"},
    "luz": {"valor": round(random.uniform(0, 100), 1), "unidad": "%"},
    "viento": {"valor": round(random.uniform(0, 60), 1), "unidad": "km/h"},
    "aqi": {"valor": round(random.uniform(0, 200), 1), "unidad": "AQI"},
}

actuadores = {
    "led": {"estado": "OFF"},
    "ventilador": {"estado": "OFF"},
    "rele": {"estado": "OPEN"},
    "alarma": {"estado": "OFF"},
}

historial = []
alertas = []

def control_automatico():
    temp = sensores["temperatura"]["valor"]
    humedad = sensores["humedad"]["valor"]
    viento = sensores["viento"]["valor"]
    aqi = sensores["aqi"]["valor"]

    if temp > 28:
        actuadores["ventilador"]["estado"] = "ON"
    else:
        actuadores["ventilador"]["estado"] = "OFF"

    if viento > 50:
        actuadores["rele"]["estado"] = "CLOSED"
    else:
        actuadores["rele"]["estado"] = "OPEN"

    actuadores["led"]["estado"] = "ON" if aqi > 150 else "OFF"

    if humedad > 80 and temp > 25:
        if actuadores["alarma"]["estado"] == "OFF":
            registrar_alerta("ALTA HUMEDAD + CALOR", f"Hum: {humedad}%, Temp: {temp}°C")
        actuadores["alarma"]["estado"] = "ON"
    else:
        actuadores["alarma"]["estado"] = "OFF"

def registrar_alerta(tipo, detalle=""):
    ahora = time.strftime("%Y-%m-%d %H:%M:%S")
    alertas.append({"tiempo": ahora, "tipo": tipo, "detalle": detalle})

def detectar_tendencia():
    if len(historial) < 3:
        return "estable"
    temps = [h.get("temperatura", 0) for h in historial[-3:]]
    if temps[0] < temps[1] < temps[2]:
        return "subiendo"
    if temps[0] > temps[1] > temps[2]:
        return "bajando"
    return "estable"

cliente_mqtt = mqtt.Client()
cliente_mqtt.connect(BROKER, 1883, 60)
print(f" MQTT conectado a {BROKER}")

@app.route("/")
def home():
    return "<h1>API IoT + MQTT</h1><p>Este servidor también publica sensores por MQTT.</p>"

@app.route("/status")
def status():
    return jsonify({"status": "ok", "dispositivo": "Raspberry Pi Zero W", "mqtt": BROKER})

@app.route("/sensores")
def listar_sensores():
    return jsonify(sensores)

@app.route("/sensor/<nombre>")
def leer_sensor(nombre):
    if nombre in sensores:
        return jsonify({"nombre": nombre, **sensores[nombre]})
    return jsonify({"error": "Sensor no encontrado", "disponibles": list(sensores.keys())}), 404

@app.route("/actuadores")
def listar_actuadores():
    return jsonify(actuadores)

@app.route("/actuador/<nombre>", methods=["GET", "POST"])
def controlar_actuador(nombre):
    if nombre not in actuadores:
        return jsonify({"error": "Actuador no encontrado", "disponibles": list(actuadores.keys())}), 404
    if request.method == "POST":
        datos = request.get_json(silent=True)
        if datos is None or "estado" not in datos:
            return jsonify({"error": "Falta campo 'estado'"}), 400
        actuadores[nombre]["estado"] = datos["estado"].upper()
    return jsonify({"nombre": nombre, **actuadores[nombre]})

@app.route("/historial")
def ver_historial():
    return jsonify(historial[-50:])

@app.route("/alertas")
def ver_alertas():
    return jsonify(alertas[-20:])

@app.route("/resumen")
def resumen():
    return jsonify({"sensores": sensores, "actuadores": actuadores, "total_lecturas": len(historial), "tendencia": detectar_tendencia()})

@app.route("/dashboard")
def dashboard():
    cards = ""
    for nombre, datos in sensores.items():
        cards += f"<div style='background:#1e293b;padding:15px;border-radius:10px;color:white;min-width:150px;text-align:center;'><h3>{nombre}</h3><p style='font-size:28px;margin:5px 0;'>{datos['valor']} {datos['unidad']}</p></div>"
    actuadores_html = ""
    for nombre, datos in actuadores.items():
        color = "#22c55e" if datos["estado"] in ("ON","CLOSED") else "#ef4444"
        actuadores_html += f"<div style='background:#1e293b;padding:15px;border-radius:10px;color:white;min-width:150px;text-align:center;'><h3>{nombre}</h3><p style='font-size:24px;color:{color};'>{datos['estado']}</p></div>"
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta http-equiv="refresh" content="5"><title>Dashboard IoT + MQTT</title></head>
<body style="font-family:Arial;background:#0f172a;color:white;padding:20px;margin:0;">
<h1 style="text-align:center;"> Dashboard IoT + MQTT</h1>
<h2> Sensores</h2><div style="display:flex;gap:15px;flex-wrap:wrap;">{cards}</div>
<h2> Actuadores</h2><div style="display:flex;gap:15px;flex-wrap:wrap;">{actuadores_html}</div>
<p style="text-align:center;color:#94a3b8;margin-top:20px;">MQTT broker: {BROKER}</p>
</body></html>"""

def simular_y_publicar():
    while True:
        sensores["temperatura"]["valor"] = round(random.uniform(15, 35), 1)
        sensores["humedad"]["valor"] = round(random.uniform(40, 90), 1)
        sensores["luz"]["valor"] = round(random.uniform(0, 100), 1)
        sensores["viento"]["valor"] = round(random.uniform(0, 60), 1)
        sensores["aqi"]["valor"] = round(random.uniform(0, 200), 1)

        ahora = time.strftime("%H:%M:%S")
        lectura = {"tiempo": ahora}
        for k, v in sensores.items():
            lectura[k] = v["valor"]
        historial.append(lectura)
        if len(historial) > 100:
            historial.pop(0)

        control_automatico()

        cliente_mqtt.publish(f"{TOPIC_BASE}/temperatura", sensores["temperatura"]["valor"])
        cliente_mqtt.publish(f"{TOPIC_BASE}/humedad", sensores["humedad"]["valor"])
        cliente_mqtt.publish(f"{TOPIC_BASE}/luz", sensores["luz"]["valor"])
        cliente_mqtt.publish(f"{TOPIC_BASE}/viento", sensores["viento"]["valor"])

        print(f"[{ahora}] HTTP + MQTT | Temp: {sensores['temperatura']['valor']}°C | Hum: {sensores['humedad']['valor']}%")
        time.sleep(5)

if __name__ == "__main__":
    hilo = threading.Thread(target=simular_y_publicar, daemon=True)
    hilo.start()
    print("=" * 55)
    print("  SERVIDOR IoT + MQTT INICIADO")
    print("=" * 55)
    print(f"  HTTP:  http://0.0.0.0:5000")
    print(f"  MQTT:  {BROKER} -> {TOPIC_BASE}/#")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000)
