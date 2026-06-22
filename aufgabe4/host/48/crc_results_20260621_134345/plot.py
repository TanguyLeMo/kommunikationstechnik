import json
import csv
from pathlib import Path

import matplotlib.pyplot as plt


RESULT_DIR = Path(__file__).resolve().parent

FRAME_SIZES = [16, 32, 64, 96, 128]
CRCS = ["CRC4", "CRC6", "CRC8", "CRC16"]


def load_results():
    final_json = RESULT_DIR / "final_result.json"
    summary_json = RESULT_DIR / "summary.json"
    summary_csv = RESULT_DIR / "summary.csv"

    if final_json.exists():
        with open(final_json, "r", encoding="utf-8") as f:
            return json.load(f)["summary"]

    if summary_json.exists():
        with open(summary_json, "r", encoding="utf-8") as f:
            return json.load(f)["summary"]

    if summary_csv.exists():
        rows = []
        with open(summary_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                converted = {}
                for key, value in row.items():
                    if value in ("", "None", None):
                        converted[key] = None
                    elif value in ("True", "False"):
                        converted[key] = value == "True"
                    else:
                        try:
                            converted[key] = int(value)
                        except ValueError:
                            try:
                                converted[key] = float(value)
                            except ValueError:
                                converted[key] = value
                rows.append(converted)
        return rows

    raise FileNotFoundError("No final_result.json, summary.json or summary.csv found.")


def find_row(rows, frame_size, crc):
    for row in rows:
        if row["frame_size"] == frame_size and row["crc"] == crc:
            return row
    return None


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

def save_and_close(filename):
    print("Showing:", filename)
    plt.show()
    plt.close()


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

    if description:
        add_plot_description(description)
    else:
        plt.tight_layout()

    save_and_close(filename)


def main():
    rows = load_results()

    labels = [
        str(r["frame_size"]) + "B " + r["crc"]
        for r in rows
    ]

    undetected_values = [r.get("undetected_errors", 0) for r in rows]
    transmission_values = [r.get("total_transmissions", 0) for r in rows]

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
    save_and_close("undetected_errors.png")

    plot_metric_by_frame_size(
        rows,
        "undetected_errors",
        "Unerkannte Framefehler bei 5 RFC Übertragungen",
        "Datenintegrität in Abhängigkeit von Framegröße und CRC",
        "integrity_by_frame_size.png",
        limit_line=3,
        description="Metrik: undetected_errors = Summe der unerkannten Framefehler pro Konfiguration. x = Framegröße, y = Fehleranzahl, eine Linie pro CRC."
    )

    plt.figure(figsize=(12, 6))
    plt.bar(labels, transmission_values)
    plt.xlabel("Konfiguration")
    plt.ylabel("Anzahl benötigter Übertragungen")
    plt.title("Übertragungsaufwand")
    plt.xticks(rotation=45, ha="right")
    add_plot_description(
        "Metrik: total_transmissions = sent_chunks + total_retries. Der Wert beschreibt die Anzahl aller gesendeten Datenframes inklusive Wiederholungen."
    )
    save_and_close("total_transmissions.png")

    plot_metric_by_frame_size(
        rows,
        "total_transmissions",
        "Benötigte Übertragungen",
        "Übertragungsaufwand in Abhängigkeit von Framegröße und CRC",
        "transmissions_by_frame_size.png",
        description="Metrik: total_transmissions = sent_chunks + total_retries. x = Framegröße, y = benötigte Datenframe Übertragungen, eine Linie pro CRC."
    )

    plot_metric_by_frame_size(
        rows,
        "retry_rate",
        "Retries pro gesendetem Chunk",
        "Retry Rate in Abhängigkeit von Framegröße und CRC",
        "retry_rate_by_frame_size.png",
        description="Metrik: retry_rate = total_retries / sent_chunks. Der Wert zeigt, wie viele Wiederholungen im Verhältnis zu den normal gesendeten Chunks nötig waren."
    )

    plt.figure(figsize=(10, 6))

    for r in rows:
        label = str(r["frame_size"]) + "B " + r["crc"]
        marker = "o" if r.get("valid") else "x"

        x = r.get("total_transmissions")
        y = r.get("undetected_errors")

        if x is None or y is None:
            continue

        plt.scatter(x, y, marker=marker)
        plt.text(x, y, label, fontsize=8)

    plt.axhline(3, linestyle=":", label="Grenze: maximal 3 unerkannte Fehler")
    plt.xlabel("Benötigte Übertragungen")
    plt.ylabel("Unerkannte Framefehler bei 5 RFC Übertragungen")
    plt.title("Entscheidungsplot: Datenintegrität vs. Übertragungsaufwand")
    plt.legend()
    add_plot_description(
        "Jeder Punkt ist eine Konfiguration. x = total_transmissions, y = undetected_errors. Kreis = gültig, Kreuz = ungültig. Gültig bedeutet: alle 5 Runs erfolgreich und undetected_errors <= 3."
    )
    save_and_close("decision_plot.png")

    print("Plots regenerated in:", RESULT_DIR)


if __name__ == "__main__":
    main()