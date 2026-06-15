from machine import UART, Pin
import time



# UART Setup (GP0 = TX, GP1 = RX)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))  # Baudrate muss zu Device A & Mega passen

print("Warte auf eingehende Daten...")

while True:
    if uart.any():
        received = uart.read()
        if received:
            print("Empfangen:", received)
    time.sleep(0.1)