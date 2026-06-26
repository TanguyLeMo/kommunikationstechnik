from machine import UART, Pin # pyright: ignore[reportMissingImports]
import time

# klausurfrei
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


def verifiy_received(message, crc_ding, received_sequence, last_correct_seq) -> int:
    if message is None or crc_ding is None or received_sequence is None:
      #  print("Invalid input to verifiy_received: message, crc_ding, and received_sequence must not be None")
        #send_nack(uart, last_correct_seq + 1)
        return 0
    computed_crc = calc_crc(len(message).to_bytes(1, "big") + message + received_sequence.to_bytes(1, "big"), CRC16)

    if crc_ding != computed_crc.to_bytes(2, "big"):
        print("CRC mismatch: expected", computed_crc, "but got", int.from_bytes(crc_ding, "big"))
        send_nack(uart, last_correct_seq + 1)
        return 0
    
    if received_sequence < last_correct_seq + 1:
        #print("Duplicate frame detected: expected sequence", last_correct_seq + 1, "but got", received_sequence)
        send_ack(uart, received_sequence)

    if received_sequence == last_correct_seq + 1:
        #print("Valid frame received: sequence", received_sequence)
        return 1
    
    if received_sequence > last_correct_seq + 1:
        #print("Missing frame(s) detected: expected sequence", last_correct_seq + 1, "but got", received_sequence)
        return -1
    return 1
        
def parse_frame(frame) -> tuple[bytes | None, bytes | None, int | None]:
    try:
        if not frame:
            print("Empty frame received")
            return None, None, None
        if len(frame) < 4:
            print("Frame too short: expected at least 4 bytes but got", len(frame))
            return None, None, None
        message_lengtth = frame[0]
        data = frame[1:1 + message_lengtth]
        local_seq = frame[message_lengtth+1]
        crc_ding = frame[len(frame)-2:len(frame)]
        return data, crc_ding, local_seq
    except Exception as e:
        print("Error parsing frame:", e)
        print("Received frame:", frame)
        return None, None, None

def send_ack(uart, sequence):
    ack_payload = bytes([0xAA, sequence])
    crc_ack = calc_crc(ack_payload, CRC16)
    ack_frame = ack_payload + crc_ack.to_bytes(2, "big")
    print("Sending ACK for sequence", sequence)
    uart.write(ack_frame)

def send_nack(uart, sequence):
    nack_payload = bytes([0x00, sequence])
    crc_nack = calc_crc(nack_payload, CRC16)
    nack_frame = nack_payload + crc_nack.to_bytes(2, "big")
    print("Sending NACK for sequence", sequence)
    uart.write(nack_frame)

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
chunk_size = 16
CRC16 = "10001000000100001"  # x^16 + x^12 + x^5 + 1
last_correct_seq = 0

messages_received = []
rfc_text = []

with open("rfc2324.txt", "r") as f:
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            print("End of file reached.")
            print(f"Total lines read: {len(rfc_text)}")
            break
        rfc_text.append(chunk)
            
print("waiting for data...")
while True:
    if uart.any():
        try:
            received = uart.read()
            print("Raw received data:", received)
            data, crc_ding, received_seq = parse_frame(received)
            #print(f"Parsed frame - Data: {data}, CRC: {crc_ding}, Sequence: {received_seq}")
        except ValueError as e:
            print("Error parsing frame:", e)
            continue
        result = verifiy_received(data, crc_ding, received_seq, last_correct_seq)
        if result == 1:
            send_ack(uart, received_seq)
            if data not in messages_received:
                print("received:", data)
                messages_received.append(data)
            last_correct_seq = last_correct_seq  + 1
    if len(messages_received) >= 12:
        print("Received 12 messages, stopping receiver.")
        break
print("Final list of received messages:")
for msg in messages_received:
    print("Message:", msg)
