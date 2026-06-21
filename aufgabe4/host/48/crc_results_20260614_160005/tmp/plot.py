"""
Plot raw_runs.jsonl from the CRC/ARQ experiments.

Usage:
    python plot_raw_runs.py raw_runs.jsonl
    python plot_raw_runs.py raw_runs.jsonl --out plots

The script creates:
    plots/summary_by_config.csv
    plots/duration_s.png
    plots/throughput_payload_bytes_per_s.png
    plots/total_retries.png
    plots/detected_crc_errors.png
    plots/wire_overhead_ratio.png
    plots/overhead_bytes.png
    plots/retry_rate.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


CRC_ORDER = ["CRC4", "CRC8", "CRC16"]


def flatten_run(obj: dict[str, Any]) -> dict[str, Any]:
    """Flatten one JSON object from the JSONL file."""
    row: dict[str, Any] = {
        "run_id": obj.get("run_id"),
        "frame_size": obj.get("frame_size"),
        "crc": obj.get("crc"),
        "run_number": obj.get("run_number"),
    }

    result = obj.get("result", {})
    for section in ("config", "receiver", "sender"):
        values = result.get(section, {})
        if isinstance(values, dict):
            for key, value in values.items():
                row[f"{section}_{key}"] = value

    return row


def load_runs(path: Path) -> pd.DataFrame:
    """Load and flatten a raw_runs.jsonl file."""
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                rows.append(flatten_run(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in line {line_number}: {exc}") from exc

    if not rows:
        raise ValueError("No runs found in the file.")

    df = pd.DataFrame(rows)

    df["crc"] = pd.Categorical(df["crc"], categories=CRC_ORDER, ordered=True)

    # Derived metrics that are useful for plots.
    df["duration_s"] = df["receiver_duration_s"].fillna(df.get("sender_duration_s"))
    df["payload_bytes_per_s"] = df["receiver_payload_bytes_accepted"] / df["duration_s"]
    df["wire_overhead_ratio"] = df["receiver_wire_overhead_bytes"] / df["receiver_bytes_received"]
    df["retry_rate"] = df["sender_total_retries"] / df["sender_sent_chunks"]
    df["detected_error_rate"] = df["receiver_detected_crc_errors"] / df["receiver_frames_received"]
    df["duplicate_rate"] = df["receiver_duplicate_last_confirmed"] / df["receiver_frames_received"]

    return df.sort_values(["frame_size", "crc", "run_number"])


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate repeated runs by frame size and CRC."""
    metrics = [
        "duration_s",
        "payload_bytes_per_s",
        "sender_total_retries",
        "retry_rate",
        "receiver_detected_crc_errors",
        "detected_error_rate",
        "receiver_wire_overhead_bytes",
        "wire_overhead_ratio",
        "receiver_duplicate_last_confirmed",
        "duplicate_rate",
    ]

    summary = (
        df.groupby(["frame_size", "crc"], observed=True)[metrics]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
    )

    # Flatten multiindex columns.
    summary.columns = [
        "_".join(str(part) for part in col if part != "") for col in summary.columns
    ]
    return summary


def plot_metric(
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    out_path: Path,
) -> None:
    """
    Plot mean metric by frame size, one line per CRC.
    Error bars show standard deviation over repeated runs.
    """
    grouped = (
        df.groupby(["frame_size", "crc"], observed=True)[metric]
        .agg(["mean", "std"])
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    for crc in CRC_ORDER:
        part = grouped[grouped["crc"] == crc].sort_values("frame_size")
        if part.empty:
            continue

        ax.errorbar(
            part["frame_size"],
            part["mean"],
            yerr=part["std"].fillna(0),
            marker="o",
            capsize=4,
            label=crc,
        )

    ax.set_title(title)
    ax.set_xlabel("Frame size in bytes")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend(title="CRC")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_grouped_bars(
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    out_path: Path,
) -> None:
    """Alternative grouped bar plot for metrics where direct comparison is nicer."""
    grouped = (
        df.groupby(["frame_size", "crc"], observed=True)[metric]
        .mean()
        .unstack("crc")
        .reindex(columns=CRC_ORDER)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    grouped.plot(kind="bar", ax=ax)

    ax.set_title(title)
    ax.set_xlabel("Frame size in bytes")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(title="CRC")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to raw_runs.jsonl")
    parser.add_argument("--out", type=Path, default=Path("plots"), help="Output folder")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    df = load_runs(args.input)
    summary = summarize(df)

    df.to_csv(args.out / "runs_flat.csv", index=False)
    summary.to_csv(args.out / "summary_by_config.csv", index=False)

    # These skip total_transmissions and undetected_errors on purpose.
    plot_metric(
        df,
        "duration_s",
        "Duration in seconds",
        "Transmission duration by frame size and CRC",
        args.out / "duration_s.png",
    )

    plot_metric(
        df,
        "payload_bytes_per_s",
        "Payload bytes per second",
        "Useful payload throughput",
        args.out / "throughput_payload_bytes_per_s.png",
    )

    plot_metric(
        df,
        "sender_total_retries",
        "Retries",
        "Retries by frame size and CRC",
        args.out / "total_retries.png",
    )

    plot_metric(
        df,
        "receiver_detected_crc_errors",
        "Detected CRC errors",
        "Detected CRC errors by frame size and CRC",
        args.out / "detected_crc_errors.png",
    )

    plot_metric(
        df,
        "wire_overhead_ratio",
        "Overhead share of received bytes",
        "Wire overhead ratio",
        args.out / "wire_overhead_ratio.png",
    )

    plot_grouped_bars(
        df,
        "receiver_wire_overhead_bytes",
        "Overhead bytes",
        "Wire overhead bytes",
        args.out / "overhead_bytes.png",
    )

    plot_metric(
        df,
        "retry_rate",
        "Retries per accepted chunk",
        "Retry rate",
        args.out / "retry_rate.png",
    )

    print(f"Loaded {len(df)} runs")
    print(f"Saved plots and CSV files to: {args.out.resolve()}")


if __name__ == "__main__":
    main()