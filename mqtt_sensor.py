import paho.mqtt.client as mqtt
import random
import time

BROKER = "test.mosquitto.org"
TOPIC_BASE = "clase10/raspberry"

def publicar_sensores():
    cliente = mqtt.Client()
    cliente.connect(BROKER, 1883, 60)
    print(f" Conectado a broker MQTT: {BROKER}")
    print(f" Publicando en: {TOPIC_BASE}/#")
    print("-" * 50)

    while True:
        temp = round(random.uniform(15, 35), 1)
        hum = round(random.uniform(40, 90), 1)
        luz = round(random.uniform(0, 100), 1)
        viento = round(random.uniform(0, 60), 1)

        cliente.publish(f"{TOPIC_BASE}/temperatura", temp)
        cliente.publish(f"{TOPIC_BASE}/humedad", hum)
        cliente.publish(f"{TOPIC_BASE}/luz", luz)
        cliente.publish(f"{TOPIC_BASE}/viento", viento)

        print(f" Publicado: temp={temp}°C | hum={hum}% | luz={luz}% | viento={viento} km/h")
        time.sleep(5)

if __name__ == "__main__":
    try:
        publicar_sensores()
    except KeyboardInterrupt:
        print("\n Publicación MQTT detenida.")
