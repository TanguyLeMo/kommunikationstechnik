from machine import UART, Pin  # pyright: ignore[reportMissingImports]
import time


UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 0
UART_RX_PIN = 1

FRAME_SIZE = 16
TIMEOUT_MS = 500
START_SEQUENCE = 1

RFC_FILE = "rfc2324.txt"

ACK_BYTE = 0xAA
NACK_BYTE = 0x00

CRC4 = "10011"
CRC8 = "100000111"
CRC16 = "10001000000100001"

CRC_POLY = CRC16

CRC_BITS = len(CRC_POLY) - 1
CRC_BYTES = (CRC_BITS + 7) // 8

FRAME_HEADER_BYTES = 2
FRAME_OVERHEAD_BYTES = FRAME_HEADER_BYTES + CRC_BYTES
MAX_DATA_BYTES = FRAME_SIZE - FRAME_OVERHEAD_BYTES

ACK_FRAME_SIZE = 2 + CRC_BYTES

MAX_CHUNKS = None#1635
MAX_RETRIES_PER_FRAME = 500


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


def next_seq(seq):
    return (seq + 1) % 256


def load_file_chunks(filename, max_data_bytes, max_chunks=None)-> list[bytes]:
    chunks = []

    with open(filename, "rb") as f:
        while True:
            chunk = f.read(max_data_bytes)

            if not chunk:
                break

            chunks.append(chunk)

            if max_chunks is not None and len(chunks) >= max_chunks:
                break

    return chunks


def create_data_frame(message, sequence_number):
    if len(message) > MAX_DATA_BYTES:
        raise ValueError("Message too long for frame")

    padding_len = MAX_DATA_BYTES - len(message)
    data_area = message + b"\x00" * padding_len

    crc_input = bytes([len(message), sequence_number]) + data_area
    crc_value = calc_crc(crc_input, CRC_POLY)

    frame = crc_input + crc_value.to_bytes(CRC_BYTES, "big")

    if len(frame) != FRAME_SIZE:
        raise ValueError("Internal frame size error")

    return frame, crc_value


def receive_ack_or_nack(uart, expected_sequence):
    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < TIMEOUT_MS:
        if uart.any() >= ACK_FRAME_SIZE:
            data = uart.read(ACK_FRAME_SIZE)

            if data is None or len(data) != ACK_FRAME_SIZE:
                continue

            kind = data[0]
            seq = data[1]
            crc_bytes = data[2:2 + CRC_BYTES]

            computed_crc = calc_crc(data[:2], CRC_POLY)
            received_crc = int.from_bytes(crc_bytes, "big")

            if computed_crc != received_crc:
                print("Received corrupted ACK/NACK")
                return -1

            if seq != expected_sequence:
                print(
                    "Received ACK/NACK with wrong sequence:",
                    seq,
                    "expected:",
                    expected_sequence,
                )
                return 0

            if kind == ACK_BYTE:
                print("Received ACK for message", seq)
                return 1

            if kind == NACK_BYTE:
                print("Received NACK for message", seq)
                return 0

            print("Received unknown control byte:", kind)
            return -1

        time.sleep_ms(1)

    print("Timeout waiting for ACK/NACK")
    return -1


def flush_uart(uart):
    while uart.any():
        uart.read()


def send_message_until_ack(uart, message, sequence_number):
    retries = 0

    while retries < MAX_RETRIES_PER_FRAME:
        frame, crc_value = create_data_frame(message, sequence_number)

        uart.write(frame)

        print("Sending frame seq:", sequence_number, "crc:", crc_value)

        result = receive_ack_or_nack(uart, sequence_number)

        if result == 1:
            return retries

        retries += 1

    print("Too many retries. Flushing UART.")
    flush_uart(uart)

    return None


def send_all_messages(uart, messages):
    sequence_number = START_SEQUENCE
    total_retries = 0

    start_ms = time.ticks_ms()

    for i, message in enumerate(messages):
        retries = send_message_until_ack(uart, message, sequence_number)

        if retries is None:
            print("Giving up at message", i)
            break

        total_retries += retries

        print(
            "Finished sending message",
            i + 1,
            "/",
            len(messages),
            "retries:",
            retries,
        )

        sequence_number = next_seq(sequence_number)

    duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)

    print()
    print("===== SENDER SUMMARY =====")
    print("Sent chunks:", len(messages))
    print("Total retries:", total_retries)
    print("Duration:", duration_ms / 1000, "s")
    print("FRAME_SIZE:", FRAME_SIZE)
    print("MAX_DATA_BYTES:", MAX_DATA_BYTES)
    print("CRC_BITS:", CRC_BITS)
    print("==========================")


def main():
    if MAX_DATA_BYTES <= 0:
        raise ValueError("FRAME_SIZE is too small for header and CRC")

    uart = create_uart()
    messages = load_file_chunks(RFC_FILE, MAX_DATA_BYTES, MAX_CHUNKS)

    print("Loaded chunks:", len(messages))
    print("FRAME_SIZE:", FRAME_SIZE)
    print("MAX_DATA_BYTES:", MAX_DATA_BYTES)
    print("CRC_BITS:", CRC_BITS)

    send_all_messages(uart, messages)


main()