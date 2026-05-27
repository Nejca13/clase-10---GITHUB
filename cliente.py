import requests
import time
import sys

IP = input("Ingresá la IP de la Raspberry Pi: ")
BASE = f"http://{IP}:5000"


def mostrar_menu():
    print("\n" + "=" * 45)
    print("  CLIENTE IoT - Clase 10")
    print("=" * 45)
    print("  1. Ver sensores")
    print("  2. Ver actuadores")
    print("  3. Controlar actuador")
    print("  4. Monitoreo continuo (cada 3s)")
    print("  5. Ver alertas")
    print("  6. Ver resumen completo")
    print("  0. Salir")
    print("=" * 45)


def cmd_ver_sensores():
    try:
        r = requests.get(f"{BASE}/sensores", timeout=5)
        r.raise_for_status()
        datos = r.json()
        print("\n SENSORES:")
        for nombre, info in datos.items():
            print(f"   {nombre}: {info['valor']} {info['unidad']}")
    except requests.exceptions.ConnectionError:
        print(f" ERROR: No se pudo conectar a {BASE}")
        print("   Verificá que:")
        print("   - La IP sea correcta")
        print("   - El servidor esté corriendo")
        print("   - Estén en la misma red")
    except requests.exceptions.Timeout:
        print(" ERROR: Tiempo de espera agotado")
    except requests.exceptions.HTTPError as e:
        print(f" ERROR HTTP: {e}")
    except Exception as e:
        print(f" ERROR inesperado: {e}")


def cmd_ver_actuadores():
    try:
        r = requests.get(f"{BASE}/actuadores", timeout=5)
        r.raise_for_status()
        datos = r.json()
        print("\n ACTUADORES:")
        for nombre, info in datos.items():
            estado = info["estado"]
            icono = "" if estado in ("ON", "CLOSED") else ""
            print(f"   {nombre}: {icono} {estado}")
    except Exception as e:
        print(f" ERROR: {e}")


def cmd_controlar():
    print("\n Actuadores disponibles: led, ventilador, rele, alarma")
    actuador = input("¿Cuál querés controlar? ").strip().lower()
    estado = input("Estado (ON/OFF o OPEN/CLOSED): ").strip().upper()
    try:
        r = requests.post(
            f"{BASE}/actuador/{actuador}",
            json={"estado": estado},
            timeout=5,
        )
        resultado = r.json()
        if r.status_code == 200:
            print(f" OK: {resultado['nombre']} -> {resultado['estado']}")
        else:
            print(f" ERROR: {resultado.get('error', 'desconocido')}")
    except Exception as e:
        print(f" ERROR: {e}")


def cmd_monitoreo():
    print("\n Monitoreando cada 3 segundos... (Ctrl+C para salir)")
    try:
        while True:
            ahora = time.strftime("%H:%M:%S")
            r = requests.get(f"{BASE}/sensores", timeout=3)
            sensores = r.json()
            linea = f"[{ahora}] "
            for nombre, info in sensores.items():
                linea += f"{nombre}: {info['valor']}{info['unidad']} | "
            print(linea)
            temp = sensores.get("temperatura", {}).get("valor", 0)
            if temp > 30:
                print(f"   [ {ahora} ]  ALERTA: Temperatura alta ({temp}°C)!")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n Monitoreo detenido.")
    except Exception as e:
        print(f" ERROR: {e}")


def cmd_alertas():
    try:
        r = requests.get(f"{BASE}/alertas", timeout=5)
        r.raise_for_status()
        alertas = r.json()
        print(f"\n  ALERTAS ({len(alertas)} registradas):")
        if not alertas:
            print("   No hay alertas")
        for al in alertas[-10:]:
            print(f"   [{al['tiempo']}] {al['tipo']} - {al.get('detalle', '')}")
    except Exception as e:
        print(f" ERROR: {e}")


def cmd_resumen():
    try:
        r = requests.get(f"{BASE}/resumen", timeout=5)
        r.raise_for_status()
        datos = r.json()
        print(f"\n  RESUMEN DEL SISTEMA")
        print(f"  Total lecturas: {datos['total_lecturas']}")
        print(f"  Tendencia: {datos['tendencia']}")
        print(f"\n  Alertas acumuladas:")
        for k, v in datos["alertas"].items():
            print(f"    {k}: {v}")
    except Exception as e:
        print(f" ERROR: {e}")


if __name__ == "__main__":
    while True:
        mostrar_menu()
        opcion = input("Elegí una opción: ").strip()
        if opcion == "1":
            cmd_ver_sensores()
        elif opcion == "2":
            cmd_ver_actuadores()
        elif opcion == "3":
            cmd_controlar()
        elif opcion == "4":
            cmd_monitoreo()
        elif opcion == "5":
            cmd_alertas()
        elif opcion == "6":
            cmd_resumen()
        elif opcion == "0":
            print(" Chau!")
            sys.exit(0)
        else:
            print(" Opción inválida")
