# Addon HackGDL 2025

### Descripción
Este proyecto utiliza un ESP32-C3 programado en CircuitPython para manejar un conjunto de **Neopixels** y crear múltiples funcionalidades. Incluye animaciones LED, detección de paquetes WiFi y la creación de puntos de acceso WiFi falsos. Además, cuenta con un modo especial que muestra un mensaje en código Morse utilizando los Neopixels.

---

## Características principales
1. **Modo Reguilete de Colores**: 
   - Los Neopixels simulan una animación suave de respiración utilizando una gama de colores del arcoíris.

2. **Modo Detección de Paquetes**:
   - Los LEDs muestran visualmente la cantidad de paquetes WiFi detectados en tiempo real.
   - El canal WiFi también se puede visualizar y cambia dinámicamente.

3. **Modo Redes Falsas (Fake WiFi)**:
   - Crea múltiples puntos de acceso WiFi con nombres aleatorios.
   - Diseñado para pruebas de ciberseguridad o como parte de demostraciones.

4. **Modo Morse**:
   - Utiliza los Neopixels para mostrar un mensaje en código Morse.
   - Cada Neopixel muestra un símbolo (punto, raya, espacio).

---

## Requisitos
- **Hardware**:
  - ESP32 con soporte para CircuitPython.
  - Un anillo o tira de 16 LEDs Neopixel.
  - Botón conectado al pin `GP8` y `GND`.

- **Software**:
  - CircuitPython instalado en la ESP32.
  - Librerías necesarias:
    - `adafruit_pixelbuf`
    - `adafruit_dotstar`
    - `asyncio`

---

## Instalación
1. **Preparar el entorno**:
   - Descarga CircuitPython para ESP32 desde [circuitpython.org](https://circuitpython.org/).
   - Copia los archivos necesarios al directorio principal del ESP32.

2. **Cargar el proyecto**:
   - Asegúrate de tener los siguientes archivos en tu ESP32-C3:
     - `code.py` (código principal).
     - Librerías requeridas dentro de la carpeta `lib/`.

3. **Configurar el hardware**:
   - Conecta los Neopixels al pin de datos adecuado (especificado en el código).
   - Conecta un botón al pin `GP8` y a `GND`.

---

## Modos de Operación
El proyecto cuenta con múltiples modos, los cuales se pueden alternar presionando el botón conectado a `GP8`. 

### 1. **Modo Reguilete de Colores** (Modo 1):
   - Animación de un reguilete en colores del arcoíris.
   - Diseñado para mostrar efectos visuales interesantes.

### 2. **Modo Detección de Paquetes** (Modo 2):
   - Los Neopixels visualizan la cantidad de paquetes WiFi detectados.
   - El canal WiFi es mostrado en la consola y los LEDs.

### 3. **Modo Redes Falsas** (Modo 3):
   - Crea múltiples puntos de acceso WiFi con nombres falsos y aleatorios.
   - Ejemplo de nombres:
     - `HackGDL_Guest`
     - `CTF_Whaaa`
     - `Network_1234`
   - Observa en la consola la lista de redes creadas.

### 4. **Modo Morse** (Modo 4):
   - Los Neopixels muestran el mensaje "GLITCHBOI" en código Morse.
   - Punto: LED de Color aleatorio.
   - Raya: LED del color negativo del punto.
   - Espacio: LED apagado.
   - El mensaje se repite continuamente.

---

## Uso
1. **Encender el ESP32**:
   - Asegúrate de que los Neopixels y el botón estén correctamente conectados.

2. **Cambiar modos**:
   - Presiona el botón conectado al pin `GP8` para alternar entre los diferentes modos en tiempo real.

3. **Depuración**:
   - Los mensajes de depuración se imprimen en la consola serial, incluyendo:
     - Modo activo.
     - Canales WiFi.
     - Paquetes detectados.
     - Redes creadas.

---

## Créditos
**Autor**: GlitchBoi  
**Fecha de creación**: Enero 2025  
**Licencia**: GPL v3  

---

## Notas adicionales
- Este proyecto fue diseñado para la convencion HackGDL 2025 como un SAO (Shitty Add-On).
- Si encuentras algún problema, asegúrate de que las librerías estén actualizadas y correctamente cargadas en tu dispositivo.
