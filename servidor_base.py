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
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API IoT - Raspberry Pi Zero</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0a0f1e;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 2rem 1rem;
    }
    .container { max-width: 700px; margin: auto; }
    .header {
      text-align: center;
      margin-bottom: 2.5rem;
      padding: 2rem;
      background: linear-gradient(135deg, #1e293b, #0f172a);
      border-radius: 16px;
      border: 1px solid #1e3a5f;
    }
    .badge {
      display: inline-block;
      background: #22d3ee22;
      color: #22d3ee;
      border: 1px solid #22d3ee44;
      border-radius: 999px;
      padding: 4px 14px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 1rem;
    }
    h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
    h1 span { color: #38bdf8; }
    .subtitle { color: #64748b; font-size: 0.9rem; }
    .section-title {
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #475569;
      margin: 2rem 0 0.75rem;
    }
    .endpoint {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.85rem 1.2rem;
      background: #111827;
      border: 1px solid #1e293b;
      border-radius: 10px;
      margin-bottom: 0.5rem;
      text-decoration: none;
      color: inherit;
      transition: border-color 0.2s, background 0.2s;
    }
    .endpoint:hover { background: #1e293b; border-color: #38bdf8; }
    .method {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 5px;
      min-width: 44px;
      text-align: center;
    }
    .get  { background: #14532d; color: #4ade80; }
    .post { background: #1e3a5f; color: #38bdf8; }
    .path { font-family: monospace; font-size: 0.95rem; flex: 1; }
    .desc { color: #64748b; font-size: 0.82rem; }
    .footer {
      text-align: center;
      margin-top: 2.5rem;
      color: #334155;
      font-size: 0.8rem;
    }
    .dot {
      display: inline-block;
      width: 8px; height: 8px;
      border-radius: 50%;
      background: #4ade80;
      margin-right: 6px;
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="badge">&#x2022; En l&iacute;nea</div>
    <h1>API IoT &mdash; <span>Raspberry Pi Zero</span></h1>
    <p class="subtitle"><span class="dot"></span>Servidor activo &bull; Puerto 5000 &bull; Clase 10</p>
  </div>

  <p class="section-title">Endpoints disponibles</p>

  <a class="endpoint" href="/status">
    <span class="method get">GET</span>
    <span class="path">/status</span>
    <span class="desc">Estado del servidor</span>
  </a>
  <a class="endpoint" href="/sensores">
    <span class="method get">GET</span>
    <span class="path">/sensores</span>
    <span class="desc">Todos los sensores</span>
  </a>
  <a class="endpoint" href="/sensor/temperatura">
    <span class="method get">GET</span>
    <span class="path">/sensor/&lt;nombre&gt;</span>
    <span class="desc">Un sensor espec&iacute;fico</span>
  </a>
  <a class="endpoint" href="/actuadores">
    <span class="method get">GET</span>
    <span class="path">/actuadores</span>
    <span class="desc">Estado de actuadores</span>
  </a>
  <div class="endpoint">
    <span class="method post">POST</span>
    <span class="path">/actuador/&lt;nombre&gt;</span>
    <span class="desc">Controlar un actuador</span>
  </div>
  <a class="endpoint" href="/docs">
    <span class="method get">GET</span>
    <span class="path">/docs</span>
    <span class="desc">Documentaci&oacute;n completa</span>
  </a>

  <div class="footer">CEAER &mdash; Clase 10 &bull; Sistema IoT Base</div>
</div>
</body>
</html>"""


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
