"""Plotting and study runners for the communication simulation.

This module imports the reusable math/simulation functions from
communication_logic.py and keeps all matplotlib code in one place.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
from komm import PSKModulation, QAModulation, RectangularPulse

from communication_logic import (
    add_awgn_noise,
    amplitude_demodulation,
    amplitude_modulation,
    bit2symbol,
    bit_error_probability,
    bits_per_symbol,
    constellation_points,
    derived_parameters,
    integrate_and_dump,
    pulse_shaping,
    simulate_ber_symbol_level,
    simulate_symbol_level_once,
    symbol2bit,
)


def default_modulation_schemes() -> dict[str, object]:
    return {
        "BPSK": PSKModulation(2),
        "QPSK": PSKModulation(4),
        "16QAM": QAModulation(16),
        "64QAM": QAModulation(64),
    }


def plot_frequency_snr_study() -> None:
    rb = 2
    fc = 4
    fs = 64

    symbol_count = 16
    mod_scheme = PSKModulation(4)
    pulse = RectangularPulse()

    m = bits_per_symbol(mod_scheme)
    k = symbol_count * m

    snr_values = [50, 30, 20, 10, 5, 0]

    np.random.seed(1)

    bit_sequence = np.random.randint(0, 2, k)
    params = derived_parameters(k, rb, fs, mod_scheme)

    symbol_sequence = bit2symbol(bit_sequence, mod_scheme)
    bb_signal = pulse_shaping(symbol_sequence, pulse, params["ns"])
    fb_signal = amplitude_modulation(bb_signal, fc, fs)

    output_dir = "frequency_snr_study"
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(
        len(snr_values),
        1,
        figsize=(10, 4 * len(snr_values)),
        sharex=True,
        constrained_layout=True,
    )

    if len(snr_values) == 1:
        axes = [axes]

    frequencies = np.fft.fftshift(np.fft.fftfreq(len(fb_signal), d=1 / fs))
    original_spectrum = np.fft.fftshift(np.fft.fft(fb_signal))
    original_mag = np.abs(original_spectrum)

    for ax, snr_db in zip(axes, snr_values):
        noisy_fb_signal = add_awgn_noise(fb_signal, snr_db)

        noisy_spectrum = np.fft.fftshift(np.fft.fft(noisy_fb_signal))
        noisy_mag = np.abs(noisy_spectrum)
        ax.plot(
            frequencies,
            noisy_mag,
            label=f"Noisy, SNR = {snr_db} dB",
            alpha=0.7,
        )

        ax.plot(
            frequencies,
            original_mag,
            label="Original",
        )

        ax.set_title(f"Frequenzbereich des Bandpasssignals bei SNR = {snr_db} dB", pad=12)
        ax.set_ylabel("Magnitude")
        ax.grid(True)
        ax.legend()

    axes[-1].set_xlabel("Frequenz [Hz]")

    filename = os.path.join(output_dir, "frequency_snr_study_all.png")
    fig.savefig(filename, dpi=200)
    plt.show()


def plot_ber_study() -> None:
    modulation_schemes = default_modulation_schemes()
    snr_values = np.arange(-10, 36, 2)
    k = 100000

    plt.figure(figsize=(10, 6))

    for name, mod_scheme in modulation_schemes.items():
        ber_values = []

        for snr_db in snr_values:
            ber = simulate_ber_symbol_level(mod_scheme, snr_db, k=k)
            ber_values.append(ber)

        ber_values = np.asarray(ber_values)

        # For logarithmic plots, zero cannot be displayed.
        ber_values_for_plot = np.maximum(ber_values, 1 / k)

        plt.semilogy(snr_values, ber_values_for_plot, marker="o", label=name)

    plt.xlabel("SNR [dB]")
    plt.ylabel("Bit Error Probability")
    plt.title("Bit Error Probability over SNR")
    plt.ylim(1e-4, 0.5)
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_one_symbol_constellation(
    ax,
    name: str,
    mod_scheme,
    snr_db: float,
    tx_symbols,
    rx_symbols,
    ber: float,
    max_points: int = 3000,
) -> None:
    """Plot ideal and noisy symbols into one matplotlib axes object."""
    ideal = constellation_points(mod_scheme, tx_symbols)

    if len(rx_symbols) > max_points:
        idx = np.random.choice(len(rx_symbols), max_points, replace=False)
        rx_plot = rx_symbols[idx]
    else:
        rx_plot = rx_symbols

    ax.scatter(
        np.real(rx_plot),
        np.imag(rx_plot),
        s=5,
        alpha=0.25,
        label="verrauschte Punkte",
    )

    ax.scatter(
        np.real(ideal),
        np.imag(ideal),
        s=90,
        marker="x",
        linewidths=2,
        label="ideale Symbole",
    )

    all_points = np.concatenate([ideal, rx_plot])
    max_abs = np.max(
        [
            np.max(np.abs(np.real(all_points))),
            np.max(np.abs(np.imag(all_points))),
            1.0,
        ]
    )
    limit = 1.2 * max_abs

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal", adjustable="box")

    ax.axhline(0, linewidth=0.5)
    ax.axvline(0, linewidth=0.5)
    ax.grid(True)

    ax.set_title(f"{name}, SNR = {snr_db} dB\nBER = {ber:.3e}")
    ax.set_xlabel("I")
    ax.set_ylabel("Q")


def plot_symbol_level_constellation_study(k: int = 200000, snr_values=(20, 10, 5, 0), max_points: int = 3000,) -> dict[str, dict[float, float]]:

    """Create constellation diagrams and print the BER table."""
    modulation_schemes = default_modulation_schemes()

    np.random.seed(1)

    fig, axes = plt.subplots(
        len(modulation_schemes),
        len(snr_values),
        figsize=(4 * len(snr_values), 4 * len(modulation_schemes)),
        squeeze=False,
    )

    ber_results = {}

    for row, (name, mod_scheme) in enumerate(modulation_schemes.items()):
        ber_results[name] = {}

        for col, snr_db in enumerate(snr_values):
            result = simulate_symbol_level_once(mod_scheme, snr_db, k=k)
            ber_results[name][snr_db] = result["ber"]

            plot_one_symbol_constellation(
                axes[row][col],
                name,
                mod_scheme,
                snr_db,
                result["tx_symbols"],
                result["rx_symbols"],
                result["ber"],
                max_points=max_points,
            )

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2)
    fig.suptitle("Symbol-Level Studie: Konstellationsdiagramme mit AWGN", y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()

    print_ber_table(ber_results, snr_values)
    return ber_results


def print_ber_table(ber_results, snr_values) -> None:
    """Print BER values as a small console table."""
    header = "Modulation".ljust(12)
    for snr_db in snr_values:
        header += f"{snr_db:>12} dB"
    print(header)

    for name, values in ber_results.items():
        row = name.ljust(12)
        for snr_db in snr_values:
            row += f"{values[snr_db]:12.3e}\t"
        print(row)


def plot_symbol_level_ber_curve(
    k: int = 200000,
    snr_values=np.arange(-4, 31, 2),
) -> None:
    """Additional plot: BER curve over many SNR values."""
    modulation_schemes = default_modulation_schemes()

    np.random.seed(2)

    plt.figure(figsize=(10, 6))

    for name, mod_scheme in modulation_schemes.items():
        ber_values = []

        for snr_db in snr_values:
            result = simulate_symbol_level_once(mod_scheme, snr_db, k=k)
            ber_values.append(result["ber"])

        ber_values = np.asarray(ber_values)
        ber_values_for_plot = np.maximum(ber_values, 1 / k)

        plt.semilogy(snr_values, ber_values_for_plot, marker="o", label=name)

    plt.xlabel("SNR [dB]")
    plt.ylabel("Bitfehlerwahrscheinlichkeit")
    plt.ylim(1e-5, 0.5)
    plt.title("Bitfehlerwahrscheinlichkeit auf Symbolebene")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_bandpass_spectrum(fb_signal, fs: float, noisy_fb_signal=None) -> None:
    frequencies = np.fft.fftfreq(len(fb_signal), d=1 / fs)
    spectrum = np.fft.fft(fb_signal)

    plt.figure(figsize=(10, 4))
    plt.plot(frequencies, np.abs(spectrum), label="Original")

    if noisy_fb_signal is not None:
        noisy_spectrum = np.fft.fft(noisy_fb_signal)
        plt.plot(frequencies, np.abs(noisy_spectrum), label="Noisy")

    plt.title("Bandpass Signal (Frequency Domain)")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_bandpass_signals(fb_signal, noisy_fb_signal=None) -> None:
    t = np.arange(len(fb_signal))

    plt.figure(figsize=(10, 4))
    plt.plot(t, fb_signal, label="Original")

    if noisy_fb_signal is not None:
        plt.plot(t, noisy_fb_signal, label="Noisy")

    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.title("Bandpass Signal")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_baseband_signals(bb_signal, noisy_bb_signal=None) -> None:
    t = np.arange(len(bb_signal))

    plt.figure(figsize=(10, 6))

    plt.subplot(2, 1, 1)
    plt.plot(t, np.real(bb_signal), label="Original")
    if noisy_bb_signal is not None:
        plt.plot(t, np.real(noisy_bb_signal), label="Noisy")
    plt.ylabel("I")
    plt.title("Baseband Signal")
    plt.grid(True)
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(t, np.imag(bb_signal), label="Original")
    if noisy_bb_signal is not None:
        plt.plot(t, np.imag(noisy_bb_signal), label="Noisy")
    plt.xlabel("Sample index")
    plt.ylabel("Q")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()


def plot_konstellations_diagramm(original_symbols, recovered_symbols, noisy_symbols=None) -> None:
    plt.figure(figsize=(6, 6))
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)

    plt.scatter(
        np.real(original_symbols),
        np.imag(original_symbols),
        marker="o",
        s=100,
        label="Original",
    )

    if noisy_symbols is not None:
        plt.scatter(
            np.real(noisy_symbols),
            np.imag(noisy_symbols),
            marker=".",
            s=30,
            label="Noisy",
        )

    plt.scatter(
        np.real(recovered_symbols),
        np.imag(recovered_symbols),
        marker="x",
        s=80,
        label="Recovered",
    )

    plt.axhline(0, linewidth=0.5)
    plt.axvline(0, linewidth=0.5)
    plt.xlabel("In Phase (I)")
    plt.ylabel("Quadrature (Q)")
    plt.title("Constellation Diagram")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()
    plt.show()


def demo_end_to_end() -> None:
    """Small end-to-end demo from the original main function."""
    k = 10
    rb = 2
    fc = 4
    fs = 64
    snr_db = 20

    mod_scheme = PSKModulation(4)
    pulse = RectangularPulse()
    bit_sequence = np.array([1, 0, 1, 1, 0, 0, 0, 1, 1, 0])

    params = derived_parameters(k, rb, fs, mod_scheme)
    symbol_sequence = bit2symbol(bit_sequence, mod_scheme)
    bb_signal = pulse_shaping(symbol_sequence, pulse, params["ns"])
    fb_signal = amplitude_modulation(bb_signal, fc, fs)
    noisy_fb_signal = add_awgn_noise(fb_signal, snr_db)
    recovered_bb_signal = amplitude_demodulation(noisy_fb_signal, fc, fs)
    recovered_symbol_sequence = integrate_and_dump(recovered_bb_signal, params["ns"])
    recovered_bit_sequence = symbol2bit(recovered_symbol_sequence, mod_scheme)

    print("Aufgabe 1.1 - Parameter")
    print(f"m  = {params['m']} bit/Symbol")
    print(f"s  = {params['s']} Symbole")
    print(f"rs = {params['rs']} Symbole/s")
    print(f"Ts = {params['Ts']} s")
    print(f"ns = {params['ns']} Samples/Symbol")
    print()
    print("Aufgabe 1.2 - Sender")
    print("Bits:", bit_sequence)
    print("Symbole:", np.round(symbol_sequence, 3))
    print("Basisbandsignal, erste 12 Samples:", np.round(bb_signal[:12], 3))
    print("Bandpasssignal, erste 12 Samples:", np.round(fb_signal[:12], 3))
    print()
    print("Aufgabe 1.3 - Empfaenger")
    print(
        "Demoduliertes Basisbandsignal, erste 12 Samples:",
        np.round(recovered_bb_signal[:12], 3),
    )
    print("Wiedergewonnene Symbole:", np.round(recovered_symbol_sequence, 3))
    print("Wiedergewonnene Bits:", recovered_bit_sequence)
    print("Bitfolgen identisch:", np.array_equal(bit_sequence, recovered_bit_sequence))

    plot_konstellations_diagramm(symbol_sequence, recovered_symbol_sequence)
    plot_baseband_signals(bb_signal, recovered_bb_signal)
    plot_bandpass_signals(fb_signal, noisy_fb_signal)
    plot_bandpass_spectrum(fb_signal, fs, noisy_fb_signal=noisy_fb_signal)

    ber = bit_error_probability(bit_sequence, recovered_bit_sequence)
    print("Bit Error Probability:", ber)


if __name__ == "__main__":
    # For the current symbol-level task:


    # For the previous frequency-domain task with few symbols:
    plot_symbol_level_constellation_study()
    plot_frequency_snr_study()
    plot_symbol_level_ber_curve(k=200000)
    # For the small original end-to-end demo:
    #demo_end_to_end()

    # For the old BER plot:
    # plot_ber_study()
