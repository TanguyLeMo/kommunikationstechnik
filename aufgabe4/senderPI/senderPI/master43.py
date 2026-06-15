from machine import I2C, Pin, UART
import struct
import time

# I2C Setup für Pico 2W (Standard-Pins: GP4 = SDA, GP5 = SCL)
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
mega_addr = 0x42  # I2C-Adresse vom Arduino Mega

# Beispiel-Konfiguration
ber_value = 1           # Bitfehlerrate (Vielfaches von 1/65536)
baudrate_value = 19200     # Serielle Baudrate in Baud

# Serieller Port für UART-Sende-Empfang (z. B. Kommunikation mit Mega)
uart = UART(0, baudrate_value, tx=Pin(0), rx=Pin(1))  # GP0 = TX, GP1 = RX

# Konfigurationsdaten als Little Endian packen (2 Byte BER, 4 Byte Baudrate)
config_data = struct.pack('<HL', ber_value, baudrate_value)

print("Sende BER und Baudrate an Arduino Mega...")
i2c.writeto(mega_addr, config_data)
print("Konfigurationsdaten gesendet.")

# Warte etwas, bis der Mega die neue Baudrate übernimmt
time.sleep(1)

# Testkommunikation mit Arduino Mega
test_text = "Hallo vom Pico!\n"
uart.write(test_text)
print("Testnachricht gesendet über UART:", test_text)