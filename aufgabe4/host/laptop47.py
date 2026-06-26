import socket
import json
import matplotlib.pyplot as plt
import time

DEVICE_A_IP = "192.168.180.138"
DEVICE_B_IP = "192.168.180.86"


PORT_A = 5001
PORT_B = 5002

def connect_and_send_config(ip, port, cfg):
    last_error = None

    for attempt in range(30):
        try:
            print("Connecting to", ip, port, "attempt", attempt + 1)

            sock = socket.create_connection((ip, port), timeout=5)
            file = sock.makefile("rwb")

            file.write(json.dumps(cfg).encode() + b"\n")
            file.flush()

            ack_line = file.readline()

            if not ack_line:
                raise RuntimeError("Connection closed before ACK")

            ack = json.loads(ack_line.decode())
            print("ACK from", ip, ack)

            # Wichtig: ab jetzt unbegrenzt auf Resultate warten
            sock.settimeout(None)

            return sock, file

        except ConnectionRefusedError as e:
            last_error = e
            print("Port not ready yet")
            time.sleep(1)

    raise last_error

def run_simulation(cfg):
    print()
    print("Starting simulation:", cfg)

    sock_b, file_b = connect_and_send_config(DEVICE_B_IP, PORT_B, cfg)
    sock_a, file_a = connect_and_send_config(DEVICE_A_IP, PORT_A, cfg)

    result_b = json.loads(file_b.readline().decode())

    print("Result from B:")
    print(json.dumps(result_b, indent=2))

    try:
        result_a = json.loads(file_a.readline().decode())
        print("Result from A:")
        print(json.dumps(result_a, indent=2))
    except:
        result_a = None

    file_a.close()
    file_b.close()
    sock_a.close()
    sock_b.close()

    return result_b


configs = [
    {
        "frame_size": 16,
        "crc": "CRC16",
        "timeout_ms": 500,
        "max_chunks": None,
        "max_retries_per_frame": 500,
        "rfc_file": "rfc2324.txt",
        "out_file": "received_rfc2324.txt",
    },
    {
        "frame_size": 16,
        "crc": "CRC8",
        "timeout_ms": 500,
        "max_chunks": None,
        "max_retries_per_frame": 500,
        "rfc_file": "rfc2324.txt",
        "out_file": "received_rfc2324.txt",
    },
    {
        "frame_size": 32,
        "crc": "CRC16",
        "timeout_ms": 500,
        "max_chunks": None,
        "max_retries_per_frame": 500,
        "rfc_file": "rfc2324.txt",
        "out_file": "received_rfc2324.txt",
    },
]

results = []

for cfg in configs:
    result = run_simulation(cfg)
    results.append(result)


x = [str(r["frame_size"]) + "B CRC" + str(r["crc_bits"]) for r in results]
y = [r["detected_crc_errors"] for r in results]

plt.bar(x, y)
plt.xlabel("Konfiguration")
plt.ylabel("Erkannte CRC Fehler")
plt.title("Parameterstudie CRC Fehler")
plt.show()