from machine import UART, Pin  # pyright: ignore[reportMissingImports]
import time
import sys
import network
import socket
import ujson


UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 0
UART_RX_PIN = 1

WIFI_SSID = "stairwaytoheaven"
WIFI_PASSWORD = "SalimisteinrichtigerMann!!!"

CONTROL_PORT = 5002

FRAME_SIZE = 16
START_SEQUENCE = 1

RFC_FILE = "rfc2324.txt"
OUT_FILE = "received_rfc2324.txt"

ACK_BYTE = 0xAA
NACK_BYTE = 0x00

CRC4 = "10011"
CRC6 = "1100001"
CRC8 = "100000111"
CRC16 = "10001000000100001"

CRC_POLY = CRC16

FRAME_HEADER_BYTES = 2

MAX_CHUNKS = None
EXPECTED_CHUNKS = None

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
    global MAX_CHUNKS
    global EXPECTED_CHUNKS
    global RFC_FILE
    global OUT_FILE
    global CRC_POLY

    if "frame_size" in cfg:
        FRAME_SIZE = int(cfg["frame_size"])

    if "max_chunks" in cfg:
        MAX_CHUNKS = cfg["max_chunks"]

        if MAX_CHUNKS is not None:
            MAX_CHUNKS = int(MAX_CHUNKS)

    if "expected_chunks" in cfg:
        EXPECTED_CHUNKS = cfg["expected_chunks"]

        if EXPECTED_CHUNKS is not None:
            EXPECTED_CHUNKS = int(EXPECTED_CHUNKS)

    if "rfc_file" in cfg:
        RFC_FILE = cfg["rfc_file"]

    if "out_file" in cfg:
        OUT_FILE = cfg["out_file"]

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


def parse_data_frame(frame):
    if frame is None:
        return None

    if len(frame) != FRAME_SIZE:
        return None

    msg_len = frame[0]
    seq = frame[1]

    data_area_start = 2
    data_area_end = 2 + MAX_DATA_BYTES

    data_area = frame[data_area_start:data_area_end]
    crc_bytes = frame[data_area_end:data_area_end + CRC_BYTES]

    crc_input = frame[:data_area_end]
    computed_crc = calc_crc(crc_input, CRC_POLY)
    received_crc = int.from_bytes(crc_bytes, "big")

    crc_ok = computed_crc == received_crc
    length_ok = msg_len <= MAX_DATA_BYTES

    if length_ok:
        data = data_area[:msg_len]
    else:
        data = data_area

    return {
        "seq": seq,
        "data": data,
        "crc_ok": crc_ok,
        "length_ok": length_ok,
        "computed_crc": computed_crc,
        "received_crc": received_crc,
    }


def create_control_frame(kind, seq):
    payload = bytes([kind, seq])
    crc = calc_crc(payload, CRC_POLY)
    return payload + crc.to_bytes(CRC_BYTES, "big")


def send_ack(uart, seq, stats):
    frame = create_control_frame(ACK_BYTE, seq)

    uart.write(frame)

    stats["acks_sent"] += 1
    print("Sending ACK for sequence", seq)


def send_nack(uart, seq, stats):
    frame = create_control_frame(NACK_BYTE, seq)

    uart.write(frame)

    stats["nacks_sent"] += 1
    print("Sending NACK for expected sequence", seq)


def flush_uart(uart):
    while uart.any():
        uart.read()


def print_summary(stats, total_expected_chunks, duration_ms):
    print()
    print("===== STATISTIK DEVICE B =====")
    print("Framegroesse:", FRAME_SIZE, "bytes")
    print("Maximale Nutzdaten pro Frame:", MAX_DATA_BYTES, "bytes")
    print("CRC Pruefbits:", CRC_BITS)
    print("CRC Bytes:", CRC_BYTES)
    print("Header plus CRC Overhead pro Frame:", FRAME_OVERHEAD_BYTES, "bytes")
    print()

    print("Erwartete Nutzdaten Frames:", total_expected_chunks)
    print("Empfangene Frames insgesamt:", stats["frames_received"])
    print("Akzeptierte Frames:", stats["accepted_frames"])
    print("Korrekte Uebertragungen:", stats["correct_transmissions"])
    print("Erkannte Uebertragungsfehler CRC:", stats["detected_crc_errors"])
    print("Unerkannte Uebertragungsfehler:", stats["undetected_errors"])
    print()

    print("Fehlerhafte Sequenznummern:")
    print("Wiederholung zuletzt bestaetigter Frame:", stats["duplicate_last_confirmed"])
    print("Vollkommen falsche Sequenznummer:", stats["wrong_sequence"])
    print()

    print("ACKs gesendet:", stats["acks_sent"])
    print("NACKs gesendet:", stats["nacks_sent"])
    print()

    print("Empfangene Bytes insgesamt:", stats["bytes_received"])
    print("Akzeptierte Nutzdaten Bytes:", stats["payload_bytes_accepted"])
    print("Header plus CRC Bytes insgesamt:", stats["frames_received"] * FRAME_OVERHEAD_BYTES)

    wire_overhead = stats["bytes_received"] - stats["payload_bytes_accepted"]
    print("Gesamter Overhead auf Leitung inklusive Padding und Wiederholungen:", wire_overhead, "bytes")

    print("Dauer:", duration_ms / 1000, "s")
    print("================================")


def create_result_json(stats, total_expected_chunks, duration_ms):
    result = {}

    for key in stats:
        result[key] = stats[key]

    result["device"] = "B"
    result["role"] = "receiver"
    result["status"] = "receiver_done"

    result["expected_chunks"] = total_expected_chunks
    result["duration_s"] = duration_ms / 1000

    result["frame_size"] = FRAME_SIZE
    result["max_data_bytes"] = MAX_DATA_BYTES
    result["crc_bits"] = CRC_BITS
    result["crc_bytes"] = CRC_BYTES
    result["frame_overhead_bytes"] = FRAME_OVERHEAD_BYTES

    result["header_crc_bytes_total"] = stats["frames_received"] * FRAME_OVERHEAD_BYTES
    result["wire_overhead_bytes"] = stats["bytes_received"] - stats["payload_bytes_accepted"]

    return result


def get_total_expected_chunks(original_chunks):
    if EXPECTED_CHUNKS is not None:
        return EXPECTED_CHUNKS

    return len(original_chunks)



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

        original_chunks = load_file_chunks(RFC_FILE, MAX_DATA_BYTES, MAX_CHUNKS)
        total_expected_chunks = get_total_expected_chunks(original_chunks)

        print("Device B ready.")
        print("Expected chunks:", total_expected_chunks)
        print("FRAME_SIZE:", FRAME_SIZE)
        print("MAX_DATA_BYTES:", MAX_DATA_BYTES)
        print("CRC_BITS:", CRC_BITS)
        print("Waiting for data...")

        stats = {
            "frames_received": 0,
            "accepted_frames": 0,
            "correct_transmissions": 0,
            "detected_crc_errors": 0,
            "undetected_errors": 0,
            "duplicate_last_confirmed": 0,
            "wrong_sequence": 0,
            "acks_sent": 0,
            "nacks_sent": 0,
            "bytes_received": 0,
            "payload_bytes_accepted": 0,
        }

        last_accepted_seq = (START_SEQUENCE - 1) % 256
        start_ms = None

        out = open(OUT_FILE, "wb")

        try:
            while stats["accepted_frames"] < total_expected_chunks:
                if uart.any() >= FRAME_SIZE:
                    frame = uart.read(FRAME_SIZE)

                    if start_ms is None:
                        start_ms = time.ticks_ms()

                    if frame is None:
                        stats["detected_crc_errors"] += 1
                        expected_seq = next_seq(last_accepted_seq)
                        send_nack(uart, expected_seq, stats)
                        continue

                    stats["frames_received"] += 1
                    stats["bytes_received"] += len(frame)

                    parsed = parse_data_frame(frame)
                    expected_seq = next_seq(last_accepted_seq)

                    if parsed is None:
                        stats["detected_crc_errors"] += 1
                        send_nack(uart, expected_seq, stats)
                        continue

                    seq = parsed["seq"]
                    data = parsed["data"]

                    if not parsed["crc_ok"] or not parsed["length_ok"]:
                        stats["detected_crc_errors"] += 1

                        print(
                            "Detected frame error. Expected CRC:",
                            parsed["computed_crc"],
                            "Received CRC:",
                            parsed["received_crc"],
                            "Seq:",
                            seq,
                        )

                        send_nack(uart, expected_seq, stats)
                        continue

                    if seq == expected_seq:
                        expected_data = original_chunks[stats["accepted_frames"]]

                        if data == expected_data:
                            stats["correct_transmissions"] += 1
                        else:
                            stats["undetected_errors"] += 1
                            print("UNDETECTED ERROR at accepted frame", stats["accepted_frames"])
                            print("Expected:", expected_data)
                            print("Got     :", data)

                        out.write(data)
                        stats["payload_bytes_accepted"] += len(data)
                        stats["accepted_frames"] += 1
                        last_accepted_seq = seq

                        send_ack(uart, seq, stats)

                    elif stats["accepted_frames"] > 0 and seq == last_accepted_seq:
                        stats["duplicate_last_confirmed"] += 1

                        print("Duplicate of last confirmed frame:", seq)
                        send_ack(uart, seq, stats)

                    else:
                        stats["wrong_sequence"] += 1

                        print(
                            "Wrong sequence number. Expected:",
                            expected_seq,
                            "Got:",
                            seq,
                        )

                        send_nack(uart, expected_seq, stats)

                else:
                    time.sleep_ms(1)

        finally:
            out.close()

        if start_ms is None:
            duration_ms = 0
        else:
            duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)

        print_summary(stats, total_expected_chunks, duration_ms)

        result = create_result_json(stats, total_expected_chunks, duration_ms)
        send_json_line(pc_conn, result)

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
            print("Receiver run finished. Waiting for next config...")
        except Exception as e:
            print("Receiver run crashed:", e)
            time.sleep_ms(1000)

main()