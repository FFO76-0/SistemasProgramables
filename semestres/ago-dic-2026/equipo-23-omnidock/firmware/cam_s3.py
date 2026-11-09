"""
Proyecto: OmniDock - Alcancía Inteligente
Objetivo: Firmware para ESP32-CAM S3 (OV2640). Captura fotogramas y los envía
          en Base64 por MQTT para su validación en el servidor IA.
"""
import network
import time
import ubinascii
import ujson
from umqtt.simple import MQTTClient

try:
    import camera
    CAMARA_DISPONIBLE = True
except ImportError:
    CAMARA_DISPONIBLE = False

WIFI_SSID = "TU_RED_WIFI"
WIFI_PASS = "TU_PASSWORD_WIFI"
MQTT_BROKER = "broker.hivemq.com"
CLIENT_ID = "OmniDock_ESP32CAM_S3_Eq23"

TOPIC_BILLETE_IN = b"omnivault/sensor/billete_in"
TOPIC_CAM_FRAME = b"omnivault/cam/frame"

def iniciar_camara():
    if CAMARA_DISPONIBLE:
        camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
        camera.framesize(camera.FRAME_QVGA)
        camera.quality(12)

def callback_disparo(topic, msg):
    if CAMARA_DISPONIBLE:
        buf = camera.capture()
        img_b64 = ubinascii.b2a_base64(buf).decode("utf-8").strip()
    else:
        img_b64 = "SIMULACION_FRAME_BILLETE"
    client.publish(TOPIC_CAM_FRAME, ujson.dumps({"imagen": img_b64}).encode())

def main():
    global client
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep(0.5)

    iniciar_camara()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(callback_disparo)
    client.connect()
    client.subscribe(TOPIC_BILLETE_IN)

    while True:
        client.check_msg()
        time.sleep(0.1)

if __name__ == "__main__":
    main()