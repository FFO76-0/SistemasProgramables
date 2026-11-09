"""
Proyecto: OmniDock - Alcancía Inteligente
Objetivo: Servidor backend en Python que procesa la telemetría MQTT, clasifica
          billetes mediante visión artificial (OpenCV por perfil cromático HSV),
          acciona el puente H y actualiza el saldo en tiempo real.
"""
import base64
import json
from datetime import datetime
import cv2
import numpy as np
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_SUB = "omnivault/#"
TOPIC_CMD_MOTOR = "omnivault/actuador/motor/cmd"
TOPIC_ESTADO_SALDO = "omnivault/servidor/saldo"

estado_boveda = {
    "saldo_total": 0,
    "monedas": {"1": 0, "2": 0, "5": 0, "10": 0},
    "billetes": {"20": 0, "50": 0, "100": 0, "200": 0, "500": 0},
    "puerta_abierta": False,
    "historial": []
}

def clasificar_billete_opencv(imagen_b64):
    if imagen_b64.startswith("SIMULACION"):
        return 50
    try:
        bytes_img = base64.b64decode(imagen_b64)
        arr_np = np.frombuffer(bytes_img, dtype=np.uint8)
        frame = cv2.imdecode(arr_np, cv2.IMREAD_COLOR)
        if frame is None: return None

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hue_promedio = float(np.mean(hsv[:, :, 0]))
        sat_promedio = float(np.mean(hsv[:, :, 1]))

        if sat_promedio < 25: return None
        if hue_promedio < 18 or hue_promedio > 160: return 100
        elif 35 <= hue_promedio < 85: return 200
        elif 85 <= hue_promedio < 130: return 500
        else: return 50
    except Exception:
        return None

def publicar_saldo(client):
    client.publish(TOPIC_ESTADO_SALDO, json.dumps(estado_boveda), retain=True)

def registrar_evento(descripcion, monto=0):
    hora = datetime.now().strftime("%H:%M:%S")
    estado_boveda["historial"].insert(0, {"hora": hora, "evento": descripcion, "monto": monto})
    estado_boveda["historial"] = estado_boveda["historial"][:15]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[SERVIDOR] Conectado. Escuchando telemetría...")
        client.subscribe(TOPIC_SUB)
        publicar_saldo(client)

def on_message(client, userdata, msg):
    topico = msg.topic
    texto = msg.payload.decode("utf-8", errors="ignore")

    if topico == "omnivault/sensor/moneda":
        datos = json.loads(texto)
        valor = int(datos.get("valor", 0))
        if str(valor) in estado_boveda["monedas"]:
            estado_boveda["monedas"][str(valor)] += 1
            estado_boveda["saldo_total"] += valor
            registrar_evento(f"Moneda ingresada de ${valor}", valor)
            publicar_saldo(client)

    elif topico == "omnivault/cam/frame":
        datos = json.loads(texto)
        denominacion = clasificar_billete_opencv(datos.get("imagen", ""))
        if denominacion:
            estado_boveda["billetes"][str(denominacion)] += 1
            estado_boveda["saldo_total"] += denominacion
            registrar_evento(f"Billete validado de ${denominacion}", denominacion)
            client.publish(TOPIC_CMD_MOTOR, "PULL")
        else:
            registrar_evento("Billete rechazado", 0)
            client.publish(TOPIC_CMD_MOTOR, "REJECT")
        publicar_saldo(client)

    elif topico == "omnivault/sensor/puerta":
        datos = json.loads(texto)
        estado_boveda["puerta_abierta"] = bool(datos.get("abierta", False))
        if datos.get("alerta"):
            registrar_evento("¡ALERTA! Puerta forzada", 0)
        publicar_saldo(client)

if __name__ == "__main__":
    cliente_mqtt = mqtt.Client(client_id="OmniDock_Backend")
    cliente_mqtt.on_connect = on_connect
    cliente_mqtt.on_message = on_message
    cliente_mqtt.connect(BROKER, PORT, 60)
    cliente_mqtt.loop_forever()