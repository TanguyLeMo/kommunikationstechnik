from machine import UART, Pin
import time

def calc_crc(u,g):
    pbits=len(g) -1
    gen_poly=int(g,2)
    bits2byte = max(0,8 - pbits)
    gen_poly <<= bits2byte
    bitmask = 1 <<max(8,pbits)

    crc = 0
    for i,b in enumerate(u):
        crc ^= b << max(0,pbits-8)
        for j in range(8):
            crc <<= 1
            if crc & bitmask:
                crc ^= gen_poly
            crc&=(1<<max(8, pbits))-1
    crc>>=bits2byte
    return crc
        
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

CRC4  = "10011"              # x^4 + x + 1
CRC6  = "1101111"            # x^6 + x^5 + x^3 + x^2 + x + 1
CRC8  = "100000111"          # x^8 + x^2 + x + 1
CRC16 = "10001000000100001"  # x^16 + x^12 + x^5 + 1

frame_len = 39 + 2
while True:
    print("waiting for data...")
    if uart.any():
        frame = uart.read(frame_len)
        data = frame[:-2]  
        crc_ding = frame[-2:]

        computed_crc = calc_crc(data, CRC4)
        if computed_crc == int.from_bytes(crc_ding, "big"):
            print("CRC is valid")
        else:
            print("CRC is invalid")
            print("expected CRC:", computed_crc)
            print("received CRC:", int.from_bytes(crc_ding, "big"))
        print("received",frame)
    time.sleep(0.1)
