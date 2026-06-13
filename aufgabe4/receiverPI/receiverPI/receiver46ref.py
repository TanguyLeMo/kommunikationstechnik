from machine import UART, Pin  
import time
import gc


# =========================
# Configuration
# =========================

UART_ID = 0
BAUDRATE = 9600
TX_PIN = 0
RX_PIN = 1

CHUNK_SIZE = 16
STOP_AFTER_MESSAGES = 1635

ACK_BYTE = 0xAA
NACK_BYTE = 0x00

CRC16 = "10001000000100001"  # x^16 + x^12 + x^5 + 1
fileName = "received_messages.txt"
counter = 0
last_msg = b""

# =========================
# CRC
# =========================

def calc_crc(data, generator):
    pbits = len(generator) - 1
    gen_poly = int(generator, 2)

    bits2byte = max(0, 8 - pbits)
    gen_poly <<= bits2byte

    bitmask = 1 << max(8, pbits)

    crc = 0

    for byte in data:
        crc ^= byte << max(0, pbits - 8)

        for _ in range(8):
            crc <<= 1

            if crc & bitmask:
                crc ^= gen_poly

            crc &= (1 << max(8, pbits)) - 1

    crc >>= bits2byte
    return crc


# =========================
# Frame parsing
# =========================

def parse_frame(frame):
    try:
        if not frame:
            print("Empty frame received")
            return None, None, None

        if len(frame) < 4:
            #print("Frame too short: expected at least 4 bytes but got", len(frame))
            return None, None, None

        message_length = frame[0]

        data = frame[1:1 + message_length]
        sequence = frame[message_length + 1]
        crc_bytes = frame[len(frame) - 2:len(frame)]

        return data, crc_bytes, sequence

    except Exception as e:
        print("Error parsing frame:", e)
        print("Received frame:", frame)
        return None, None, None


# =========================
# ACK / NACK
# =========================

def send_control_frame(uart, control_byte, sequence, label):
    payload = bytes([control_byte, sequence])
    crc = calc_crc(payload, CRC16)

    frame = payload + crc.to_bytes(2, "big")

    print("Sending", label, "for sequence", sequence)
    uart.write(frame)


def send_ack(uart, sequence):
    send_control_frame(uart, ACK_BYTE, sequence, "ACK")


def send_nack(uart, sequence):
    send_control_frame(uart, NACK_BYTE, sequence, "NACK")


# =========================
# Verification
# =========================

def verify_received(uart, message, crc_bytes, received_sequence, last_correct_sequence)-> bool:
    if (
        message is None
        or crc_bytes is None
        or received_sequence is None
        or uart is None
    ):
        return False


    crc_input = (
        len(message).to_bytes(1, "big")
        + message
        + received_sequence.to_bytes(1, "big")
    )

    computed_crc = calc_crc(crc_input, CRC16)
    expected_sequence = (last_correct_sequence + 1) % 256
    if crc_bytes != computed_crc.to_bytes(2, "big"):
        print(
            "CRC mismatch: expected",
            computed_crc,
            "but got",
            int.from_bytes(crc_bytes, "big")
        )
        send_nack(uart, expected_sequence)
        return False
    received_duplicate = received_sequence < expected_sequence or (expected_sequence == 0 and received_sequence == 255)
    received_old = received_sequence < expected_sequence or (expected_sequence == 0 and received_sequence == 255)
    received_future = received_sequence > expected_sequence
    if received_sequence == expected_sequence:
        return True

    if received_duplicate :
        print("received duplicate frame: expected sequence", expected_sequence, "but got", received_sequence)
        send_ack(uart, received_sequence)
    elif received_old:
        print("received old frame: expected sequence", expected_sequence, "but got", received_sequence)
        send_ack(uart, received_sequence)
    elif received_future:
        print("received future frame: expected sequence", expected_sequence, "but got", received_sequence)
        send_nack(uart, expected_sequence)
        
    return False


# =========================
# Receive handling
# =========================

def handle_valid_message(uart, data, received_sequence, messages_received: list, last_correct_sequence: int):
    global counter

    print(f"Message with sequence {received_sequence} accepted. Total messages received: {counter} len of messages_received: {len(messages_received)}")
    messages_received.append(data)
    last_correct_sequence = (last_correct_sequence + 1) % 256
    counter += 1
    if counter % 256 == 0:
        print(f"Saving received messages to {fileName}...")
        with open(fileName, "ab") as f:
            for message in messages_received:
                f.write(message.decode("utf-8"))
            f.flush()
            f.close()
        messages_received.clear()
        gc.collect()
    return last_correct_sequence

def receive_loop(uart):
    last_correct_sequence = 0
    messages_received = []
    with open(fileName, "wb") as f:
        pass
    print("waiting for data...")
    while True:
        if uart.any():
            try:
                received = uart.read()
                data, crc_bytes, received_sequence = parse_frame(received)

            except ValueError as e:
                print("Error parsing frame:", e)
                continue

            result = verify_received(
                uart,
                data,
                crc_bytes,
                received_sequence,
                last_correct_sequence
            )

            if result:
                last_correct_sequence = handle_valid_message(
                    uart,
                    data,
                    received_sequence,
                    messages_received,
                    last_correct_sequence
                )

        if counter >= STOP_AFTER_MESSAGES:
            print("Received 1635 messages, stopping receiver.")
            break

    print("Final list of received messages:")

    for message in messages_received:
        print(message)


# =========================
# Main
# =========================

uart = UART(
    UART_ID,
    baudrate=BAUDRATE,
    tx=Pin(TX_PIN),
    rx=Pin(RX_PIN)
)

receive_loop(uart)