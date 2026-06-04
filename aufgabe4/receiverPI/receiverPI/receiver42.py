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
        pass

with open("rfc2324.txt", "rb") as f:
    while True:
        if uart.any():
            received = uart.read(CHUNK_SIZE)
            text = f.read(CHUNK_SIZE)
            if received != text:
                print("Empfangen:", received)
                print("Erwartet:", text)
            else:
                print("correcct received")