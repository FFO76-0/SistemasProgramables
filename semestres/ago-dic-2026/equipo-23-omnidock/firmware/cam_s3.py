"""
Proyecto: OmniDock - Alcancía Inteligente
Módulo: main.py para ESP32-CAM S3 (Respaldado en repositorio como firmware/cam_s3.py)
Objetivo: Capturar fotografías JPEG del billete al recibir el pulso por MQTT
          o mediante petición HTTP en http://<IP_CAMARA>/capture
"""
import network
import socket
import time
import ubinascii
import ujson
from umqtt.simple import MQTTClient

try:
    import camera
    CAMARA_DISPONIBLE = True
except ImportError:
    CAMARA_DISPONIBLE = False

# Credenciales de tu Hotspot y la IPv4 actual de tu laptop con Mosquitto
WIFI_SSID = "HONOR ML"
WIFI_PASS = "Chuy123."
MQTT_BROKER = "10.245.60.63"
CLIENT_ID = "OmniDock_CAM_S3_Eq23"

TOPIC_BILLETE_IN = b"omnidock/sensor/billete_in"
TOPIC_CAM_FRAME = b"omnidock/cam/frame"


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.6)
    wlan.active(True)
    if not wlan.isconnected():
        print("[CAM WIFI] Conectando a la red Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        intentos = 0
        while not wlan.isconnected():
            time.sleep(0.5)
            intentos += 1
            if intentos > 30:
                import machine
                machine.reset()
    ip = wlan.ifconfig()[0]
    print("¡Conexión exitosa!")
    print("Dirección IP asignada:", ip)
    return ip


def inicializar_camara():
    if not CAMARA_DISPONIBLE:
        print("[CAM] Librería 'camera' no detectada en este firmware.")
        return False
    try:
        camera.deinit()
    except Exception:
        pass

    try:
        # Configuración estándar para ESP32-CAM / ESP32-S3-CAM con PSRAM
        camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
        camera.framesize(camera.FRAME_VGA)  # 640x480 ideal para OpenCV y MQTT
        camera.quality(12)
        print("Cámara inicializada correctamente.")
        return True
    except Exception as e:
        print("Error iniciando cámara:", e)
        return False


def capturar_jpeg():
    if CAMARA_DISPONIBLE:
        try:
            return camera.capture()
        except Exception:
            return None
    return None


def main():
    inicializar_camara()
    ip = conectar_wifi()

    # 1. Servidor Web HTTP en el puerto 80 para entregar la captura a OpenCV
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 80))
    srv.listen(2)
    srv.settimeout(0.05)
    print(f"Servidor web iniciado en http://{ip}:80")

    # 2. Conexión al Broker Mosquitto local para enviar el frame automáticamente
    client = None
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883, keepalive=60)

        def callback_mqtt(topic, msg):
            if topic == TOPIC_BILLETE_IN:
                print("[CAM MQTT] Billete detectado, capturando frame...")
                buf = capturar_jpeg()
                if buf:
                    b64 = ubinascii.b2a_base64(buf).decode("utf-8").strip()
                    client.publish(TOPIC_CAM_FRAME, ujson.dumps({"imagen": b64}).encode())
                    print("[CAM MQTT] Frame enviado al servidor IA.")

        client.set_callback(callback_mqtt)
        client.connect()
        client.subscribe(TOPIC_BILLETE_IN)
        print("[CAM MQTT] Conectado al broker Mosquitto en:", MQTT_BROKER)
    except Exception as e:
        print("[CAM MQTT] Modo solo HTTP activo (Broker no alcanzado):", e)
        client = None

    # 3. Bucle principal híbrido (atiende MQTT y peticiones HTTP en /capture)
    while True:
        try:
            if client:
                client.check_msg()
        except Exception:
            pass

        try:
            conn, addr = srv.accept()
            conn.recv(512)
            buf = capturar_jpeg()
            if buf:
                conn.send(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Access-Control-Allow-Origin: *\r\n\r\n"
                )
                conn.sendall(buf)
            else:
                conn.send(b"HTTP/1.1 500 Internal Error\r\n\r\nError de captura")
            conn.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()