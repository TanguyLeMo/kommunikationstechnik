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
CHUNK_SIZE = 64
CRC16 = "10001000000100001"  # x^16 + x^12 + x^5 + 1


messages = [b"sie haben",b"bestimmt ein liebsten zuhause",
            b"ich weise diese", b" Unterstellung zurueck",
            b"Unterstellungen sind", b"ein journalisitscher Trick",
            b"diese duerften in der", b"freiheitlichen demokratischen,",
            b"Grundordnung", b"nicht vorkommen",
            b"sie haetten mich", b"anders befragen muessen"
             ]

timeout = 5  # seconds
local_sec = 1

def receive_and_wait():
    start_time = time.time()
    while time.time() - start_time < timeout:
        if uart.any() >= 4:  # Expecting 4 bytes (1 for data (ack/nackk) + 1 for sequence number + 2 for CRC)
            data = uart.read(4)
            ack_nack = data[0]  # ACK/NACK byte
            seq = data[1]  # First byte is sequence number or ACK/NACK
            crc_bytes = data[2:4]  # Next two bytes are the CRC
            calculated_crc = calc_crc(data[0:2], CRC16)  # Calculate CRC for the ACK/NACK byte
            if calculated_crc != int.from_bytes(crc_bytes, "big"):
                print("Received corrupted ACK/NACK")
                return -1
            if ack_nack == 0xAA: # ACK
                print(f"Received ACK for message {seq}")
                if seq == local_sec:
                    return 1
                else:
                    return 0
            if seq != local_sec:
                print(f"Received ACK with wrong sequence number {seq}, expected {local_sec}")
                return -1
            return -1
        
      
        
for message in messages:
    crc_val = 0
    while True:
        message_length = len(message)
        payload = message_length.to_bytes(1, "big") + message + local_sec.to_bytes(1, "big") 
        if message_length > CHUNK_SIZE - 3 or message_length > 0xFF: 
            print(f"Message is too long to send in one frame. Max allowed is {CHUNK_SIZE - 3} bytes. Or not more than 255")
            print(f"Message length: {message_length} bytes")
            break
        crc_val = calc_crc(payload, CRC16)
        frame = payload + crc_val.to_bytes(2, "big")
        #frame = 1 bytes for message length + message + sequence number + 2 bytes for CRC
        if len(frame) < CHUNK_SIZE:
            frame = frame + b"\x00" * max(0, CHUNK_SIZE - len(frame))
        while uart.any():
            uart.read()  

        print("sending message:", frame)
        uart.write(frame)



        result = receive_and_wait()


        if result == 1:
            print(f"Message {local_sec} sent successfully with CRC {crc_val}")
            local_sec = (local_sec + 1) % 256
            break
        else:
            print(f"Resending message: {message} with sequence number {local_sec} due to NACK or timeout") 
        time.sleep(0.1)
