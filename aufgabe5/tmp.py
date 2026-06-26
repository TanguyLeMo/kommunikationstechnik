from math import log2, pi
import os
import matplotlib.pyplot as plt
import numpy as np
from komm import PSKModulation, RectangularPulse, TransmitFilter, QAModulation
def plot_frequency_snr_study():
    rb = 2
    fc = 4
    fs = 64

    symbol_count = 16       # <= 20 Symbole
    mod_scheme = PSKModulation(4)   # QPSK
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

    for snr_db in snr_values:
        noisy_fb_signal = add_awgn_noise(fb_signal, snr_db)

        frequencies = np.fft.fftshift(np.fft.fftfreq(len(fb_signal), d=1 / fs))

        original_spectrum = np.fft.fftshift(np.fft.fft(fb_signal))
        noisy_spectrum = np.fft.fftshift(np.fft.fft(noisy_fb_signal))

        plt.figure(figsize=(10, 4))

        plt.plot(
            frequencies,
            20 * np.log10(np.abs(original_spectrum) + 1e-12),
            label="Original"
        )

        plt.plot(
            frequencies,
            20 * np.log10(np.abs(noisy_spectrum) + 1e-12),
            label=f"Noisy, SNR = {snr_db} dB"
        )

        plt.title(f"Frequenzspektrum des Bandpasssignals bei SNR = {snr_db} dB")
        plt.xlabel("Frequenz [Hz]")
        plt.ylabel("Magnitude [dB]")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        filename = os.path.join(output_dir, f"spectrum_snr_{snr_db}dB.png")
        plt.savefig(filename, dpi=200)
        plt.show()

def add_awgn_noise_complex(signal, snr_db):
    signal = np.asarray(signal)

    signal_power = np.mean(np.abs(signal) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear

    noise = np.sqrt(noise_power / 2) * (
        np.random.normal(size=signal.shape)
        + 1j * np.random.normal(size=signal.shape)
    )

    return signal + noise

def simulate_ber_symbol_level(mod_scheme, snr_db, k=100000):
    m = bits_per_symbol(mod_scheme)
    if k % m != 0:
        k = k - (k % m)
    bit_sequence = np.random.randint(0, 2, k)
    symbol_sequence = bit2symbol(bit_sequence, mod_scheme)
    noisy_symbol_sequence = add_awgn_noise_complex(symbol_sequence,snr_db)
    recovered_bit_sequence = symbol2bit(noisy_symbol_sequence,mod_scheme)
    return bit_error_probability(bit_sequence,recovered_bit_sequence)


def plot_ber_study():
    modulation_schemes = {
        "BPSK": PSKModulation(2),
        "QPSK": PSKModulation(4),
        "16QAM": QAModulation(16),
        "64QAM": QAModulation(64),
    }

    snr_values = np.arange(-10, 36, 2)
    k = 100000

    plt.figure(figsize=(10, 6))

    for name, mod_scheme in modulation_schemes.items():
        ber_values = []
        for snr_db in snr_values:
            ber = simulate_ber_symbol_level(mod_scheme,snr_db,k=k)
            ber_values.append(ber)

        ber_values = np.array(ber_values)

        # Für logarithmische Darstellung: 0 kann nicht geplottet werden
        ber_values_for_plot = np.maximum(ber_values, 1 / k)

        plt.semilogy(
            snr_values,
            ber_values_for_plot,
            marker="o",
            label=name
        )

    plt.xlabel("SNR [dB]")
    plt.ylabel("Bit Error Probability")
    plt.title("Bit Error Probability over SNR")
    plt.ylim(1e-4, 0.5)
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.show()


def simulate_symbol_level_once(mod_scheme, snr_db, k=200000):
    """Simuliert eine reine Symbolkanal-Uebertragung.

    Ablauf:
    Bits -> Modulationssymbole -> komplexes AWGN -> Demodulation -> BER

    Auf Symbolebene werden bewusst kein Pulse Shaping, keine Traegermodulation
    und kein Tiefpass verwendet.
    """
    m = bits_per_symbol(mod_scheme)
    if k % m != 0:
        k = k - (k % m)

    tx_bits = np.random.randint(0, 2, k)
    tx_symbols = bit2symbol(tx_bits, mod_scheme)

    rx_symbols = add_awgn_noise_complex(tx_symbols, snr_db)

    rx_bits = symbol2bit(rx_symbols, mod_scheme)
    decided_symbols = bit2symbol(rx_bits, mod_scheme)

    ber = bit_error_probability(tx_bits, rx_bits)

    return {
        "tx_bits": tx_bits,
        "rx_bits": rx_bits,
        "tx_symbols": tx_symbols,
        "rx_symbols": rx_symbols,
        "decided_symbols": decided_symbols,
        "ber": ber,
    }


def constellation_points(mod_scheme, tx_symbols):
    """Liefert die idealen Konstellationspunkte."""
    if hasattr(mod_scheme, "constellation"):
        return np.asarray(mod_scheme.constellation)

    # Fallback, falls komm das Attribut bei einer Modulation nicht anbietet.
    return np.unique(np.round(tx_symbols, 12))


def plot_one_symbol_constellation(
    ax,
    name,
    mod_scheme,
    snr_db,
    tx_symbols,
    rx_symbols,
    ber,
    max_points=3000,
):
    """Plottet ideale und verrauschte Symbole in ein Achsenobjekt."""
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


def plot_symbol_level_constellation_study(k=200000,snr_values=(20, 10, 5, 0), max_points=3000,):
    """Erzeugt Konstellationsdiagramme und gibt die BER-Tabelle aus."""
    modulation_schemes = {
        "BPSK": PSKModulation(2),
        "QPSK": PSKModulation(4),
        "16QAM": QAModulation(16),
        "64QAM": QAModulation(64),
    }

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


def print_ber_table(ber_results, snr_values):
    """Gibt die BER-Werte sauber als Tabelle in der Konsole aus."""
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
    k=200000,
    snr_values=np.arange(-4, 31, 2),
):
    """Zusatzplot: BER-Verlauf ueber viele SNR-Werte."""
    modulation_schemes = {
        "BPSK": PSKModulation(2),
        "QPSK": PSKModulation(4),
        "16QAM": QAModulation(16),
        "64QAM": QAModulation(64),
    }

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
    plt.title("Bitfehlerwahrscheinlichkeit auf Symbolebene")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plt.show()



def plot_bandpass_spectrum(fb_signal, fs, noisy_fb_signal=None):
    frequencies = np.fft.fftfreq(len(fb_signal), d=1 / fs)

    spectrum = np.fft.fft(fb_signal)

    plt.figure(figsize=(10, 4))

    plt.plot(
        frequencies,
        np.abs(spectrum),
        label="Original"
    )

    if noisy_fb_signal is not None:
        noisy_spectrum = np.fft.fft(noisy_fb_signal)

        plt.plot(
            frequencies,
            np.abs(noisy_spectrum),
            label="Noisy"
        )

    plt.title("Bandpass Signal (Frequency Domain)")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

def plot_bandpass_signals(fb_signal, noisy_fb_signal=None):
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



def plot_baseband_signals(bb_signal, noisy_bb_signal=None):
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

def plot_konstellations_diagramm(original_symbols, recovered_symbols, noisy_symbols=None):
    plt.figure(figsize=(6, 6))
    plt.xlim(-1.5, 1.5)
    plt.ylim(-1.5, 1.5)
    plt.scatter(
        np.real(original_symbols),
        np.imag(original_symbols),
        marker="o",
        s=100,
        label="Original"
    )
    if noisy_symbols is not None:
        plt.scatter(
            np.real(noisy_symbols),
            np.imag(noisy_symbols),
            marker=".",
            s=30,
            label="Noisy"
        )
    plt.scatter(
        np.real(recovered_symbols),
        np.imag(recovered_symbols),
        marker="x",
        s=80,
        label="Recovered"
    )

    plt.axhline(0, color="gray", linewidth=0.5)
    plt.axvline(0, color="gray", linewidth=0.5)

    plt.xlabel("In Phase (I)")
    plt.ylabel("Quadrature (Q)")
    plt.title("Constellation Diagram")

    plt.grid(True)
    plt.axis("equal")
    plt.legend()

    plt.show()

def add_awgn_noise(signal, snr_db):
    signal_power = np.mean(np.abs(signal) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear

    noise = np.sqrt(noise_power) * np.random.normal(size=len(signal))

    return signal + noise

def bits_per_symbol(mod_scheme):
    if hasattr(mod_scheme, "bits_per_symbol"):
        return int(mod_scheme.bits_per_symbol)
    if hasattr(mod_scheme, "order"):
        return int(log2(mod_scheme.order))
    if hasattr(mod_scheme, "constellation"):
        return int(log2(len(mod_scheme.constellation)))
    raise ValueError("Bits pro Symbol konnten nicht aus dem Modulationsschema bestimmt werden.")


def derived_parameters(k, rb, fs, mod_scheme):
    m = bits_per_symbol(mod_scheme)
    if k % m != 0:
        raise ValueError("k muss ein Vielfaches der Bits pro Symbol m sein.")

    symbol_count = k // m
    symbol_rate = rb / m
    symbol_duration = 1 / symbol_rate
    samples_per_symbol = int(round(symbol_duration * fs))

    return {
        "m": m,
        "s": symbol_count,
        "rs": symbol_rate,
        "Ts": symbol_duration,
        "ns": samples_per_symbol,
    }


def bit2symbol(bit_sequence, mod_scheme):
    return mod_scheme.modulate(np.asarray(bit_sequence, dtype=int))

def pulse_shaping(symbol_sequence, pulse, nsamp) -> np.ndarray:
    transmit_filter = TransmitFilter(pulse, nsamp)
    symbols = np.asarray(symbol_sequence)
    i_signal = transmit_filter(np.real(symbols))
    q_signal = transmit_filter(np.imag(symbols))
    return (i_signal + 1j * q_signal) / nsamp


def amplitude_modulation(bb_signal, fc, fs):
    n = np.arange(len(bb_signal))
    cos_carrier = np.cos(2 * pi * fc / fs * n)
    sin_carrier = np.sin(2 * pi * fc / fs * n)
    return np.real(bb_signal) * cos_carrier + np.imag(bb_signal) * sin_carrier


def lowpass(signal, fs, cutoff_frequency):
    frequencies = np.fft.fftfreq(len(signal), 1 / fs)
    spectrum = np.fft.fft(signal)
    spectrum[np.abs(frequencies) > cutoff_frequency] = 0
    return np.fft.ifft(spectrum)


def amplitude_demodulation(fb_signal, fc, fs):
    n = np.arange(len(fb_signal))
    mixed_signal = (
        fb_signal * np.cos(2 * pi * fc / fs * n)
        +
        1j * fb_signal * np.sin(2 * pi * fc / fs * n)
    )
    return 2 * lowpass(mixed_signal, fs, fc)


def integrate_and_dump(bb_signal, nsamp):
    return np.array(
        [np.sum(bb_signal[i:i + nsamp]) for i in range(0, len(bb_signal), nsamp)]
    )

def bit_error_probability(original_bits, recovered_bits):
    original_bits = np.asarray(original_bits)
    recovered_bits = np.asarray(recovered_bits)

    bit_errors = np.sum(original_bits != recovered_bits)
    return bit_errors / len(original_bits)

def symbol2bit(symbol_sequence, mod_scheme):
    return mod_scheme.demodulate(np.asarray(symbol_sequence))

def main():
    k = 10
    rb = 2
    fc = 4
    fs = 64
    SNRdB = 20

    mod_scheme = PSKModulation(4)
    pulse = RectangularPulse()
    bit_sequence = np.array([1, 0, 1, 1, 0, 0, 0, 1, 1, 0])
    params = derived_parameters(k, rb, fs, mod_scheme)
    symbol_sequence = bit2symbol(bit_sequence, mod_scheme) # gib complexe Symbole zurück
    bb_signal = pulse_shaping(symbol_sequence, pulse, params["ns"])
    fb_signal = amplitude_modulation(bb_signal, fc, fs)
    noisy_fb_signal = add_awgn_noise(fb_signal, SNRdB)
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

    # 1.4.1
    plot_konstellations_diagramm(symbol_sequence, recovered_symbol_sequence)
    # 1.4.2
    plot_baseband_signals(bb_signal, recovered_bb_signal)
    # 1.4.3
    plot_bandpass_signals(fb_signal, noisy_fb_signal )

    plot_bandpass_spectrum(fb_signal, fs, noisy_fb_signal=noisy_fb_signal)
    BER = bit_error_probability(bit_sequence, recovered_bit_sequence)

    print("Bit Error Probability:", BER)

if __name__ == "__main__":

    # Fuer diese Teilaufgabe:
    plot_symbol_level_constellation_study()
    plot_symbol_level_ber_curve()

    # Fuer eure vorherige Frequenzbereichsaufgabe bei wenigen Symbolen:
    # plot_frequency_snr_study()

    # Fuer den alten BER-Plot:
    # plot_ber_study()