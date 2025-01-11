import time
import board
import neopixel
import countio
import asyncio
import random
import keypad
import wifi
import pwmio

# Variables globales
current_mode = 0  # Modo inicial (respirar colores)

# Configuración de los NeoPixels
PIXEL_PIN = board.IO1
NUM_PIXELS = 16
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.5, auto_write=False)

#Iniciar el monitor de WIFI
monitor = wifi.Monitor(channel=1)

# Diccionario para rastrear el tiempo de activación de cada LED
pixel_last_seen = [0] * NUM_PIXELS
MODOS_USO = 4 #Cuantos Modos tiene el SAO + 1

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
                    current_mode = (current_mode + 1) % MODOS_USO  # Cambiar al siguiente modo (cíclico entre 0, 1 y 2)
                print(f"Modo cambiado a: {current_mode}")
                for i in range(0, NUM_PIXELS):
                    pixels[i] = (0, 0, 0)
                pixels.show()
                time.sleep(0.2)
            await asyncio.sleep(0)  # Permitir que otras tareas corran

# Modo 0: Respirar colores
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

# Modo 3: Redes WiFi falsas con animación de reguilete
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

# Modo 3: Spamm de comandos IR
async def ir_spam_mode(mode):
    ir_started = False
    while True:
        if current_mode != mode:
            if ir_started:
                print("IR Terminado")
                ir_started = False
            await asyncio.sleep(0.1)
            continue
        
        if not ir_started:
            print("Iniciando Spammeo de IR")
            for command in NEC_COMMANDS:
                send_pulse(ir_led, NEC_COMMANDS[command])
                time.sleep(2)
            ir_started = True
            await asyncio.sleep(0.2)
        
        # Animación de pares e impares
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

# Modo X: Espacio para otros modos futuros
async def placeholder_mode(mode):
    while True:
        if current_mode != mode:
            await asyncio.sleep(0.1)
            continue

        #Aqui comienza el desarollo futuro
        pixels.fill((255, 255, 255))
        pixels.show()
        await asyncio.sleep(1)

# Función principal
async def main():
    # Crear la tarea para manejar la interrupción del botón
    button_task = asyncio.create_task(button_interrupt(board.IO8))

    # Ejecutar los modos en paralelo
    await asyncio.gather(
        button_task,
        breathing_mode(0),
        packet_detection_mode(1),
        fake_wifi_mode(2),
        ir_spam_mode(3),
        #placeholder_mode(),
    )

# Iniciar el programa
asyncio.run(main())
