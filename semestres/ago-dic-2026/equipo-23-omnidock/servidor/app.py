"""
Proyecto: OmniDock - Alcancía Inteligente
Módulo: servidor/app.py (Backend con Visión Artificial OpenCV, Broker Mosquitto y Firebase)
"""
import base64
import json
import os
from datetime import datetime
import urllib.request
import cv2
import numpy as np
import paho.mqtt.client as mqtt
import requests

# 1. Configuración del Broker Mosquitto Propio (corre en esta misma laptop)
BROKER = "127.0.0.1"
PORT = 1883

# 2. IP asignada a tu ESP32-CAM en la red HONOR ML (ajústala si cambia en la consola de la cámara)
IP_ESP32_CAM = "192.168.43.16"

# 3. URL de tu Firebase Realtime Database (puedes crear una gratis en console.firebase.google.com)
# Déjala así o pon la URL de tu proyecto terminada en .firebaseio.com
FIREBASE_DB_URL = "https://omnidock-eq23-default-rtdb.firebaseio.com"

TOPIC_SUB = "omnidock/#"
TOPIC_CMD_MOTOR = "omnidock/actuador/motor/cmd"
TOPIC_CMD_AUDIO = "omnidock/actuador/audio/cmd"
TOPIC_ESTADO_SALDO = "omnidock/servidor/saldo"

PISTAS_BILLETES = {20: 13, 50: 9, 100: 10, 200: 11, 500: 12}
ARCHIVO_RESPALDO_LOCAL = "estado_boveda.json"

estado_boveda = {
    "saldo_total": 0,
    "monedas": {"1": 0, "2": 0, "5": 0, "10": 0},
    "billetes": {"20": 0, "50": 0, "100": 0, "200": 0, "500": 0},
    "puerta_abierta": False,
    "firebase_sync": False,
    "historial": []
}


def cargar_estado_previo():
    global estado_boveda
    if os.path.exists(ARCHIVO_RESPALDO_LOCAL):
        try:
            with open(ARCHIVO_RESPALDO_LOCAL, "r", encoding="utf-8") as f:
                estado_boveda.update(json.load(f))
            print(f"[RESPALDO] Saldo recuperado: ${estado_boveda['saldo_total']} MXN")
        except Exception:
            pass


def sincronizar_firebase_y_disco():
    """Guarda el estado localmente y lo sincroniza en tiempo real con Firebase."""
    try:
        with open(ARCHIVO_RESPALDO_LOCAL, "w", encoding="utf-8") as f:
            json.dump(estado_boveda, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    if FIREBASE_DB_URL and "firebaseio.com" in FIREBASE_DB_URL:
        try:
            r = requests.put(
                f"{FIREBASE_DB_URL.rstrip('/')}/omnidock_estado.json",
                json=estado_boveda,
                timeout=2.5
            )
            estado_boveda["firebase_sync"] = (r.status_code == 200)
        except Exception:
            estado_boveda["firebase_sync"] = False


def clasificar_billete_ia(frame):
    """
    Analiza la región central del billete mediante OpenCV en espacio HSV,
    filtrando píxeles grises/oscuros para obtener el matiz dominante exacto
    de las denominaciones mexicanas ($20, $50, $100, $200, $500).
    """
    if frame is None:
        return None

    cv2.imwrite("ultima_captura_billete.jpg", frame)
    alto, ancho, _ = frame.shape
    roi = frame[int(alto * 0.2):int(alto * 0.8), int(ancho * 0.2):int(ancho * 0.8)]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    Canal_H = hsv[:, :, 0]
    Canal_S = hsv[:, :, 1]
    Canal_V = hsv[:, :, 2]

    sat_media = float(np.mean(Canal_S))
    val_media = float(np.mean(Canal_V))

    # Filtramos solo los píxeles con color real para mayor precisión
    mascara_color = (Canal_S > 28) & (Canal_V > 40)
    if np.count_nonzero(mascara_color) < (roi.shape[0] * roi.shape[1] * 0.12):
        print(f"[IA OPEN-CV] Rechazado por falta de saturación cromática (S={sat_media:.1f}, V={val_media:.1f})")
        return None

    hue_dominante = float(np.median(Canal_H[mascara_color]))
    print(f"[IA OPEN-CV] Matiz Dominante(H): {hue_dominante:.1f} | Saturación(S): {sat_media:.1f} | Brillo(V): {val_media:.1f}")

    # Clasificación por perfiles cromáticos del Banco de México (familia G)
    if hue_dominante < 14 or hue_dominante >= 168:
        return 100  # Rojo intenso ($100 MXN - Sor Juana)
    elif 14 <= hue_dominante < 36:
        return 20   # Naranja / Dorado / Tricolor cálido ($20 MXN - Bicentenario)
    elif 36 <= hue_dominante < 86:
        return 200  # Verde ($200 MXN - Hidalgo y Morelos)
    elif 86 <= hue_dominante < 134:
        return 500  # Azul ($500 MXN - Benito Juárez)
    else:
        return 50   # Morado / Magenta ($50 MXN - Ajolote)


def capturar_frame_http():
    urls = [
        f"http://{IP_ESP32_CAM}/capture",
        f"http://{IP_ESP32_CAM}/jpg",
        f"http://{IP_ESP32_CAM}/photo.jpg"
    ]
    for url in urls:
        try:
            req = urllib.request.urlopen(url, timeout=3)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is not None:
                return frame
        except Exception:
            continue
    return None


def registrar_evento(descripcion, monto=0, categoria="info"):
    hora = datetime.now().strftime("%H:%M:%S")
    estado_boveda["historial"].insert(0, {
        "hora": hora,
        "evento": descripcion,
        "monto": monto,
        "categoria": categoria
    })
    estado_boveda["historial"] = estado_boveda["historial"][:20]


def publicar_saldo(client):
    sincronizar_firebase_y_disco()
    client.publish(TOPIC_ESTADO_SALDO, json.dumps(estado_boveda), retain=True)


def procesar_resultado_billete(client, denominacion):
    if denominacion in [20, 50, 100, 200, 500]:
        estado_boveda["billetes"][str(denominacion)] += 1
        estado_boveda["saldo_total"] += denominacion
        registrar_evento(f"Billete validado por IA (${denominacion} MXN)", denominacion, "billete")
        print(f"[IA BILLETE] ¡Aceptado billete de ${denominacion} MXN! Saldo Total: ${estado_boveda['saldo_total']}")
        client.publish(TOPIC_CMD_MOTOR, "PULL")
        pista = PISTAS_BILLETES.get(denominacion, 5)
        client.publish(TOPIC_CMD_AUDIO, json.dumps({"pista": pista}))
    else:
        registrar_evento("Billete no reconocido — Expulsado", 0, "alerta")
        print("[IA BILLETE] Objeto rechazado. Expulsando de la ranura...")
        client.publish(TOPIC_CMD_MOTOR, "REJECT")
    publicar_saldo(client)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[SERVIDOR] Conectado a Broker Mosquitto ({BROKER}:{PORT}). Escuchando tópicos...")
        client.subscribe(TOPIC_SUB)
        publicar_saldo(client)


def on_message(client, userdata, msg):
    topico = msg.topic
    texto = msg.payload.decode("utf-8", errors="ignore")

    if topico == "omnidock/sensor/moneda":
        datos = json.loads(texto)
        valor = int(datos.get("valor", 0))
        if str(valor) in estado_boveda["monedas"]:
            estado_boveda["monedas"][str(valor)] += 1
            estado_boveda["saldo_total"] += valor
            registrar_evento(f"Moneda clasificada de ${valor} MXN", valor, "moneda")
            print(f"[MONEDA] +${valor} MXN | Saldo Total: ${estado_boveda['saldo_total']}")
            publicar_saldo(client)

    elif topico == "omnidock/sensor/billete_in":
        print("[RANURA BILLETE] Sensor activado. Solicitando imagen a ESP32-CAM...")
        frame = capturar_frame_http()
        if frame is not None:
            denominacion = clasificar_billete_ia(frame)
            procesar_resultado_billete(client, denominacion)
        else:
            print("[RANURA BILLETE] Esperando frame por MQTT...")

    elif topico == "omnidock/cam/frame":
        datos = json.loads(texto)
        img_b64 = datos.get("imagen", "")
        if img_b64:
            bytes_img = base64.b64decode(img_b64)
            arr_np = np.frombuffer(bytes_img, dtype=np.uint8)
            frame = cv2.imdecode(arr_np, cv2.IMREAD_COLOR)
            denominacion = clasificar_billete_ia(frame)
            procesar_resultado_billete(client, denominacion)

    elif topico == "omnidock/sensor/huella":
        datos = json.loads(texto)
        if datos.get("evento") == "registro":
            exito = datos.get("exito", False)
            id_h = datos.get("id", 1)
            msg_ev = f"Huella ID #{id_h} registrada con éxito" if exito else f"Fallo al registrar huella ID #{id_h}"
            registrar_evento(msg_ev, 0, "biometria")
        else:
            if datos.get("acceso"):
                registrar_evento(f"Acceso biométrico autorizado (Usuario ID #{datos.get('id')})", 0, "biometria")
                estado_boveda["puerta_abierta"] = True
            else:
                registrar_evento("Huella desconocida rechazada por AS608", 0, "alerta")
        publicar_saldo(client)

    elif topico == "omnidock/sensor/puerta":
        datos = json.loads(texto)
        estado_boveda["puerta_abierta"] = bool(datos.get("abierta", False))
        if datos.get("alerta"):
            registrar_evento("¡ALERTA DE INTRUSIÓN! Puerta forzada sin huella", 0, "alerta")
        publicar_saldo(client)


if __name__ == "__main__":
    cargar_estado_previo()
    cliente_mqtt = mqtt.Client(client_id="OmniDock_Backend_Server")
    cliente_mqtt.on_connect = on_connect
    cliente_mqtt.on_message = on_message
    cliente_mqtt.connect(BROKER, PORT, 60)
    cliente_mqtt.loop_forever()