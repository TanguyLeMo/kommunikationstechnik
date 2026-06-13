from machine import UART, Pin  # pyright: ignore[reportMissingImports]
import time


UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 0
UART_RX_PIN = 1

CHUNK_SIZE = 16
TIMEOUT_SECONDS = 0.05
START_SEQUENCE = 1

CRC16 = "10001000000100001"  # x^16 + x^12 + x^5 + 1

ACK_BYTE = 0xAA
NACK_BYTE = 0x00

RFC_FILE = "rfc2324.txt"


def calc_crc(u, g):
    pbits = len(g) - 1
    gen_poly = int(g, 2)
    bits2byte = max(0, 8 - pbits)
    gen_poly <<= bits2byte
    bitmask = 1 << max(8, pbits)

    crc = 0
    for b in u:
        crc ^= b << max(0, pbits - 8)
        for _ in range(8):
            crc <<= 1
            if crc & bitmask:
                crc ^= gen_poly
            crc &= (1 << max(8, pbits)) - 1

    crc >>= bits2byte
    return crc


def create_uart():
    return UART(
        UART_ID,
        baudrate=UART_BAUDRATE,
        tx=Pin(UART_TX_PIN),
        rx=Pin(UART_RX_PIN),
    )


def load_file_chunks(filename, chunk_size):
    chunks = []

    with open(filename, "r") as f:
        while True:
            chunk = f.read(chunk_size - 4)

            if not chunk:
                print("End of file reached.")
                print(f"Total lines read: {len(chunks)}")
                break

            chunks.append(chunk.encode("utf-8"))

    return chunks


def is_message_too_long(message):
    message_length = len(message)

    if message_length > CHUNK_SIZE - 4 or message_length > 0xFF:
        print(
            f"Message is too long to send in one frame. "
            f"Max allowed is {CHUNK_SIZE - 4} bytes. Or not more than 255"
        )
        print(f"Message length: {message_length} bytes")
        return True

    return False


def create_payload(message, sequence_number):
    message_length = len(message)

    return (
        message_length.to_bytes(1, "big")
        + message
        + sequence_number.to_bytes(1, "big")
    )


def pad_frame_before_crc(frame, message_length):
    if len(frame) < CHUNK_SIZE - 2:
        frame = frame + b"\x00" * max(0, CHUNK_SIZE - len(frame))

    elif len(frame) >= CHUNK_SIZE:
        print(
            "you should have never come here, but the message is too long "
            "to fit in one frame. Max allowed is "
            f"{CHUNK_SIZE - 4} bytes"
        )
        print(f"Message length: {message_length} bytes")
        raise ValueError("Message too long to fit in one frame")

    return frame


def create_frame(message, sequence_number):
    message_length = len(message)

    payload = create_payload(message, sequence_number)
    frame = pad_frame_before_crc(payload, message_length)

    crc_value = calc_crc(frame, CRC16)
    frame = frame + crc_value.to_bytes(2, "big")

    return frame, crc_value


def receive_and_wait(uart, expected_sequence):
    start_time = time.time()

    while time.time() - start_time < TIMEOUT_SECONDS:
        if uart.any() >= 4:
            data = uart.read(4)

            ack_nack = data[0]
            seq = data[1]
            crc_bytes = data[2:4]

            calculated_crc = calc_crc(data[0:2], CRC16)
            received_crc = int.from_bytes(crc_bytes, "big")

            if calculated_crc != received_crc:
                print("Received corrupted ACK/NACK")
                return -1
            if ack_nack == NACK_BYTE:
                print(f"Received NACK for message {seq}")
                return 0
            if ack_nack == ACK_BYTE:
                print(f"Received ACK for message {seq}")

                if seq == expected_sequence:
                    return 1
                return 0

            if seq != expected_sequence:
                print(
                    f"Received ACK with wrong sequence number {seq}, "
                    f"expected {expected_sequence}"
                )
                return -1

            return -1


def send_message_until_ack(uart, message, sequence_number):
    tried = 0
    while tried < 500:
        if is_message_too_long(message):
            break

        print("sending message wit sequence number:", sequence_number)

        frame, crc_value = create_frame(message, sequence_number)
        uart.write(frame)

        result = receive_and_wait(uart, sequence_number)

        if result == 1:
            print(f"Message {sequence_number} sent successfully with CRC {crc_value}")
            return True
        else:
            tried += 1
    #flush uart buffer after 500 tries
    if tried >= 500:
        while uart.any():
            uart.read()    
        return send_message_until_ack(uart, message, sequence_number)
    return False


def send_all_messages(uart, messages):
    sequence_number = START_SEQUENCE

    for i, message in enumerate(messages):
        was_sent = send_message_until_ack(uart, message, sequence_number)

        if was_sent:
            sequence_number = (sequence_number + 1) % 256
            print(f"Finished sending message {i + 1}/{len(messages)}")
            


def main():
    uart = create_uart()
    rfc_text = load_file_chunks(RFC_FILE, CHUNK_SIZE)

    send_all_messages(uart, rfc_text)


main()
