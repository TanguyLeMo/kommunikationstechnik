from machine import I2C, Pin, UART
import struct
import time

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
mega_addr = 0x42  

ber_value = 1           
baudrate_value = 9600     

uart = UART(0, 9600, tx=Pin(0), rx=Pin(1))  

# Konfigurationsdaten als Little Endian packen (2 Byte BER, 4 Byte Baudrate)
config_data = struct.pack('<HL', ber_value, baudrate_value)

print("Sende BER und Baudrate an Arduino Mega...")
i2c.writeto(mega_addr, config_data)
print("Konfigurationsdaten gesendet.")

time.sleep(1)
test_text = "Hallo vom Pico!\n"
uart.write(test_text)
print("Testnachricht gesendet über UART:", test_text)