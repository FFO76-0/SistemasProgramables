"""
Proyecto: OmniDock - Alcancía Inteligente
Script: generar_audios.py (Crea las 13 pistas MP3 para la tarjeta MicroSD del DFPlayer Mini)
"""
from gtts import gTTS
import os

AUDIOS = {
    "0001.mp3": "Moneda de un peso ingresada",
    "0002.mp3": "Moneda de dos pesos ingresada",
    "0003.mp3": "Moneda de cinco pesos ingresada",
    "0004.mp3": "Moneda de diez pesos ingresada",
    "0005.mp3": "Billete validado y aceptado",
    "0006.mp3": "Billete no reconocido, retírelo de la ranura",
    "0007.mp3": "Huella verificada, abriendo bóveda OmniDock",
    "0008.mp3": "Alerta de seguridad, acceso no autorizado",
    "0009.mp3": "Billete de cincuenta pesos aceptado",
    "0010.mp3": "Billete de cien pesos aceptado",
    "0011.mp3": "Billete de doscientos pesos aceptado",
    "0012.mp3": "Billete de quinientos pesos aceptado",
    "0013.mp3": "Billete de veinte pesos aceptado"
}

os.makedirs("audios_sd", exist_ok=True)

for archivo, texto in AUDIOS.items():
    ruta = os.path.join("audios_sd", archivo)
    tts = gTTS(text=texto, lang="es", slow=False)
    tts.save(ruta)
    print(f"[AUDIO] Generado: {ruta} -> '{texto}'")

print("\n¡Listo! Copia los 13 archivos de la carpeta 'audios_sd' en la raíz de tu MicroSD.")