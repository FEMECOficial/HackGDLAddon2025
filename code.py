import time
import board
import neopixel
#import countio
import asyncio
import random
import keypad
import wifi
import pwmio
import binascii

# Variables globales
current_mode = 0  # Modo inicial (respirar colores)

# Evento para señalizar cambios de modo
mode_change_event = asyncio.Event()

# Configuración de los NeoPixels
PIXEL_PIN = board.IO1
NUM_PIXELS = 16
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.5, auto_write=False)

#Iniciar el monitor de WIFI
monitor = wifi.Monitor(channel=1)

# Diccionario para rastrear el tiempo de activación de cada LED
pixel_last_seen = [0] * NUM_PIXELS
MODOS_USO = 5 #Cuantos Modos tiene el SAO + 1

# Caracteres para generar SSID aleatorios
ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

# Configuracion de LEDS IR
ir_led = pwmio.PWMOut(board.IO2, frequency=38000, duty_cycle=0)

# Comandos en formato NEC (ejemplo: encendido y apagado)
# Nota: Estos valores son de ejemplo
NEC_COMMANDS = {
    0: [9000, 4500, 560, 560, 560, 1690, 560, 560, 560, 1690, 560, 1690, 560, 560],
    1: [9000, 4500, 560, 560, 560, 1690, 560, 560, 560, 560, 560, 1690, 560, 560]
}

# Diccionario de código Morse
MORSE_CODE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.', '0': '-----',
    ' ': ' '  # Espacio entre palabras
}

# Funcion para convertir un texto a codigo morse
def text_to_morse(message):
    """Convierte un texto a código Morse."""
    return ' '.join(MORSE_CODE[char] for char in message.upper() if char in MORSE_CODE)

# Funcion para corresponder ch con Num. de LED
def map_channel_to_pixel(channel):
    """Mapea un canal WiFi (1-14) al índice del LED en el anillo."""
    return (channel - 1) % NUM_PIXELS

# Generador de nombres de redes WiFi aleatorias
def generate_random_ssid():
    """Genera un nombre aleatorio para una red WiFi."""
    prefix = random.choice(["HackGDL_","CTF_","HackTheWorld_"])
    suffix = "".join(random.choice(ASCII_LETTERS + DIGITS) for _ in range(4))
    return prefix + suffix

# Función para enviar pulsos
def send_pulse(pwm, durations):
    print(f"durations:{durations}")
    for i, duration in enumerate(durations):
        print(f"duration:{duration} i:{i}")
        pwm.duty_cycle = 0x7FFF if i % 2 == 0 else 0  # 50% duty cycle para HIGH
        time.sleep(duration / 1_000_000)  # Convertir duración a segundos
    pwm.duty_cycle = 0  # Apagar LED al final

# Interrupción del botón
async def button_interrupt(pin):
    """Maneja el cambio de modos al detectar una interrupción en el botón."""
    global current_mode
    with keypad.Keys((pin,), value_when_pressed=False) as keys:
        while True:
            event = keys.events.get()
            if event:
                if event.pressed:
                    current_mode = (current_mode + 1) % MODOS_USO  # Cambiar al siguiente modo ciclicamente
                print(f"Modo cambiado a: {current_mode}")
            await asyncio.sleep(0)  # Permitir que otras tareas corran

# Modo 0: Reguilete de colores
async def breathing_mode(mode):
    
    while True:    
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue

        # Animación de pares e impares
        while current_mode == mode:
            # Encender los LEDs en posiciones pares
            for i in range(0, NUM_PIXELS, 2):
                pixels[i] = wheel((i * 256 // NUM_PIXELS) & 255)
            # Apagar los LEDs en posiciones impares
            for i in range(1, NUM_PIXELS, 2):
                pixels[i] = (0, 0, 0)
            pixels.show()
            await asyncio.sleep(0.2)

            # Encender los LEDs en posiciones impares
            for i in range(1, NUM_PIXELS, 2):
                pixels[i] = wheel((i * 256 // NUM_PIXELS) & 255)
            # Apagar los LEDs en posiciones pares
            for i in range(0, NUM_PIXELS, 2):
                pixels[i] = (0, 0, 0)
            pixels.show()
            await asyncio.sleep(0.2)

# Modo 1: Detección de paquetes
async def packet_detection_mode(mode):
        
    while True:
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue
        
        print(f"Escaneando canal: {monitor.channel}")  # Imprimir el canal actual
        received = monitor.packet()
        if received:
            channel = received[wifi.Packet.CH]
            rssi = received[wifi.Packet.RSSI]
            pixel_index = map_channel_to_pixel(channel)
        
            # Calcular el color basado en el RSSI
            intensity = max(0, min(255, round((1 - abs(rssi / 100)) * 255)))  # Escalar RSSI a 0-255

            # Definir colores basados en el subtipo del paquete
            subt = (received[wifi.Packet.RAW][0] & 0b11110000) >> 4
            print(f'Packet recived: {binascii.hexlify(received[wifi.Packet.RAW]).decode("utf-8")}')
            if subt == 8:  # Beacons (azul)
                color = (0, 0, intensity)
                print(f"Canal {channel}: Beacon recibido con RSSI {rssi}")
            elif subt == 4:  # Probe Requests (verde)
                color = (0, intensity, 0)
                print(f"Canal {channel}: Probe Request recibido con RSSI {rssi}")
            else:  # Otros subtipos de tramas de gestión (rojo)
                color = (intensity, 0, 0)
                print(f"Canal {channel}: Otro paquete recibido con RSSI {rssi}")

            # Actualizar el LED correspondiente
            pixels[pixel_index] = color
            pixel_last_seen[pixel_index] = time.monotonic()  # Registrar el tiempo de actividad

            pixels.show()

        # Apagar LEDs inactivos después de 2 segundos
        current_time = time.monotonic()
        for i in range(NUM_PIXELS):
            if current_time - pixel_last_seen[i] > 5:  # Si el LED no se ha actualizado en 2 segundos
                pixels[i] = (0, 0, 0)

        # Actualizar los LEDs
        pixels.show()

        # Cambiar al siguiente canal WiFi
        monitor.channel = (monitor.channel % 13) + 1
        await asyncio.sleep(0.2)

# Modo 2: Rede WiFi falsas
async def fake_wifi_mode(mode):
    ap_started = False
    while True:
        if current_mode != mode:
            if ap_started:
                print("Apagando puntos de acceso falsos...")
                wifi.radio.stop_ap()  # Desactiva cualquier punto de acceso iniciado
                ap_started = False
            await asyncio.sleep(0.1)
            continue
        
        if not ap_started:
            print("Iniciando puntos de acceso falsos...")
            
            # Crear 5 redes con nombres aleatorios
            for _ in range(1):
                ssid = generate_random_ssid()
                try:
                    wifi.radio.start_ap(ssid=ssid)
                    print(f"SSID falso creado: {ssid}")
                except Exception as e:
                    print(f"Error al crear SSID {ssid}: {e}")
            ap_started = True

        # Generar un color aleatorio
        r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
        for brightness in range(0, 255, 5):
            pixels.fill((r * brightness // 255, g * brightness // 255, b * brightness // 255))
            pixels.show()
            await asyncio.sleep(0.02)
        for brightness in range(255, 0, -5):
            pixels.fill((r * brightness // 255, g * brightness // 255, b * brightness // 255))
            pixels.show()
            await asyncio.sleep(0.02)

# Función auxiliar para generar colores arcoíris
def wheel(pos):
    """Devuelve un color RGB basado en la posición del arcoíris (0-255)."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# Animacion de requilete rojo para el modo Infrarojo
async def ir_spam_animation(mode):
    """Animación de los LEDs en modo spamming IR."""
    while current_mode == mode:
        # Encender los LEDs en posiciones pares
        for i in range(0, NUM_PIXELS, 2):
            pixels[i] = (255, 0, 0)
        # Apagar los LEDs en posiciones impares
        for i in range(1, NUM_PIXELS, 2):
            pixels[i] = (0, 0, 0)
        pixels.show()
        await asyncio.sleep(0.2)

        # Encender los LEDs en posiciones impares
        for i in range(1, NUM_PIXELS, 2):
            pixels[i] = (255, 0, 0)
        # Apagar los LEDs en posiciones pares
        for i in range(0, NUM_PIXELS, 2):
            pixels[i] = (0, 0, 0)
        pixels.show()
        await asyncio.sleep(0.2)

# Spammeo de comandos
async def ir_spam_commands(mode):
    """Envío de comandos IR en modo spamming IR."""
    while current_mode == mode:
        for command in NEC_COMMANDS:
            send_pulse(ir_led, NEC_COMMANDS[command])
            await asyncio.sleep(2)

# Modo 3: Spamm de comandos IR
async def ir_spam_mode(mode):
    while True:
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue

        # Ejecutar animación y comandos IR en paralelo
        await asyncio.gather(ir_spam_animation(mode), ir_spam_commands(mode))
        
# Modo 4: Reproduce un mensaje en codigo morse
async def morse_mode(mode):
    """Modo que reproduce un mensaje en código Morse."""
    morse_message = text_to_morse("GlitchBoi")
    
    dot_time = 0.5  # Duración de un punto en segundos
    dash_time = dot_time * 3  # Duración de una raya
    gap_time = 1  # Tiempo entre elementos de una misma letra
    letter_gap_time = dot_time * 3  # Tiempo entre letras
    word_gap_time = dot_time * 7  # Tiempo entre palabras
    
    #Elegir un color al azar para los puntos y lineas
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

    while True:
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue
        
        # Expandir mensaje en una lista de estados para Neopixels
        pixel_states = []
        for char in morse_message:
            if char == '.':
                pixel_states.append((r, g, b))  # Un color para punto
            elif char == '-':
                pixel_states.append((255-r, 255-g, 255-b))  # El negativo del punto para raya
            elif char == ' ':
                pixel_states.append((0, 0, 0))  # Apagado para espacio

        # Rellenar si el mensaje es menor que la cantidad de Neopixels
        while len(pixel_states) < 16:
            pixel_states.append((0, 0, 0))  # Apagar LEDs restantes
        
        for i in range(len(pixel_states)):
            # Mostrar un "carrusel" de 16 LEDs
            for j in range(16):
                # Determinar el estado del LED actual (usar módulo para ciclar)
                pixel_index = (i + j) % len(pixel_states)
                pixels[j] = pixel_states[pixel_index]

            pixels.show()

            # Determinar duración con base en el tipo de símbolo
            if pixel_states[i] == (38, 37, 190):  # Punto
                await asyncio.sleep(dot_time)
            elif pixel_states[i] == (190, 172, 37):  # Raya
                await asyncio.sleep(dash_time)
            elif pixel_states[i] == (0, 0, 0):  # Espacio
                await asyncio.sleep(gap_time)

        # Pausa entre repeticiones del mensaje
        await asyncio.sleep(letter_gap_time)

# Modo X: Espacio para otros modos futuros
async def placeholder_mode(mode):
    while True:
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue
       
        pixels.fill((255, 255, 255))
        pixels.show()
        await asyncio.sleep(1)

# Función principal
async def main():
    # Crear la tarea para manejar la interrupción del botón
    button_task = asyncio.create_task(button_interrupt(board.IO0))

    # Ejecutar los modos en paralelo
    await asyncio.gather(
        button_task,
        breathing_mode(0),
        packet_detection_mode(1),
        fake_wifi_mode(2),
        ir_spam_mode(3),
        morse_mode(4),
        #placeholder_mode(),
    )

# Iniciar el programa
asyncio.run(main())
