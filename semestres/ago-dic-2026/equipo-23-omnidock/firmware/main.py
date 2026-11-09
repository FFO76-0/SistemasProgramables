"""
Proyecto: OmniDock - Alcancía Inteligente
Objetivo: Firmware principal del ESP32 DevKit V1 para lectura de sensores en tiempo
          real, control de actuadores y sincronización de telemetría por MQTT.
"""
import network
import time
import ujson
from umqtt.simple import MQTTClient
from dispositivos import RampaMonedas, SensorDigital, ServoSeguro, MotorTraccion, ReproductorDFPlayer, LectorHuellaAS608

WIFI_SSID = "TU_RED_WIFI"
WIFI_PASS = "TU_PASSWORD_WIFI"
MQTT_BROKER = "broker.hivemq.com"
CLIENT_ID = "OmniDock_ESP32_Main_Eq23"

TOPIC_MONEDA = b"omnivault/sensor/moneda"
TOPIC_BILLETE_IN = b"omnivault/sensor/billete_in"
TOPIC_HUELLA = b"omnivault/sensor/huella"
TOPIC_PUERTA_ESTADO = b"omnivault/sensor/puerta"
TOPIC_CMD_PUERTA = b"omnivault/actuador/puerta/cmd"
TOPIC_CMD_MOTOR = b"omnivault/actuador/motor/cmd"
TOPIC_CMD_AUDIO = b"omnivault/actuador/audio/cmd"

rampa = RampaMonedas({13: 1, 14: 2, 26: 5, 33: 10})
ir_billete = SensorDigital(pin_num=32, debounce_ms=1500)
reed_puerta = SensorDigital(pin_num=15, debounce_ms=500)
servo_puerta = ServoSeguro(pin_num=2)
motor_billete = MotorTraccion(pin_in1=18, pin_in2=19, pin_ena=21)
audio = ReproductorDFPlayer(uart_id=1, tx_pin=27, rx_pin=25)
huella = LectorHuellaAS608(uart_id=2, tx_pin=17, rx_pin=16)

MAPA_PISTAS_MONEDAS = {1: 1, 2: 2, 5: 3, 10: 4}
estado_puerta_anterior = 0

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)

def callback_mqtt(topic, msg):
    comando = msg.decode("utf-8")
    if topic == TOPIC_CMD_PUERTA:
        if comando == "OPEN":
            servo_puerta.abrir()
            audio.reproducir_pista(7)
        elif comando == "CLOSE":
            servo_puerta.cerrar()
    elif topic == TOPIC_CMD_MOTOR:
        if comando == "PULL":
            motor_billete.arrastrar_billete()
            time.sleep(1.5)
            motor_billete.detener()
            audio.reproducir_pista(5)
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

def main():
    global estado_puerta_anterior
    conectar_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(callback_mqtt)
    client.connect()
    for t in [TOPIC_CMD_PUERTA, TOPIC_CMD_MOTOR, TOPIC_CMD_AUDIO]:
        client.subscribe(t)

    ultimo_chequeo_huella = 0

    while True:
        try:
            client.check_msg()
            
            valor_moneda = rampa.leer_moneda()
            if valor_moneda:
                audio.reproducir_pista(MAPA_PISTAS_MONEDAS[valor_moneda])
                client.publish(TOPIC_MONEDA, ujson.dumps({"valor": valor_moneda, "ts": time.ticks_ms()}).encode())

            if ir_billete.activo():
                motor_billete.arrastrar_billete(velocidad=700)
                time.sleep(0.4)
                motor_billete.detener()
                client.publish(TOPIC_BILLETE_IN, ujson.dumps({"detectado": 1, "ts": time.ticks_ms()}).encode())

            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, ultimo_chequeo_huella) > 500:
                ultimo_chequeo_huella = ahora
                id_usuario = huella.verificar_dedo()
                if id_usuario is not None:
                    servo_puerta.abrir()
                    audio.reproducir_pista(7)
                    client.publish(TOPIC_HUELLA, ujson.dumps({"id": id_usuario, "acceso": True}).encode())

            estado_actual = reed_puerta.estado_crudo()
            if estado_actual != estado_puerta_anterior:
                estado_puerta_anterior = estado_actual
                abierta = (estado_actual == 1)
                alerta_intrusion = abierta and (not servo_puerta.abierto)
                if alerta_intrusion:
                    audio.reproducir_pista(8)
                client.publish(TOPIC_PUERTA_ESTADO, ujson.dumps({"abierta": abierta, "alerta": alerta_intrusion}).encode())

            time.sleep(0.02)
        except OSError:
            time.sleep(2)
            try:
                client.connect()
                for t in [TOPIC_CMD_PUERTA, TOPIC_CMD_MOTOR, TOPIC_CMD_AUDIO]:
                    client.subscribe(t)
            except:
                pass

if __name__ == "__main__":
    main()