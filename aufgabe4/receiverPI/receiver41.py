from machine import UART, Pin
import time

CHUNK_SIZE = 64

uart = UART(0,
            baudrate=9600,
            tx=Pin(0),
            rx=Pin(1))

print("Warte auf Daten...")

def safe_decode(data):
    try:
        return data.decode('utf-8')
    except Exception:
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)

while True:
    if uart.any() >= CHUNK_SIZE:
        received = uart.read(CHUNK_SIZE)
        if received:
            text = safe_decode(received)
            print("Empfangen:", text)