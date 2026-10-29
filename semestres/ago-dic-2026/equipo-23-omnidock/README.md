# OmniVault - Alcancía Inteligente

| Semestre | Materia | Equipo |
| :--- | :--- | :--- |
| ago-dic-2026 | Sistemas Programables — ISC TecNM León | equipo-23-omnidock |

### Integrantes
| Nombre | Matrícula | Rol | GitHub |
| :--- | :--- | :--- | :--- |
| Israel Dominguez Zendejas | 23240380 | Firmware ESP32 & MQTT | @IsraelDZ3 |
| Jesus Fernandez Olmos | 23240357 | Backend Python & IA | @FFO76-0 |
| Emilio Uriel Rocha Manzano | 23240356 | Diseño Hardware & CAD | @23240356-Uriel |

---

## Resumen del Proyecto y Arquitectura
OmniVault es un sistema de resguardo de efectivo IoT de alta seguridad. 
1. **Percepción (Edge):** Clasificación mecánica de monedas con barreras IR (FC-51) y validación de billetes mediante visión artificial (ESP32-CAM S3).
2. **Control (Firmware):** Lógica de acceso biométrico (AS608) y accionamiento electromecánico (Servomotor y DC).
3. **Telemetría (Backend):** Sincronización asíncrona de transacciones hacia un servidor Python mediante el protocolo MQTT (`broker.hivemq.com`).

---

## Especificaciones de Hardware (HAL)
El ruteo completo de pines y definición de tópicos de comunicación se encuentra documentado en [docs/HAL.md](docs/HAL.md).

---

## Problemas Conocidos y Limitaciones (Sprint 1)
1. **Emulación de actuadores:** El puente H y el motor DC operan en modo simulación de estados lógicos mientras finaliza el ensamble en el chasis MDF.
2. **Latencia asíncrona:** El broker MQTT público presenta una latencia variable (150ms - 600ms).
3. **Falsos positivos IR:** El sensor requiere un *debounce* (anti-rebote) por software de 500ms para evitar conteos dobles.

---

## Demostración
* **Video de Avance:** `https://youtube.com/@omnidock_sistemasprogramables?si=SbqNf1KXrRyeVOAZ`