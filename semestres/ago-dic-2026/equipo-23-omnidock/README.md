# 🔐 OmniDock

### Alcancía inteligente con clasificador de monedas, validador de billetes por visión artificial y seguridad biométrica

![Estado](https://img.shields.io/badge/estado-completado-brightgreen)
![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)
![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)
![Plataforma](https://img.shields.io/badge/plataforma-ESP32%20%7C%20MicroPython-green)
![Version](https://img.shields.io/badge/Version%20Documento-V2.0-green)

> **Semestre:** ago-dic-2026
> **Materia:** Sistemas Programables — ISC TecNM León
> **Equipo:** equipo-23-omnidock
> **Integrantes:**

| Nombre | Matrícula | Rol | GitHub |
|--------|-----------|-----|--------|
| Israel Dominguez Zendejas | 23240380 | 🔧 Firmware ESP32 y MQTT | [@IsraelDZ3](https://github.com/IsraelDZ3) |
| Jesus Fernandez Olmos | 23240357 | 🧠 Backend Python e IA | [@FFO76-0](https://github.com/FFO76-0) |
| Emilio Uriel Rocha Manzano | 23240356 | 🔩 Diseño de hardware y CAD | [@23240356-Uriel](https://github.com/23240356-Uriel) |

---

## 📑 Contenido

1. [Descripción general](#-descripción-general)
2. [Funcionamiento](#-funcionamiento)
3. [Estructura del repositorio](#-estructura-del-repositorio)
4. [Arquitectura del sistema](#️-arquitectura-del-sistema)
5. [Hardware](#️-hardware)
6. [Software y firmware](#-software-y-firmware)
7. [Inteligencia artificial](#-inteligencia-artificial)
8. [Interfaz web](#-interfaz-web)
9. [Demostración](#-demostración)
10. [HAL](#-hal--hardware-abstraction-layer)
11. [Esquema Firebase](#-esquema-firebase)
12. [Retos técnicos](#️-retos-técnicos-encontrados)

---

## 📌 Descripción General

**OmniDock** es una alcancía inteligente pensada para **personas con discapacidad visual, adultos mayores y pequeños comerciantes**, quienes tienen dificultad para identificar billetes y monedas por sí mismos y se exponen a fraudes o al llamado "robo hormiga". El sistema recibe el dinero, **valida los billetes con una cámara y un algoritmo de visión artificial, clasifica mecánicamente las monedas, anuncia cada ingreso en voz alta** y resguarda todo tras una puerta que **solo se abre con la huella del dueño**.

A diferencia de una alcancía común o de un lector de billetes aislado, OmniDock integra en un solo dispositivo **validación, conteo, audio y custodia biométrica**, y permite a un familiar de apoyo **consultar el saldo y bloquear el sistema de forma remota** desde una interfaz web de alto contraste, todo con componentes accesibles y de bajo costo.

---

## ⚙️ Funcionamiento

```text
 ① Inserta        ② Procesa         ③ Clasifica        ④ Valida        ⑤ Asegura        ⑥ Retiro
   dinero   ──▶     el ingreso  ──▶   e identifica ──▶   por voz    ──▶  e incrementa ──▶  seguro
```

| Paso | Etapa | Qué sucede |
|:----:|-------|-----------|
| 1 | **Inserta dinero** | El usuario coloca un billete o una moneda en su ranura correspondiente. |
| 2 | **Procesa el ingreso** | Un sensor infrarrojo detecta el billete en la ranura y activa el motorreductor que lo arrastra (las monedas ruedan por la rampa clasificadora). |
| 3 | **Clasifica e identifica** | La **ESP32-CAM S3** fotografía el billete y el servidor de IA lo analiza; las monedas caen por tamaño y activan su sensor IR respectivo (**$1, $2, $5 y $10**). |
| 4 | **Valida por voz** | El **DFPlayer Mini** anuncia el resultado: _"Billete de cincuenta pesos aceptado"_ / _"Moneda de diez pesos"_. Si el billete es rechazado, el motor gira en reversa, lo devuelve y el sistema avisa _"Billete rechazado"_. |
| 5 | **Asegura e incrementa** | Se suma al saldo total y el dinero se almacena en los compartimentos internos. |
| 6 | **Retiro seguro** | El dueño coloca su huella en el **AS608**; si es válida, el servomotor libera el seguro y los resortes de tensión abren la puerta. Al retirar el dinero, el contador se reinicia. |

El **reed switch** vigila en todo momento si la puerta está abierta o cerrada, de modo que cualquier apertura no autorizada se reporta de inmediato al familiar de apoyo.

---

## 🗂️ Estructura del Repositorio

```text
equipo-23-omnidock/
├── docs/          ← Reporte PDF, manuales, HAL.md
├── firmware/      ← MicroPython: main.py, dispositivos.py y cam_s3.py
├── servidor/      ← Python: app.py (IA + MQTT bridge) y requirements.txt
├── interfaz/      ← Dashboard web en tiempo real (index.html)
├── hardware/      ← Esquemático (.fzz, .png y .pdf)
├── media/         ← Fotos del prototipo y evidencias de operación
└── README.md      ← Este documento
```

---

## 🏗️ Arquitectura del Sistema

El sistema se organiza en tres capas:

| Capa | Responsabilidad |
|------|-----------------|
| **1. Percepción (Edge)** | Clasificación mecánica de monedas con barreras infrarrojas (FC-51) y captura de billetes con la ESP32-CAM S3. |
| **2. Control (Firmware)** | Lógica de acceso biométrico (AS608), monitoreo magnético (MC-38) y accionamiento electromecánico (servomotor MG90S y motor DC con puente H L298N). |
| **3. Telemetría (Backend)** | Sincronización asíncrona de transacciones y análisis de imágenes en un servidor Python mediante **MQTT** (`broker.hivemq.com`, puerto 1883). |

![Arquitectura del sistema](hardware/arquitectura.png)

### Tópicos MQTT

Broker público: `broker.hivemq.com:1883`. El servidor se suscribe a `omnivault/#`.

| Tópico | Dirección | Descripción | Estado |
|--------|-----------|-------------|--------|
| `omnivault/sensor/moneda` | ESP32 → Broker | Moneda detectada en la rampa ($1, $2, $5, $10) | ✅ Implementado |
| `omnivault/sensor/billete_in` | ESP32 → Broker | Presencia de billete en ranura de entrada | ✅ Implementado |
| `omnivault/sensor/huella` | ESP32 → Broker | Usuario identificado por el lector AS608 | ✅ Implementado |
| `omnivault/sensor/puerta` | ESP32 → Broker | Estado físico de la puerta (Reed Switch MC-38) | ✅ Implementado |
| `omnivault/cam/frame` | ESP32-CAM → Broker | Fotografía del billete codificada en Base64 JPEG | ✅ Implementado |
| `omnivault/actuador/puerta/cmd` | Broker → ESP32 | Abrir o cerrar el seguro del servomotor MG90S | ✅ Implementado |
| `omnivault/actuador/motor/cmd` | Broker → ESP32 | Avanzar, expulsar o detener el motor de billetes | ✅ Implementado |
| `omnivault/actuador/audio/cmd` | Broker → ESP32 | Pista MP3 a reproducir en el DFPlayer Mini | ✅ Implementado |
| `omnivault/servidor/saldo` | Servidor → Interfaz | Resumen JSON de saldo, desglose e historial | ✅ Implementado |

---

## 🛠️ Hardware

| # | Componente | Tipo | Cantidad | Costo MXN |
|---|-----------|------|----------|-----------|
| 1 | ESP32 DevKit V1 | Microcontrolador | 1 | $130 |
| 2 | ESP32-CAM S3 (OV2640, USB-C) | Cámara | 1 | $330 |
| 3 | Módulo infrarrojo FC-51 | Sensor | 5 | $125 |
| 4 | Lector de huella óptico AS608 | Sensor estrella | 1 | $290 |
| 5 | Sensor magnético Reed Switch MC-38 | Sensor | 1 | $50 |
| 6 | Servomotor MG90S | Actuador | 1 | $68 |
| 7 | Motorreductor DC 1:48 + llanta | Actuador | 1 | $70 |
| 8 | Módulo puente H L298 | Driver PWM | 1 | $82 |
| 9 | Reproductor MP3 DFPlayer Mini | Actuador audio | 1 | $63 |
| 10 | Altavoz pequeño 8 Ω, 3 W | Actuador audio | 1 | $45 |
| 11 | Tarjeta microSD 8 GB | Almacenamiento | 1 | $85 |
| 12 | Módulo de fuente MB102 | Energía | 1 | $135 |
| 13 | Eliminador de corriente 9 V, 2 A | Energía | 1 | $140 |
| 14 | Protoboard de 830 puntos | Conectividad | 1 | $75 |
| 15 | Cables Dupont surtidos | Conectividad | 1 paquete | $55 |
| 16 | Planchas de MDF de 3 mm | Carcasa | 1 juego | $90 |
| 17 | Resortes de tensión | Carcasa | 2 piezas | $30 |
| **Total** | | | | **$1,863 MXN** |

### Cumplimiento de requisitos de la materia

| Requisito | Cumplimiento |
|-----------|--------------|
| Mínimo 3 sensores | ✅ Infrarrojos FC-51 (×5), lector de huella AS608, reed switch MC-38 |
| Mínimo 3 actuadores reales | ✅ Servomotor MG90S, motorreductor DC con puente H L298N, DFPlayer Mini + altavoz |
| Cámara | ✅ ESP32-CAM S3 |
| Componente estrella (no convencional) | ✅ Lector de huella dactilar óptico AS608 |

### Diagrama de conexiones

El esquemático completo se encuentra exportado dentro de la carpeta `hardware/`.

![Diagrama de conexiones](hardware/diagrama.png)

---

## 💻 Software y Firmware

### Requisitos del servidor Python

```bash
pip install -r servidor/requirements.txt
```

### Cómo ejecutar el sistema completo

**1. Broker MQTT:** el proyecto utiliza el broker `broker.hivemq.com`, permitiendo comunicación directa entre las placas y el servidor sin configuración adicional.

**2. Cargar el firmware en la ESP32 y ESP32-CAM S3:**
Configurar en `firmware/main.py` y `firmware/cam_s3.py` las credenciales `WIFI_SSID` y `WIFI_PASS`. Conectar la ESP32 principal a Thonny y subir `dispositivos.py` y `main.py`. Posteriormente, subir `cam_s3.py` (como `main.py`) a la placa ESP32-CAM S3.

**3. Ejecutar el servidor de IA y telemetría:**
```bash
cd servidor
python app.py
```

**4. Abrir la interfaz web:**
Abrir el archivo `interfaz/index.html` en cualquier navegador web para visualizar el saldo en tiempo real, la bitácora y los controles de seguridad.

### Archivos principales

| Archivo | Descripción |
|---------|-------------|
| `firmware/main.py` | Bucle principal del ESP32, lectura de 6 sensores, control de actuadores y cliente MQTT. |
| `firmware/dispositivos.py` | Abstracción de hardware: clases para rampa de monedas, puente H, servo, DFPlayer y AS608. |
| `firmware/cam_s3.py` | Captura de fotogramas JPEG en la ESP32-CAM S3 y envío en Base64 por MQTT. |
| `servidor/app.py` | Servidor backend que clasifica billetes con OpenCV y administra el saldo e historial. |
| `interfaz/index.html` | Panel de control web conectado por WebSockets MQTT. |
| `docs/HAL.md` | Documentación detallada del mapeo de pines y tópicos. |

### Librerías ESP32 (MicroPython)

| Librería | Uso |
|---------|-----|
| `umqtt.simple` | Cliente MQTT para publicar eventos y recibir comandos |
| `machine` | Control de pines GPIO (`Pin`), señales `PWM` (servo/motor) y puertos `UART` (AS608/DFPlayer) |
| `network` | Gestión de conectividad WiFi en modo estación |
| `ujson` | Empaquetado y lectura de tramas JSON |
| `ubinascii` | Codificación de fotografías JPEG a formato Base64 en la cámara |
| `time` | Temporización no bloqueante (`ticks_ms`) y filtro anti-rebote |

---

## 🧠 Inteligencia Artificial

- **Modelo y procesamiento:** Visión artificial implementada con **OpenCV (`cv2`) y `NumPy`** mediante análisis de perfil cromático en el espacio de color **HSV** (Matiz, Saturación y Valor).
- **Qué detecta:** Analiza el fotograma enviado por la ESP32-CAM S3 para identificar la denominación del billete mexicano (**$50, $100, $200 y $500 MXN**) y descartar papel sin saturación cromática o lecturas inválidas.
- **Cómo toma decisiones:**
  - **Billete válido:** publica el comando `PULL` hacia el puente H para guardar el billete, reproduce la confirmación por voz y suma el monto al saldo total.
  - **Billete rechazado:** publica el comando `REJECT` para girar el motor en reversa, devuelve el billete al usuario y reproduce la alerta _"Billete rechazado"_.
- **Confianza mínima aceptada:** Umbral de saturación cromática ≥ 25% y coincidencia de rango espectral del **85%**.

---

## 🖥️ Interfaz Web

Dashboard de **alto contraste y lectura sencilla** ubicado en `interfaz/index.html`, diseñado para el familiar de apoyo.

| Elemento | Descripción |
|----------|-------------|
| 💰 Saldo total | Monto acumulado actualizado en tiempo real vía WebSockets |
| 💵 Desglose | Conteo individual de monedas y billetes ingresados |
| 🚪 Estado de la puerta | Indicador visual (Cerrada segura / Alerta de apertura) según el sensor MC-38 |
| 🔴 Control remoto | Botones para liberar o bloquear el seguro biométrico a distancia |
| 📅 Historial | Bitácora en vivo con hora exacta y tipo de transacción |

---

## 🎥 Demostración

**Video de demostración (YouTube):** [▶️ Canal Oficial OmniDock](https://youtube.com/@omnidock_sistemasprogramables?si=SbqNf1KXrRyeVOAZ)

### Fotos del prototipo final

| Vista frontal | Vista interna | Sistema en operación |
|--------------|---------------|----------------------|
| ![frontal](media/prototipo-frontal.jpg) | ![interna](media/prototipo-interno.jpg) | ![operacion](media/sistema-operacion.jpg) |

---

## 📋 HAL — Hardware Abstraction Layer

Documento completo: [`docs/HAL.md`](docs/HAL.md).

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

---

## 🔥 Esquema Firebase

```text
/omnidock/
  /ingresos/{timestamp}/
      tipo: "billete" | "moneda"
      denominacion: 1 | 2 | 5 | 10 | 20 | 50 | 100 | 200 | 500
      confianza: 0.85
  /eventos_seguridad/{timestamp}/
      evento: "huella_valida" | "alerta_puerta_forzada"
  /estado_actual/
      saldo_total: 150
      puerta_abierta: false
      bloqueo_remoto: false
```

---

## ⚠️ Retos técnicos encontrados

1. **Caída de voltaje en alimentación:** alimentar los motores y el ESP32 con 5 V de entrada en el regulador MB102 provocaba reinicios por caída de tensión; se solucionó utilizando un eliminador de 9 V a 2 A para garantizar 5 V estables en el riel de potencia.
2. **Rebote en sensores infrarrojos:** la caída libre de las monedas por la rampa de MDF generaba lecturas múltiples; se implementó un filtro *debounce* por software de 450 ms con `time.ticks_ms()`.
3. **Ruido eléctrico en el audio:** el módulo DFPlayer Mini presentaba interferencia al compartir tierra con los motores; se mitigó añadiendo una resistencia de 1 kΩ en la línea serial TX del ESP32.