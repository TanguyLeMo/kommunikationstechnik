from math import log2, pi, sqrt

import numpy as np
from komm import PSKModulation, RectangularPulse, TransmitFilter
def _modulate_by_index(bits, bits_per_symbol, constellation):
    bit_sequence = np.asarray(bits, dtype=int)
    if len(bit_sequence) % bits_per_symbol != 0:
        raise ValueError("Die Bitanzahl muss durch die Bits pro Symbol teilbar sein.")

    groups = bit_sequence.reshape(-1, bits_per_symbol)
    weights = 2 ** np.arange(bits_per_symbol - 1, -1, -1)
    indexes = groups @ weights
    return constellation[indexes]


def _demodulate_by_distance(symbols, bits_per_symbol, constellation):
    distances = np.abs(np.asarray(symbols)[:, None] - constellation[None, :])
    indexes = np.argmin(distances, axis=1)
    shifts = np.arange(bits_per_symbol - 1, -1, -1)
    return ((indexes[:, None] >> shifts) & 1).reshape(-1)


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


def pulse_shaping(symbol_sequence, pulse, nsamp):
    transmit_filter = TransmitFilter(pulse, nsamp)
    return transmit_filter(np.asarray(symbol_sequence)) / nsamp


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
        + 1j * fb_signal * np.sin(2 * pi * fc / fs * n)
    )
    return 2 * lowpass(mixed_signal, fs, fc)


def integrate_and_dump(bb_signal, nsamp):
    return np.array(
        [np.sum(bb_signal[i:i + nsamp]) for i in range(0, len(bb_signal), nsamp)]
    )


def symbol2bit(symbol_sequence, mod_scheme):
    return mod_scheme.demodulate(np.asarray(symbol_sequence))

def main():
    k = 10
    rb = 2
    fc = 4
    fs = 64
    mod_scheme = PSKModulation(4)
    pulse = RectangularPulse()
    bit_sequence = np.array([1, 0, 1, 1, 0, 0, 0, 1, 1, 0])
    params = derived_parameters(k, rb, fs, mod_scheme)
    symbol_sequence = bit2symbol(bit_sequence, mod_scheme) # gib complexe Symbole zurück
    bb_signal = pulse_shaping(symbol_sequence, pulse, params["ns"])
    fb_signal = amplitude_modulation(bb_signal, fc, fs)
    recovered_bb_signal = amplitude_demodulation(fb_signal, fc, fs)
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


if __name__ == "__main__":
    main()
