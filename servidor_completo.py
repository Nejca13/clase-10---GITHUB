import random
import time
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)

# ============================================================
# ESTADO GLOBAL DEL SISTEMA
# ============================================================

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

historial = []  # Guarda las últimas 100 lecturas completas
alertas = []  # Guarda eventos importantes con timestamp
contador_alertas = {"temperatura": 0, "viento": 0, "aqi": 0}

# Para detectar tendencia de temperatura
ultimas_temperaturas = []


# ============================================================
# LOGICA DE CONTROL AUTOMATICO
# ============================================================


def control_automatico():
    temp = sensores["temperatura"]["valor"]
    humedad = sensores["humedad"]["valor"]
    viento = sensores["viento"]["valor"]
    aqi = sensores["aqi"]["valor"]

    # Regla 1: Temperatura alta -> ventilador ON
    if temp > 28:
        actuadores["ventilador"]["estado"] = "ON"
    else:
        actuadores["ventilador"]["estado"] = "OFF"

    # Regla 2: Viento fuerte -> relé CLOSED (cortar circuito)
    if viento > 50:
        actuadores["rele"]["estado"] = "CLOSED"
    else:
        actuadores["rele"]["estado"] = "OPEN"

    # Regla 3: Mala calidad del aire -> LED rojo ON
    actuadores["led"]["estado"] = "ON" if aqi > 150 else "OFF"

    # Regla 4: Humedad > 80% Y temperatura > 25°C -> alarma
    if humedad > 80 and temp > 25:
        if actuadores["alarma"]["estado"] == "OFF":
            registrar_alerta("ALTA HUMEDAD + CALOR", f"Hum: {humedad}%, Temp: {temp}°C")
        actuadores["alarma"]["estado"] = "ON"
    else:
        actuadores["alarma"]["estado"] = "OFF"


def detectar_tendencia():
    """Analiza si la temperatura está subiendo, bajando o estable."""
    if len(ultimas_temperaturas) < 3:
        return "estable"
    recientes = ultimas_temperaturas[-3:]
    if recientes[0] < recientes[1] < recientes[2]:
        return "subiendo"
    if recientes[0] > recientes[1] > recientes[2]:
        return "bajando"
    return "estable"


def registrar_alerta(tipo, detalle=""):
    ahora = time.strftime("%Y-%m-%d %H:%M:%S")
    alertas.append({"tiempo": ahora, "tipo": tipo, "detalle": detalle})


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
    .dashboard-btn {
      display: inline-block;
      margin-top: 1.25rem;
      padding: 0.6rem 1.5rem;
      background: linear-gradient(135deg, #0ea5e9, #6366f1);
      color: white;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.9rem;
      transition: opacity 0.2s;
    }
    .dashboard-btn:hover { opacity: 0.85; }
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
    <a class="dashboard-btn" href="/dashboard">&#9654; Abrir Dashboard</a>
  </div>

  <p class="section-title">Sensores &amp; Actuadores</p>

  <a class="endpoint" href="/sensores">
    <span class="method get">GET</span>
    <span class="path">/sensores</span>
    <span class="desc">Todos los sensores en tiempo real</span>
  </a>
  <a class="endpoint" href="/sensor/temperatura">
    <span class="method get">GET</span>
    <span class="path">/sensor/&lt;nombre&gt;</span>
    <span class="desc">Un sensor espec&iacute;fico</span>
  </a>
  <a class="endpoint" href="/actuadores">
    <span class="method get">GET</span>
    <span class="path">/actuadores</span>
    <span class="desc">Estado de todos los actuadores</span>
  </a>
  <div class="endpoint">
    <span class="method post">POST</span>
    <span class="path">/actuador/&lt;nombre&gt;</span>
    <span class="desc">Controlar un actuador manualmente</span>
  </div>

  <p class="section-title">Datos &amp; M&eacute;tricas</p>

  <a class="endpoint" href="/historial">
    <span class="method get">GET</span>
    <span class="path">/historial</span>
    <span class="desc">&Uacute;ltimas 50 lecturas registradas</span>
  </a>
  <a class="endpoint" href="/alertas">
    <span class="method get">GET</span>
    <span class="path">/alertas</span>
    <span class="desc">&Uacute;ltimas 20 alertas del sistema</span>
  </a>
  <a class="endpoint" href="/resumen">
    <span class="method get">GET</span>
    <span class="path">/resumen</span>
    <span class="desc">Estado completo + tendencia</span>
  </a>

  <p class="section-title">Sistema</p>

  <a class="endpoint" href="/status">
    <span class="method get">GET</span>
    <span class="path">/status</span>
    <span class="desc">Estado del servidor + uptime</span>
  </a>
  <a class="endpoint" href="/dashboard">
    <span class="method get">GET</span>
    <span class="path">/dashboard</span>
    <span class="desc">Panel visual HTML (auto-refresca)</span>
  </a>

  <div class="footer">CEAER &mdash; Clase 10 &bull; Sistema IoT Completo</div>
</div>
</body>
</html>"""


@app.route("/status")
def status():
    return jsonify(
        {
            "status": "ok",
            "dispositivo": "Raspberry Pi Zero W",
            "clase": 10,
            "uptime_lecturas": len(historial),
            "tendencia": detectar_tendencia(),
        }
    )


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
        datos = request.get_json(silent=True)
        if datos is None:
            return jsonify(
                {"error": 'El cuerpo debe ser JSON válido. Ej: {"estado": "ON"}'}
            ), 400
        if "estado" not in datos:
            return jsonify({"error": "Falta el campo 'estado'"}), 400
        nuevo = datos["estado"].upper()
        estados_validos = {
            "led": ("ON", "OFF"),
            "ventilador": ("ON", "OFF"),
            "rele": ("OPEN", "CLOSED"),
            "alarma": ("ON", "OFF"),
        }
        if nombre in estados_validos and nuevo not in estados_validos[nombre]:
            return jsonify(
                {
                    "error": f"Estado inválido para {nombre}: {nuevo}. Válidos: {estados_validos[nombre]}"
                }
            ), 400
        actuadores[nombre]["estado"] = nuevo
        registrar_alerta("CONTROL MANUAL", f"{nombre} -> {nuevo}")
        print(f" [CONTROL] {nombre} -> {nuevo}")

    return jsonify({"nombre": nombre, **actuadores[nombre]})


@app.route("/historial")
def ver_historial():
    return jsonify(historial[-50:])


@app.route("/alertas")
def ver_alertas():
    return jsonify(alertas[-20:])


@app.route("/resumen")
def resumen():
    return jsonify(
        {
            "sensores": sensores,
            "actuadores": actuadores,
            "alertas": contador_alertas,
            "total_lecturas": len(historial),
            "tendencia": detectar_tendencia(),
            "ultimas_alertas": alertas[-5:],
        }
    )


@app.route("/dashboard")
def dashboard():
    tendencia = detectar_tendencia()
    emoji_tendencia = {"subiendo": " ", "bajando": " ", "estable": " "}.get(
        tendencia, ""
    )

    cards = ""
    for nombre, datos in sensores.items():
        color_fondo = "#1e293b"
        if nombre == "temperatura" and datos["valor"] > 30:
            color_fondo = "#7f1d1d"
        elif nombre == "aqi" and datos["valor"] > 150:
            color_fondo = "#7f1d1d"
        elif nombre == "viento" and datos["valor"] > 50:
            color_fondo = "#7f1d1d"
        cards += f"<div style='background:{color_fondo};padding:15px;border-radius:10px;color:white;min-width:150px;text-align:center;'><h3>{nombre}</h3><p style='font-size:28px;margin:5px 0;'>{datos['valor']} {datos['unidad']}</p></div>"

    actuadores_html = ""
    for nombre, datos in actuadores.items():
        activo = datos["estado"] in ("ON", "CLOSED")
        color = "#22c55e" if activo else "#ef4444"
        icono = "" if activo else ""
        actuadores_html += f"<div style='background:#1e293b;padding:15px;border-radius:10px;color:white;min-width:150px;text-align:center;'><h3>{nombre}</h3><p style='font-size:24px;margin:5px 0;color:{color};'>{icono} {datos['estado']}</p></div>"

    alertas_html = ""
    for al in alertas[-5:]:
        alertas_html += f"<div style='background:#3b0f0f;padding:8px 12px;border-radius:6px;margin:4px 0;font-size:13px;'><b>{al['tiempo']}</b> - {al['tipo']} {al['detalle']}</div>"

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta http-equiv="refresh" content="5"><title>Dashboard IoT</title></head>
<body style="font-family:Arial;background:#0f172a;color:white;padding:20px;margin:0;">
<h1 style="text-align:center;">  Dashboard IoT - Raspberry Pi <span style="font-size:16px;color:#94a3b8;">(actualiza cada 5s)</span></h1>
<p style="text-align:center;color:#94a3b8;">Tendencia: {emoji_tendencia} {tendencia} | Lecturas: {len(historial)}</p>
<h2> Sensores</h2>
<div style="display:flex;gap:15px;flex-wrap:wrap;justify-content:center;margin-bottom:30px;">{cards}</div>
<h2> Actuadores</h2>
<div style="display:flex;gap:15px;flex-wrap:wrap;justify-content:center;margin-bottom:30px;">{actuadores_html}</div>
<h2>  Últimas alertas</h2>
<div style="max-width:600px;margin:auto;">{alertas_html if alertas_html else '<p style="color:#94a3b8;text-align:center;">Sin alertas</p>'}</div>
</body></html>"""


# ============================================================
# SIMULACION EN SEGUNDO PLANO
# ============================================================


def simular_sensores():
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

        # Mantener historial acotado a 100 entradas
        if len(historial) > 100:
            historial.pop(0)

        # Tendencia
        ultimas_temperaturas.append(sensores["temperatura"]["valor"])
        if len(ultimas_temperaturas) > 10:
            ultimas_temperaturas.pop(0)

        control_automatico()

        # Contar alertas de umbral
        if sensores["temperatura"]["valor"] > 30:
            contador_alertas["temperatura"] += 1
            if contador_alertas["temperatura"] == 1:
                registrar_alerta("TEMP ALTA", f"{sensores['temperatura']['valor']}°C")
        if sensores["viento"]["valor"] > 50:
            contador_alertas["viento"] += 1
            if contador_alertas["viento"] == 1 or contador_alertas["viento"] % 5 == 0:
                registrar_alerta("VIENTO FUERTE", f"{sensores['viento']['valor']} km/h")
        if sensores["aqi"]["valor"] > 150:
            contador_alertas["aqi"] += 1

        print(
            f"[{ahora}] Temp: {sensores['temperatura']['valor']}°C | Hum: {sensores['humedad']['valor']}% | "
            f"Vent: {actuadores['ventilador']['estado']} | LED: {actuadores['led']['estado']}"
        )
        time.sleep(5)


if __name__ == "__main__":
    hilo = threading.Thread(target=simular_sensores, daemon=True)
    hilo.start()
    print("=" * 55)
    print("  SERVIDOR IoT COMPLETO INICIADO")
    print("=" * 55)
    print(f"  Endpoints disponibles:")
    print(f"    /status       - Estado general")
    print(f"    /sensores     - Todos los sensores")
    print(f"    /sensor/<id>  - Sensor individual")
    print(f"    /actuadores   - Todos los actuadores")
    print(f"    /actuador/<id>- Controlar actuador")
    print(f"    /historial    - Últimas 50 lecturas")
    print(f"    /alertas      - Últimas 20 alertas")
    print(f"    /resumen      - Estado completo")
    print(f"    /dashboard    - Panel visual HTML")
    print("=" * 55)
    print(f"  Dashboard: http://0.0.0.0:5000/dashboard")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000)
