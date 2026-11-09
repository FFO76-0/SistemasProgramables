# Capa de Abstracción de Hardware (HAL) — OmniDock

## Mapa de Pines del Nodo Principal (ESP32 DevKit / S2 / S3)

| Componente | Pin ESP32 | Tipo / Protocolo | Nivel Lógico / Alimentación | Función en OmniDock |
| :--- | :--- | :--- | :--- | :--- |
| Sensor IR Moneda $1 (FC-51) | GPIO 13 | Entrada Digital | 3.3 V (VCC a 3V3) | Detecta paso de moneda de $1 MXN |
| Sensor IR Moneda $2 (FC-51) | GPIO 14 | Entrada Digital | 3.3 V (VCC a 3V3) | Detecta paso de moneda de $2 MXN |
| Sensor IR Moneda $5 (FC-51) | GPIO 26 | Entrada Digital | 3.3 V (VCC a 3V3) | Detecta paso de moneda de $5 MXN |
| Sensor IR Moneda $10 (FC-51) | GPIO 33 | Entrada Digital | 3.3 V (VCC a 3V3) | Detecta paso de moneda de $10 MXN |
| Sensor IR Entrada Billete (FC-51) | GPIO 32 | Entrada Digital | 3.3 V (VCC a 3V3) | Detecta billete en ranura y activa pre-arrastre |
| Sensor Magnético Puerta (MC-38) | GPIO 15 | Entrada `PULL_UP` | 3.3 V (a GND) | Detecta apertura autorizada o intrusión forzada |
| Servomotor Seguro (MG90S) | GPIO 2 | Salida PWM (50 Hz) | 5.0 V (Riel MB102) | Acciona el cerrojo mecánico de la bóveda |
| Puente H L298N (IN1 / IN2) | GPIO 18 / 19 | Salida Digital | 5.0 V en pin 12V/VCC | Controla sentido de giro del motor de billetes |
| Puente H L298N (ENA) | GPIO 21 | Salida PWM (1 kHz) | 3.3 V (Sin jumper) | Regula la velocidad de tracción del motor DC |
| DFPlayer Mini (RX / TX) | GPIO 27 / 25 | UART1 (9600 bps) | 5.0 V (Riel MB102) | Reproduce pistas de voz desde tarjeta MicroSD |
| Lector Biométrico AS608 (RX / TX) | GPIO 5 / 4 | UART2 (57600 bps) | 3.3 V (VCC a 3V3) | Registro y verificación de huellas personales |

## Distribución de Energía

* **Fuente MB102:** Alimentada con eliminador de 9V DC y configurada con ambos jumpers en **5V**.
* **Riel de 5V (Línea Roja):** Alimenta el pin VIN/5V del ESP32, 5V de la ESP32-CAM S3, VCC del DFPlayer Mini, cable rojo del Servomotor MG90S y la entrada **12V/VCC del puente H L298N** (dejando libre el pin de salida 5V del L298N).
* **Riel de 3.3V (Pin 3V3 del ESP32):** Alimenta los 5 sensores infrarrojos FC-51 y el lector de huella AS608 para proteger las entradas del microcontrolador.
* **Tierra Común (Línea Azul GND):** Unifica GND del MB102, ambos ESP32, L298N, sensores y actuadores.