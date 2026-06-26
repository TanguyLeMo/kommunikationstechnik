import socket
import json
import matplotlib.pyplot as plt
import time
from itertools import product
from datetime import datetime
import csv
import os

DEVICE_A_IP = "10.104.181.29"
DEVICE_B_IP = "10.104.181.45"

PORT_A = 5001
PORT_B = 5002

REPEATS_PER_CONFIG = 5

FRAME_SIZES = [16, 32, 64, 96, 128]
CRCS = ["CRC4", "CRC6", "CRC8", "CRC16"]

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
def value_for(rows, frame_size, crc, metric):
    row = find_row(rows, frame_size, crc)

    if row is None:
        return None

    return row.get(metric)
def add_plot_description(description):
    plt.figtext(
        0.5,
        0.01,
        description,
        ha="center",
        fontsize=8,
        wrap=True
    )

    plt.tight_layout(rect=[0, 0.08, 1, 1])

def plot_metric_by_frame_size(rows, metric, ylabel, title, filename, limit_line=None, description=None):
    plt.figure(figsize=(9, 5))

    for crc in CRCS:
        x_values = []
        y_values = []

        for frame_size in FRAME_SIZES:
            value = value_for(rows, frame_size, crc, metric)

            if value is not None:
                x_values.append(frame_size)
                y_values.append(value)

        plt.plot(x_values, y_values, marker="o", label=crc)

    if limit_line is not None:
        plt.axhline(limit_line, linestyle=":", label="Grenze: " + str(limit_line))

    plt.xlabel("Framegröße in Byte")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(FRAME_SIZES)
    plt.legend()

    if description is not None:
        add_plot_description(description)
    else:
        plt.tight_layout()

    plt.savefig(os.path.join(RESULT_DIR, filename), dpi=200, bbox_inches="tight")
    plt.show()

def find_row(rows, frame_size, crc):
    for row in rows:
        if row["frame_size"] == frame_size and row["crc"] == crc:
            return row
    return None


def crc_bits_from_name(crc):
    return int(crc.replace("CRC", ""))


def crc_bytes_from_name(crc):
    bits = crc_bits_from_name(crc)
    return (bits + 7) // 8


def frame_overhead_bytes(crc):
    return 2 + crc_bytes_from_name(crc)


def max_data_bytes_for(frame_size, crc):
    return frame_size - frame_overhead_bytes(crc)


def get_metric_or_none(result, side, names):
    data = result.get(side, {})
    for name in names:
        if name in data:
            return data[name]
    return None

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

    raise last_error # type: ignore

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
    #new begin
    sent_chunks = sum(
        get_metric(r, "sender", ["sent_chunks"])
        for r in successful_results
    )

    total_retries = sum(
        get_metric(r, "sender", ["total_retries"])
        for r in successful_results
    )

    accepted_frames = sum(
        get_metric(r, "receiver", ["accepted_frames", "frames_accepted"])
        for r in successful_results
    )

    acks_sent = sum(
        get_metric(r, "receiver", ["acks_sent"])
        for r in successful_results
    )

    nacks_sent = sum(
        get_metric(r, "receiver", ["nacks_sent"])
        for r in successful_results
    )

    duration_values = [
        get_metric_or_none(r, "receiver", ["duration", "duration_s", "duration_seconds"])
        for r in successful_results
    ]

    duration_values = [
        value for value in duration_values
        if value is not None
    ]

    avg_duration = (
        sum(duration_values) / len(duration_values)
        if duration_values
        else None
    )

    retry_rate = (
        total_retries / sent_chunks
        if sent_chunks > 0
        else None
    )

    transmissions_per_accepted_frame = (
        total_transmissions / accepted_frames
        if accepted_frames > 0
        else None
    )

    payload_efficiency = (
        max_data_bytes_for(frame_size, crc) / frame_size
    )

    data_bytes_est = total_transmissions * frame_size
    control_bytes_est = (acks_sent + nacks_sent) * frame_overhead_bytes(crc)
    estimated_wire_bytes = data_bytes_est + control_bytes_est
    # new end
    

    summary = {
        "frame_size": frame_size,
        "crc": crc,
        "runs": REPEATS_PER_CONFIG,
        "successful_runs": len(successful_results),

        "undetected_errors": undetected,
        "detected_crc_errors": detected,
        "wrong_sequence": wrong_sequence,
        "duplicate_last_confirmed": duplicate_last_confirmed,

        "sent_chunks": sent_chunks,
        "total_retries": total_retries,
        "total_transmissions": total_transmissions,
        "retry_rate": retry_rate,
        "accepted_frames": accepted_frames,
        "transmissions_per_accepted_frame": transmissions_per_accepted_frame,

        "payload_efficiency": payload_efficiency,
        "estimated_wire_bytes": estimated_wire_bytes,
        "avg_duration": avg_duration,

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
best = None

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
#first plot
plt.figure(figsize=(12, 6))
plt.bar(labels, undetected_values)
plt.axhline(3, linestyle=":", label="Grenze: maximal 3")
plt.xlabel("Konfiguration")
plt.ylabel("Unerkannte Framefehler bei 5 RFC Übertragungen")
plt.title("Datenintegrität")
plt.xticks(rotation=45, ha="right")
plt.legend()
add_plot_description(
    "Metrik: undetected_errors = Summe aller vom Empfänger gezählten unerkannten Framefehler über 5 RFC Übertragungen. Grenze aus der Aufgabenstellung: maximal 3."
)
plt.savefig(os.path.join(RESULT_DIR, "undetected_errors.png"), dpi=200, bbox_inches="tight")
plt.show()
plot_metric_by_frame_size(
    all_results,
    "undetected_errors",
    "Unerkannte Framefehler bei 5 RFC Übertragungen",
    "Datenintegrität in Abhängigkeit von Framegröße und CRC",
    "integrity_by_frame_size.png",
    limit_line=3,
    description="Metrik: undetected_errors = Summe der unerkannten Framefehler pro Konfiguration. x = Framegröße, y = Fehleranzahl, eine Linie pro CRC."
)
#
plt.figure(figsize=(12, 6))
plt.bar(labels, transmission_values)
plt.xlabel("Konfiguration")
plt.ylabel("Anzahl benötigter Übertragungen")
plt.title("Übertragungsaufwand")
plt.xticks(rotation=45, ha="right")
add_plot_description(
    "Metrik: total_transmissions = sent_chunks + total_retries. Der Wert beschreibt die Anzahl aller gesendeten Datenframes inklusive Wiederholungen."
)
plt.savefig(os.path.join(RESULT_DIR, "total_transmissions.png"), dpi=200, bbox_inches="tight")
plt.show()

plot_metric_by_frame_size(
    all_results,
    "total_transmissions",
    "Benötigte Übertragungen",
    "Übertragungsaufwand in Abhängigkeit von Framegröße und CRC",
    "transmissions_by_frame_size.png",
    description="Metrik: total_transmissions = sent_chunks + total_retries. x = Framegröße, y = benötigte Datenframe Übertragungen, eine Linie pro CRC."
)
plot_metric_by_frame_size(
    all_results,
    "retry_rate",
    "Retries pro gesendetem Chunk",
    "Retry Rate in Abhängigkeit von Framegröße und CRC",
    "retry_rate_by_frame_size.png",
    description="Metrik: retry_rate = total_retries / sent_chunks. Der Wert zeigt, wie viele Wiederholungen im Verhältnis zu den normal gesendeten Chunks nötig waren."
)


plt.figure(figsize=(10, 6))

for r in all_results:
    label = str(r["frame_size"]) + "B " + r["crc"]

    marker = "o" if r["valid"] else "x"
    x = r["total_transmissions"]
    y = r["undetected_errors"]
    plt.scatter(
        x,
        y,
        marker=marker
    )

    plt.text(
        x,
        y,
        label,
        fontsize=8
    )

plt.axhline(3, linestyle=":", label="Grenze: maximal 3 unerkannte Fehler")

plt.xlabel("Benötigte Übertragungen")
plt.ylabel("Unerkannte Framefehler bei 5 RFC Übertragungen")
plt.title("Entscheidungsplot: Datenintegrität vs. Übertragungsaufwand")
plt.legend()
add_plot_description(
    "Jeder Punkt ist eine Konfiguration. x = total_transmissions, y = undetected_errors. Kreis = gültig, Kreuz = ungültig. Gültig bedeutet: alle 5 Runs erfolgreich und undetected_errors <= 3."
)

plt.savefig(os.path.join(RESULT_DIR, "decision_plot.png"), dpi=200, bbox_inches="tight")
plt.show()