from machine import UART, Pin  # pyright: ignore[reportMissingImports]
import sys
import time
import network
import socket
import ujson


UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 0
UART_RX_PIN = 1

#WIFI_SSID = "stairwaytoheaven"
#WIFI_PASSWORD = "SalimisteinrichtigerMann!!!"
WIFI_SSID = "Unischallert "
WIFI_PASSWORD = "musswirgge"
CONTROL_PORT = 5001

FRAME_SIZE = 16
TIMEOUT_MS = 500
START_SEQUENCE = 1

RFC_FILE = "rfc2324.txt"

ACK_BYTE = 0xAA
NACK_BYTE = 0x00

CRC4 = "10011"
CRC6 = "1100001"
CRC8 = "100000111"
CRC16 = "10001000000100001"

CRC_POLY = CRC16

FRAME_HEADER_BYTES = 2

MAX_CHUNKS = None
MAX_RETRIES_PER_FRAME = 200

CRC_BITS = len(CRC_POLY) - 1
CRC_BYTES = (CRC_BITS + 7) // 8

FRAME_OVERHEAD_BYTES = FRAME_HEADER_BYTES + CRC_BYTES
MAX_DATA_BYTES = FRAME_SIZE - FRAME_OVERHEAD_BYTES

ACK_FRAME_SIZE = 2 + CRC_BYTES
def recalculate_sizes():
    global CRC_BITS
    global CRC_BYTES
    global FRAME_OVERHEAD_BYTES
    global MAX_DATA_BYTES
    global ACK_FRAME_SIZE

    CRC_BITS = len(CRC_POLY) - 1
    CRC_BYTES = (CRC_BITS + 7) // 8

    FRAME_OVERHEAD_BYTES = FRAME_HEADER_BYTES + CRC_BYTES
    MAX_DATA_BYTES = FRAME_SIZE - FRAME_OVERHEAD_BYTES

    ACK_FRAME_SIZE = 2 + CRC_BYTES


def crc_from_config(value):
    if value == "CRC4":
        return CRC4
    if value == "CRC6":
        return CRC6
    if value == "CRC8":
        return CRC8

    if value == "CRC16":
        return CRC16

    return value


def apply_config(cfg):
    global FRAME_SIZE
    global TIMEOUT_MS
    global MAX_CHUNKS
    global MAX_RETRIES_PER_FRAME
    global RFC_FILE
    global CRC_POLY

    if "frame_size" in cfg:
        FRAME_SIZE = int(cfg["frame_size"])

    if "timeout_ms" in cfg:
        TIMEOUT_MS = int(cfg["timeout_ms"])

    if "max_chunks" in cfg:
        MAX_CHUNKS = cfg["max_chunks"]

        if MAX_CHUNKS is not None:
            MAX_CHUNKS = int(MAX_CHUNKS)

    if "max_retries_per_frame" in cfg:
        MAX_RETRIES_PER_FRAME = int(cfg["max_retries_per_frame"])

    if "rfc_file" in cfg:
        RFC_FILE = cfg["rfc_file"]

    if "crc" in cfg:
        CRC_POLY = crc_from_config(cfg["crc"])

    recalculate_sizes()

    if MAX_DATA_BYTES <= 0:
        raise ValueError("FRAME_SIZE is too small for header and CRC")


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
def scan_wifi(wlan):

    time.sleep(2)
    print(sys.version)
    print(sys.implementation)
    for net in wlan.scan():
        ssid = net[0].decode()
        channel = net[2]
        rssi = net[3]
        security = net[4]
        hidden = net[5]
        print(ssid, "channel:", channel, "rssi:", rssi, "security:", security, "hidden:", hidden)

def connect_wifi():
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    scan_wifi(wlan)
    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    for i in range(30):
        status = wlan.status()
        print("status:", status, "connected:", wlan.isconnected())

        if wlan.isconnected():
            print("WiFi connected.")
            print("IP:", wlan.ifconfig()[0])
            return wlan

        if status < 0:
            raise RuntimeError("WiFi failed with status: " + str(status))

        time.sleep(1)

    raise RuntimeError("WiFi timeout. Last status: " + str(wlan.status()))


def recv_json_line(conn):
    data = b""
    while True:

        chunk = conn.recv(1)

        if not chunk:
            raise OSError("TCP connection closed")

        if chunk == b"\n":
            break

        data += chunk

    return ujson.loads(data.decode())


def send_json_line(conn, obj):
    conn.write(ujson.dumps(obj).encode() + b"\n")


def open_config_server():
    addr = socket.getaddrinfo("0.0.0.0", CONTROL_PORT)[0][-1]

    server = socket.socket()

    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass

    server.bind(addr)
    server.listen(1)

    print("Waiting for PC config on port", CONTROL_PORT)

    conn, client_addr = server.accept()

    print("PC connected:", client_addr)

    cfg = recv_json_line(conn)

    return cfg, conn, server


def load_file_chunks(filename, max_data_bytes, max_chunks=None):
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
    sent_chunks = 0
    gave_up = False

    start_ms = time.ticks_ms()

    for i, message in enumerate(messages):
        retries = send_message_until_ack(uart, message, sequence_number)

        if retries is None:
            print("Giving up at message", i)
            gave_up = True
            break

        total_retries += retries
        sent_chunks += 1

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
    print("Sent chunks:", sent_chunks)
    print("Total retries:", total_retries)
    print("Duration:", duration_ms / 1000, "s")
    print("FRAME_SIZE:", FRAME_SIZE)
    print("MAX_DATA_BYTES:", MAX_DATA_BYTES)
    print("CRC_BITS:", CRC_BITS)
    print("==========================")

    return {
        "device": "A",
        "role": "sender",
        "status": "sender_done",
        "sent_chunks": sent_chunks,
        "planned_chunks": len(messages),
        "total_retries": total_retries,
        "duration_s": duration_ms / 1000,
        "frame_size": FRAME_SIZE,
        "max_data_bytes": MAX_DATA_BYTES,
        "crc_bits": CRC_BITS,
        "crc_bytes": CRC_BYTES,
        "gave_up": gave_up,
        "total_transmissions": sent_chunks + total_retries,
    }

def run_once():
    cfg, pc_conn, server = open_config_server()
    try:
        apply_config(cfg)

        send_json_line(pc_conn, {
            "device": "B",
            "role": "receiver",
            "status": "config_received",
            "frame_size": FRAME_SIZE,
            "max_data_bytes": MAX_DATA_BYTES,
            "crc_bits": CRC_BITS,
        })

        uart = create_uart()
        flush_uart(uart)
        messages = load_file_chunks(RFC_FILE, MAX_DATA_BYTES, MAX_CHUNKS)

        print("Loaded chunks:", len(messages))
        print("FRAME_SIZE:", FRAME_SIZE)
        print("MAX_DATA_BYTES:", MAX_DATA_BYTES)
        print("CRC_BITS:", CRC_BITS)

        result = send_all_messages(uart, messages)

        send_json_line(pc_conn, result)

        # everything that currently happens after config
        # goes here: load chunks, receive loop, stats, send result

    finally:
        try:
            pc_conn.close()
        except:
            pass

        try:
            server.close()
        except:
            pass

        time.sleep_ms(500)



def main():
    connect_wifi()

    while True:
        try:
            run_once()
            print("Run finished. Waiting for next config...")
        except Exception as e:
            print("Run crashed:", e)
            time.sleep_ms(1000)


main()