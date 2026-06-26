from machine import UART, Pin
import time

chunksize = 64

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

try:
    with open("rfc2324.txt", "r") as f:
        while True:
            chunk = f.read(chunksize)
            if not chunk:
                print("End of file reached.")
                break
            print(f"Read chunk: {chunk}")
            uart.write(chunk)
            time.sleep(0.4)
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Finished.")
