import socket
import json
import matplotlib.pyplot as plt
import time
from itertools import product
from datetime import datetime
import csv
import os

DEVICE_A_IP = "192.168.180.138"
DEVICE_B_IP = "192.168.180.86"

PORT_A = 5001
PORT_B = 5002

REPEATS_PER_CONFIG = 5

FRAME_SIZES = [16, 32, 64]
CRCS = ["CRC4", "CRC8", "CRC16"]

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULT_DIR = "crc_results_" + RUN_ID


os.makedirs(RESULT_DIR, exist_ok=True)

RAW_JSONL_FILE = os.path.join(RESULT_DIR, "raw_runs.jsonl")
SUMMARY_JSON_FILE = os.path.join(RESULT_DIR, "summary.json")
SUMMARY_CSV_FILE = os.path.join(RESULT_DIR, "summary.csv")

EXPERIMENT_INFO = {
    "arduino_ber_threshold": 33,
    "approx_ber": 33 / 65536,
    "repeats_per_config": REPEATS_PER_CONFIG,
    "frame_sizes": FRAME_SIZES,
    "crcs": CRCS,
}

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

            sock.settimeout(None)
            return sock, file

        except OSError as e:
            last_error = e
            print("Port not ready yet:", e)
            time.sleep(1)

    raise last_error

def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def save_summary_csv(path, rows):
    fieldnames = [
        "frame_size",
        "crc",
        "runs",
        "successful_runs",
        "undetected_errors",
        "detected_crc_errors",
        "wrong_sequence",
        "duplicate_last_confirmed",
        "total_transmissions",
        "valid",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "frame_size": row["frame_size"],
                "crc": row["crc"],
                "runs": row["runs"],
                "successful_runs": row["successful_runs"],
                "undetected_errors": row["undetected_errors"],
                "detected_crc_errors": row["detected_crc_errors"],
                "wrong_sequence": row["wrong_sequence"],
                "duplicate_last_confirmed": row["duplicate_last_confirmed"],
                "total_transmissions": row["total_transmissions"],
                "valid": row["valid"],
            })


def run_simulation(cfg):
    print()
    print("Starting simulation:", cfg)

    sock_b = file_b = None
    sock_a = file_a = None

    try:
        # Erst B, damit der Empfänger bereit ist.
        sock_b, file_b = connect_and_send_config(DEVICE_B_IP, PORT_B, cfg)

        # Dann A, damit danach gesendet wird.
        sock_a, file_a = connect_and_send_config(DEVICE_A_IP, PORT_A, cfg)

        result_b = json.loads(file_b.readline().decode())

        print("Result from B:")
        print(json.dumps(result_b, indent=2))

        try:
            result_a = json.loads(file_a.readline().decode())
            print("Result from A:")
            print(json.dumps(result_a, indent=2))
        except Exception as e:
            print("No result from A:", e)
            result_a = {}

        return {
            "config": cfg,
            "receiver": result_b,
            "sender": result_a,
        }

    finally:
        for obj in [file_a, file_b, sock_a, sock_b]:
            try:
                if obj:
                    obj.close()
            except:
                pass


def get_metric(result, side, names, default=0):
    data = result.get(side, {})
    for name in names:
        if name in data:
            return data[name]
    return default


def make_config(frame_size, crc):
    return {
        "frame_size": frame_size,
        "crc": crc,
        "timeout_ms": 500,
        "max_chunks": None,
        "max_retries_per_frame": 500,
        "rfc_file": "rfc2324.txt",
        "out_file": "received_rfc2324.txt",
    }


all_results = []

for frame_size, crc in product(FRAME_SIZES, CRCS):
    cfg_results = []

    for run_number in range(REPEATS_PER_CONFIG):
        print()
        print("=" * 60)
        print("Config:", frame_size, crc, "Run:", run_number + 1, "/", REPEATS_PER_CONFIG)
        print("=" * 60)

        cfg = make_config(frame_size, crc)

        try:
            result = run_simulation(cfg)
            result["ok"] = True

        except Exception as e:
            result = {
                "ok": False,
                "config": cfg,
                "error": repr(e),
            }
            print("RUN FAILED:", repr(e))

        append_jsonl(RAW_JSONL_FILE, {
            "run_id": RUN_ID,
            "experiment_info": EXPERIMENT_INFO,
            "frame_size": frame_size,
            "crc": crc,
            "run_number": run_number + 1,
            "result": result,
        })

        cfg_results.append(result)

        time.sleep(2)

    successful_results = [
        r for r in cfg_results
        if r.get("ok")
    ]

    undetected = sum(
        get_metric(r, "receiver", ["undetected_errors"])
        for r in successful_results
    )

    detected = sum(
        get_metric(r, "receiver", ["detected_crc_errors"])
        for r in successful_results
    )

    wrong_sequence = sum(
        get_metric(r, "receiver", ["wrong_sequence"])
        for r in successful_results
    )

    duplicate_last_confirmed = sum(
        get_metric(r, "receiver", ["duplicate_last_confirmed"])
        for r in successful_results
    )

    total_transmissions = sum(
        get_metric(r, "sender", ["sent_chunks"])
        +
        get_metric(r, "sender", ["total_retries"])
        for r in successful_results
    )

    if total_transmissions == 0:
        total_transmissions = sum(
            get_metric(r, "receiver", ["frames_received"])
            for r in successful_results
        )

    summary = {
        "frame_size": frame_size,
        "crc": crc,
        "runs": REPEATS_PER_CONFIG,
        "successful_runs": len(successful_results),
        "undetected_errors": undetected,
        "detected_crc_errors": detected,
        "wrong_sequence": wrong_sequence,
        "duplicate_last_confirmed": duplicate_last_confirmed,
        "total_transmissions": total_transmissions,
        "valid": len(successful_results) == REPEATS_PER_CONFIG and undetected <= 3,
    }

    all_results.append(summary)

    save_json(SUMMARY_JSON_FILE, {
        "run_id": RUN_ID,
        "experiment_info": EXPERIMENT_INFO,
        "summary": all_results,
    })

    save_summary_csv(SUMMARY_CSV_FILE, all_results)

    print()
    print("CURRENT SUMMARY FOR CONFIG:")
    print(json.dumps(summary, indent=2))

print()
print("SUMMARY")
print(json.dumps(all_results, indent=2))


valid_results = [r for r in all_results if r["valid"]]

if valid_results:
    best = min(valid_results, key=lambda r: r["total_transmissions"])
    print()
    print("BEST CONFIG:")
    print(json.dumps(best, indent=2))
else:
    print()
    print("No valid config found. Try stronger CRC or smaller frame size.")

    
final_result = {
    "run_id": RUN_ID,
    "experiment_info": EXPERIMENT_INFO,
    "summary": all_results,
    "best_config": best if valid_results else None,
}

save_json(os.path.join(RESULT_DIR, "final_result.json"), final_result)

labels = [
    str(r["frame_size"]) + "B " + r["crc"]
    for r in all_results
]

undetected_values = [r["undetected_errors"] for r in all_results]
transmission_values = [r["total_transmissions"] for r in all_results]

plt.figure()
plt.bar(labels, undetected_values)
plt.xlabel("Konfiguration")
plt.ylabel("Unerkannte Framefehler bei 5 RFC Übertragungen")
plt.title("Datenintegrität")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "undetected_errors.png"), dpi=200)
plt.show()

plt.figure()
plt.bar(labels, transmission_values)
plt.xlabel("Konfiguration")
plt.ylabel("Anzahl benötigter Übertragungen")
plt.title("Übertragungsaufwand")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, "total_transmissions.png"), dpi=200)
plt.show()