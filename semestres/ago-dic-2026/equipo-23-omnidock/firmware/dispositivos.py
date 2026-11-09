"""
Proyecto: OmniDock - Alcancía Inteligente
Módulo: dispositivos.py (Capa de Abstracción de Hardware y Biometría AS608)
"""
from machine import Pin, PWM, UART
import time


class SensorDigital:
    def __init__(self, pin_num, pull_up=True, activo_bajo=True, debounce_ms=250):
        modo_pull = Pin.PULL_UP if pull_up else None
        self.pin = Pin(pin_num, Pin.IN, modo_pull)
        self.activo_bajo = activo_bajo
        self.debounce_ms = debounce_ms
        self.ultimo_disparo = 0

    def estado_crudo(self):
        return self.pin.value()

    def activo(self):
        lectura = self.pin.value()
        activado = (lectura == 0) if self.activo_bajo else (lectura == 1)
        if activado:
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, self.ultimo_disparo) > self.debounce_ms:
                self.ultimo_disparo = ahora
                return True
        return False


class RampaMonedas:
    def __init__(self, mapa_pines, debounce_ms=220):
        self.sensores = {}
        for pin_num, valor in mapa_pines.items():
            self.sensores[valor] = SensorDigital(pin_num, pull_up=True, activo_bajo=True, debounce_ms=debounce_ms)

    def leer_moneda(self):
        for valor, sensor in self.sensores.items():
            if sensor.activo():
                return valor
        return None


class ServoSeguro:
    def __init__(self, pin_num=2):
        self.pwm = PWM(Pin(pin_num), freq=50)
        self.abierto = False
        self.cerrar()

    def abrir(self):
        self.pwm.duty(77)  # ~90 grados
        self.abierto = True

    def cerrar(self):
        self.pwm.duty(26)  # ~0 grados
        self.abierto = False


class MotorTraccion:
    def __init__(self, pin_in1=18, pin_in2=19, pin_ena=21):
        self.in1 = Pin(pin_in1, Pin.OUT)
        self.in2 = Pin(pin_in2, Pin.OUT)
        self.ena = PWM(Pin(pin_ena), freq=1000)
        self.detener()

    def arrastrar_billete(self, velocidad=850):
        self.in1.value(1)
        self.in2.value(0)
        self.ena.duty(velocidad)

    def expulsar_billete(self, velocidad=850):
        self.in1.value(0)
        self.in2.value(1)
        self.ena.duty(velocidad)

    def detener(self):
        self.in1.value(0)
        self.in2.value(0)
        self.ena.duty(0)


class ReproductorDFPlayer:
    def __init__(self, uart_id=1, tx_pin=27, rx_pin=25):
        self.uart = UART(uart_id, baudrate=9600, tx=tx_pin, rx=rx_pin)
        time.sleep(0.3)
        self.definir_volumen(26)

    def _enviar_trama(self, cmd, param1=0, param2=0):
        version = 0xFF
        longitud = 0x06
        feedback = 0x00
        checksum = -(version + longitud + cmd + feedback + param1 + param2) & 0xFFFF
        trama = bytearray([
            0x7E, version, longitud, cmd, feedback,
            param1, param2, (checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF
        ])
        self.uart.write(trama)
        time.sleep(0.05)

    def definir_volumen(self, nivel=25):
        nivel = max(0, min(30, nivel))
        self._enviar_trama(0x06, 0x00, nivel)

    def reproducir_pista(self, numero_pista):
        self._enviar_trama(0x03, (numero_pista >> 8) & 0xFF, numero_pista & 0xFF)


class LectorHuellaAS608:
    def __init__(self, uart_id=2, tx_pin=5, rx_pin=4):
        self.uart = UART(uart_id, baudrate=57600, tx=tx_pin, rx=rx_pin)
        time.sleep(0.2)

    def _cmd(self, payload, espera=0.2):
        if self.uart.any():
            self.uart.read()
        cabecera = bytearray([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01])
        longitud = len(payload) + 2
        chk = (0x01 + (longitud >> 8) + (longitud & 0xFF) + sum(payload)) & 0xFFFF
        trama = (
            cabecera
            + bytearray([longitud >> 8, longitud & 0xFF])
            + bytearray(payload)
            + bytearray([chk >> 8, chk & 0xFF])
        )
        self.uart.write(trama)
        time.sleep(espera)
        if self.uart.any():
            resp = self.uart.read()
            if resp and len(resp) >= 10:
                return resp
        return None

    def verificar_dedo(self):
        """
        Retorna:
          - None: si no hay ningún dedo puesto en el sensor.
          - ID (int >= 0): si el dedo coincide con una huella guardada.
          - -1: si pusieron un dedo que NO está registrado (intruso).
        """
        # 1. Capturar imagen (GenImg = 0x01)
        r = self._cmd([0x01], espera=0.12)
        if not r or r[9] != 0x00:
            return None
        # 2. Extraer características en Buffer 1 (Img2Tz = 0x02)
        r = self._cmd([0x02, 0x01], espera=0.18)
        if not r or r[9] != 0x00:
            return None
        # 3. Buscar en la base de datos flash del sensor (Search = 0x04)
        r = self._cmd([0x04, 0x01, 0x00, 0x00, 0x00, 0x7F], espera=0.22)
        if r and len(r) >= 14 and r[9] == 0x00:
            id_encontrado = (r[10] << 8) | r[11]
            return id_encontrado
        return -1

    def registrar_huella(self, id_pos=1):
        """Ejecuta este método desde el REPL o por MQTT para guardar una huella nueva."""
        print(f"[AS608] Coloca el dedo en el lector para guardarlo en el ID {id_pos}...")
        intentos = 0
        while intentos < 50:
            r = self._cmd([0x01], 0.2)
            if r and r[9] == 0x00:
                break
            intentos += 1
        else:
            print("[AS608] Tiempo agotado esperando el dedo.")
            return False

        self._cmd([0x02, 0x01], 0.2)
        print("[AS608] Retira el dedo...")
        time.sleep(1.5)
        print("[AS608] Vuelve a colocar el MISMO dedo...")

        intentos = 0
        while intentos < 50:
            r = self._cmd([0x01], 0.2)
            if r and r[9] == 0x00:
                break
            intentos += 1
        else:
            return False

        self._cmd([0x02, 0x02], 0.2)
        self._cmd([0x05], 0.2)  # RegModel
        r = self._cmd([0x06, 0x01, (id_pos >> 8) & 0xFF, id_pos & 0xFF], 0.25)  # Store
        if r and r[9] == 0x00:
            print(f"[AS608] ¡Huella registrada exitosamente en la posición #{id_pos}!")
            return True
        print("[AS608] No coincidieron las dos lecturas. Intenta de nuevo.")
        return False

    def borrar_todas_huellas(self):
        r = self._cmd([0x0D], 0.3)
        return bool(r and r[9] == 0x00)