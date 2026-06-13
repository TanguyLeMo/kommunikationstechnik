from machine import UART, Pin


chunksize = 64

uart = UART(0, baudrate=9600, tx=Pin(2), rx=Pin(3))

try:
    with open("rfc2324.txt", "r") as f:
        while True:
            chunk = f.read(chunksize)
            if not chunk:
                print("End of file reached.")
                break
            print(f"Read chunk: {chunk}")
            uart.write(chunk)
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Finished.")
