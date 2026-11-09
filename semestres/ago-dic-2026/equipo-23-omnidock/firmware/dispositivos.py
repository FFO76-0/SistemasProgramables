"""
Proyecto: OmniDock - Alcancía Inteligente
Integrantes:
  - Israel Dominguez Zendejas (23240380)
  - Jesus Fernandez Olmos (23240357)
  - Emilio Uriel Rocha Manzano (23240356)
Objetivo: Capa de abstracción de hardware (HAL) en MicroPython.
"""
from machine import Pin, PWM, UART
import time

class RampaMonedas:
    def __init__(self, pines_valores):
        self.sensores = {}
        self.ultimo_disparo = {}
        for pin_num, valor in pines_valores.items():
            self.sensores[valor] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            self.ultimo_disparo[valor] = 0

    def leer_moneda(self):
        ahora = time.ticks_ms()
        for valor, pin in self.sensores.items():
            if pin.value() == 0:
                if time.ticks_diff(ahora, self.ultimo_disparo[valor]) > 450:
                    self.ultimo_disparo[valor] = ahora
                    return valor
        return None

class SensorDigital:
    def __init__(self, pin_num, debounce_ms=400):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.debounce_ms = debounce_ms
        self.ultimo_cambio = 0

    def activo(self):
        if self.pin.value() == 0:
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, self.ultimo_cambio) > self.debounce_ms:
                self.ultimo_cambio = ahora
                return True
        return False

    def estado_crudo(self):
        return self.pin.value()

class ServoSeguro:
    def __init__(self, pin_num=2):
        self.pwm = PWM(Pin(pin_num), freq=50)
        self.abierto = False
        self.cerrar()

    def abrir(self):
        self.pwm.duty(77)
        self.abierto = True

    def cerrar(self):
        self.pwm.duty(26)
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
        time.sleep(0.5)
        self.ajustar_volumen(25)

    def _enviar_trama(self, cmd, param1=0, param2=0):
        version, longitud, feedback = 0xFF, 0x06, 0x00
        checksum = -(version + longitud + cmd + feedback + param1 + param2) & 0xFFFF
        trama = bytearray([0x7E, version, longitud, cmd, feedback, param1, param2, (checksum >> 8) & 0xFF, checksum & 0xFF, 0xEF])
        self.uart.write(trama)

    def ajustar_volumen(self, nivel):
        self._enviar_trama(0x06, 0x00, max(0, min(30, nivel)))

    def reproducir_pista(self, numero_pista):
        self._enviar_trama(0x03, (numero_pista >> 8) & 0xFF, numero_pista & 0xFF)

class LectorHuellaAS608:
    def __init__(self, uart_id=2, tx_pin=17, rx_pin=16):
        self.uart = UART(uart_id, baudrate=57600, tx=tx_pin, rx=rx_pin)

    def verificar_dedo(self):
        trama_genimg = bytearray([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
        self.uart.write(trama_genimg)
        time.sleep(0.15)
        if self.uart.any():
            resp = self.uart.read()
            if resp and len(resp) >= 10 and resp[9] == 0x00:
                return 1
        return None