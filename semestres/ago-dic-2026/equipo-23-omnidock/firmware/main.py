"""
Proyecto: OmniDock - Alcancía Inteligente
Módulo: main.py (Firmware principal del ESP32)
"""
import network
import time
import ujson
import machine
from umqtt.simple import MQTTClient
from dispositivos import (
    RampaMonedas, SensorDigital, ServoSeguro,
    MotorTraccion, ReproductorDFPlayer, LectorHuellaAS608
)

# Credenciales del Hotspot y IP de la Laptop donde corre Mosquitto
WIFI_SSID = "HONOR ML"
WIFI_PASS = "Chuy123."
MQTT_BROKER = "10.245.60.63"
CLIENT_ID = "OmniDock_ESP32_Main_Eq23"

TOPIC_MONEDA = b"omnidock/sensor/moneda"
TOPIC_BILLETE_IN = b"omnidock/sensor/billete_in"
TOPIC_HUELLA = b"omnidock/sensor/huella"
TOPIC_PUERTA_ESTADO = b"omnidock/sensor/puerta"
TOPIC_CMD_PUERTA = b"omnidock/actuador/puerta/cmd"
TOPIC_CMD_MOTOR = b"omnidock/actuador/motor/cmd"
TOPIC_CMD_AUDIO = b"omnidock/actuador/audio/cmd"
TOPIC_CMD_HUELLA = b"omnidock/actuador/huella/cmd"

rampa = RampaMonedas({13: 1, 14: 2, 26: 5, 33: 10})
ir_billete = SensorDigital(pin_num=32, debounce_ms=1500)
reed_puerta = SensorDigital(pin_num=15, debounce_ms=400)
servo_puerta = ServoSeguro(pin_num=2)
motor_billete = MotorTraccion(pin_in1=18, pin_in2=19, pin_ena=21)
audio = ReproductorDFPlayer(uart_id=1, tx_pin=27, rx_pin=25)
huella = LectorHuellaAS608(uart_id=2, tx_pin=5, rx_pin=4)

MAPA_PISTAS_MONEDAS = {1: 1, 2: 2, 5: 3, 10: 4}
estado_puerta_anterior = -1
client = None


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.8)
    wlan.active(True)

    if not wlan.isconnected():
        print("[WIFI] Conectando a", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        intentos = 0
        while not wlan.isconnected():
            time.sleep(0.5)
            intentos += 1
            if intentos > 30:
                print("[WIFI] Tiempo agotado. Reiniciando ESP32...")
                machine.reset()
    print("[WIFI] Conectado exitosamente. IP:", wlan.ifconfig()[0])


def callback_mqtt(topic, msg):
    comando = msg.decode("utf-8")
    print("[MQTT CMD]", topic, "->", comando)

    if topic == TOPIC_CMD_PUERTA:
        if comando == "OPEN":
            servo_puerta.abrir()
            audio.reproducir_pista(7)
        elif comando == "CLOSE":
            servo_puerta.cerrar()

    elif topic == TOPIC_CMD_MOTOR:
        if comando == "PULL":
            motor_billete.arrastrar_billete()
            time.sleep(1.4)
            motor_billete.detener()
        elif comando == "REJECT":
            motor_billete.expulsar_billete()
            time.sleep(1.5)
            motor_billete.detener()
            audio.reproducir_pista(6)
        elif comando == "STOP":
            motor_billete.detener()

    elif topic == TOPIC_CMD_AUDIO:
        try:
            datos = ujson.loads(comando)
            audio.reproducir_pista(int(datos.get("pista", 1)))
        except ValueError:
            pass

    elif topic == TOPIC_CMD_HUELLA:
        # Permite registrar una nueva huella desde la interfaz web enviando {"registrar_id": 1}
        try:
            datos = ujson.loads(comando)
            nuevo_id = int(datos.get("registrar_id", 1))
            exito = huella.registrar_huella(nuevo_id)
            if client:
                client.publish(TOPIC_HUELLA, ujson.dumps({
                    "evento": "registro",
                    "id": nuevo_id,
                    "exito": exito
                }).encode())
        except Exception as e:
            print("[HUELLA ERROR]", e)


def conectar_mqtt():
    global client
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883, keepalive=60)
    client.set_callback(callback_mqtt)
    client.connect()
    for t in [TOPIC_CMD_PUERTA, TOPIC_CMD_MOTOR, TOPIC_CMD_AUDIO, TOPIC_CMD_HUELLA]:
        client.subscribe(t)
    print("[MQTT] Conectado al broker Mosquitto:", MQTT_BROKER)


def main():
    global estado_puerta_anterior
    conectar_wifi()
    try:
        conectar_mqtt()
    except Exception as e:
        print("[MQTT] No se encontró el broker en", MQTT_BROKER, "- Verifica la IP de tu laptop:", e)

    ultimo_chequeo_huella = 0

    while True:
        try:
            if client:
                client.check_msg()

            # 1. Lectura de Rampa de Monedas
            valor_moneda = rampa.leer_moneda()
            if valor_moneda:
                print(f"[MONEDA] Detectada moneda de ${valor_moneda}")
                audio.reproducir_pista(MAPA_PISTAS_MONEDAS[valor_moneda])
                if client:
                    client.publish(TOPIC_MONEDA, ujson.dumps({
                        "valor": valor_moneda,
                        "ts": time.ticks_ms()
                    }).encode())

            # 2. Lectura de Ranura de Billetes
            if ir_billete.activo():
                print("[BILLETE] Detectado en ranura. Sujetando para cámara...")
                motor_billete.arrastrar_billete(velocidad=720)
                time.sleep(0.35)
                motor_billete.detener()
                if client:
                    client.publish(TOPIC_BILLETE_IN, ujson.dumps({
                        "detectado": 1,
                        "ts": time.ticks_ms()
                    }).encode())

            # 3. Verificación de Huella Dactilar Personal (cada 500 ms)
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, ultimo_chequeo_huella) > 500:
                ultimo_chequeo_huella = ahora
                resultado_huella = huella.verificar_dedo()
                if resultado_huella is not None:
                    if resultado_huella >= 0:
                        print(f"[HUELLA] Acceso autorizado a Usuario ID #{resultado_huella}")
                        servo_puerta.abrir()
                        audio.reproducir_pista(7)
                        if client:
                            client.publish(TOPIC_HUELLA, ujson.dumps({
                                "id": resultado_huella,
                                "acceso": True
                            }).encode())
                    else:
                        print("[HUELLA] Huella NO registrada. Acceso denegado.")
                        audio.reproducir_pista(8)
                        if client:
                            client.publish(TOPIC_HUELLA, ujson.dumps({
                                "id": -1,
                                "acceso": False
                            }).encode())
                    time.sleep(1.5)

            # 4. Monitoreo de Puerta (Sensor Magnético MC-38)
            estado_actual = reed_puerta.estado_crudo()
            if estado_actual != estado_puerta_anterior:
                estado_puerta_anterior = estado_actual
                abierta = (estado_actual == 1)
                alerta_intrusion = abierta and (not servo_puerta.abierto)
                if alerta_intrusion:
                    print("[ALERTA] ¡Apertura forzada detectada!")
                    audio.reproducir_pista(8)
                if client:
                    client.publish(TOPIC_PUERTA_ESTADO, ujson.dumps({
                        "abierta": abierta,
                        "alerta": alerta_intrusion
                    }).encode())

            time.sleep(0.02)

        except OSError:
            time.sleep(2)
            try:
                conectar_mqtt()
            except Exception:
                pass


if __name__ == "__main__":
    main()