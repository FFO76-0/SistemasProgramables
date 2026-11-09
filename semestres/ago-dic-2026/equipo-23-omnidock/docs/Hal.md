# Hardware Abstraction Layer (HAL) — OmniDock

| Componente | Pin ESP32 | E/S | Tópico MQTT | Formato |
|-----------|-----------|-----|-------------|---------|
| IR Moneda $1 (FC-51) | GPIO 13 | Entrada (3.3 V) | `omnivault/sensor/moneda` | JSON `{"valor": 1}` |
| IR Moneda $2 (FC-51) | GPIO 14 | Entrada (3.3 V) | `omnivault/sensor/moneda` | JSON `{"valor": 2}` |
| IR Moneda $5 (FC-51) | GPIO 26 | Entrada (3.3 V) | `omnivault/sensor/moneda` | JSON `{"valor": 5}` |
| IR Moneda $10 (FC-51) | GPIO 33 | Entrada (3.3 V) | `omnivault/sensor/moneda` | JSON `{"valor": 10}` |
| IR Ranura Billete (FC-51) | GPIO 32 | Entrada (3.3 V) | `omnivault/sensor/billete_in` | JSON `{"detectado": 1}` |
| Reed Switch Puerta (MC-38) | GPIO 15 | Entrada (3.3 V) | `omnivault/sensor/puerta` | JSON `{"abierta": bool}` |
| Lector Huella AS608 | GPIO 16 / 17 | UART2 (3.3 V) | `omnivault/sensor/huella` | JSON `{"id": int, "acceso": true}` |
| Servomotor Seguro (MG90S) | GPIO 2 | PWM (5.0 V) | `omnivault/actuador/puerta/cmd` | Texto `"OPEN"` / `"CLOSE"` |
| Puente H L298N (Motor DC) | GPIO 18 / 19 / 21 | PWM (5.0 V) | `omnivault/actuador/motor/cmd` | Texto `"PULL"` / `"REJECT"` |
| DFPlayer Mini (Audio MP3) | GPIO 27 / 25 | UART1 (5.0 V) | `omnivault/actuador/audio/cmd` | JSON `{"pista": int}` |
| Cámara ESP32-CAM S3 | WiFi / Serial | Salida (5.0 V) | `omnivault/cam/frame` | JSON `{"imagen": "base64"}` |