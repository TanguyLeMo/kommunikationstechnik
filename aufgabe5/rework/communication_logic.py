"""Core communication/simulation logic without plotting.

This module contains the reusable parts of the simulation pipeline:
bit/symbol conversion, pulse shaping, modulation/demodulation, AWGN noise,
and BER simulation.
"""

from __future__ import annotations

from math import log2, pi

import numpy as np
from komm import TransmitFilter


def bits_per_symbol(mod_scheme) -> int:
    if hasattr(mod_scheme, "bits_per_symbol"):
        return int(mod_scheme.bits_per_symbol)
    if hasattr(mod_scheme, "order"):
        return int(log2(mod_scheme.order))
    if hasattr(mod_scheme, "constellation"):
        return int(log2(len(mod_scheme.constellation)))
    raise ValueError("Bits pro Symbol konnten nicht aus dem Modulationsschema bestimmt werden.")


def derived_parameters(k: int, rb: float, fs: float, mod_scheme) -> dict[str, float | int]:
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


def bit2symbol(bit_sequence, mod_scheme) -> np.ndarray:
    return mod_scheme.modulate(np.asarray(bit_sequence, dtype=int))


def symbol2bit(symbol_sequence, mod_scheme) -> np.ndarray:
    return mod_scheme.demodulate(np.asarray(symbol_sequence))


def pulse_shaping(symbol_sequence, pulse, nsamp: int) -> np.ndarray:
    transmit_filter = TransmitFilter(pulse, nsamp)
    symbols = np.asarray(symbol_sequence)

    i_signal = transmit_filter(np.real(symbols))
    q_signal = transmit_filter(np.imag(symbols))

    return (i_signal + 1j * q_signal) / nsamp


def amplitude_modulation(bb_signal, fc: float, fs: float) -> np.ndarray:
    n = np.arange(len(bb_signal))
    cos_carrier = np.cos(2 * pi * fc / fs * n)
    sin_carrier = np.sin(2 * pi * fc / fs * n)

    return np.real(bb_signal) * cos_carrier + np.imag(bb_signal) * sin_carrier


def lowpass(signal, fs: float, cutoff_frequency: float) -> np.ndarray:
    frequencies = np.fft.fftfreq(len(signal), 1 / fs)
    spectrum = np.fft.fft(signal)
    spectrum[np.abs(frequencies) > cutoff_frequency] = 0

    return np.fft.ifft(spectrum)


def amplitude_demodulation(fb_signal, fc: float, fs: float) -> np.ndarray:
    n = np.arange(len(fb_signal))
    mixed_signal = (
        fb_signal * np.cos(2 * pi * fc / fs * n)
        + 1j * fb_signal * np.sin(2 * pi * fc / fs * n)
    )

    # The factor 2 compensates the amplitude loss caused by mixing with the carrier.
    return 2 * lowpass(mixed_signal, fs, fc)


def integrate_and_dump(bb_signal, nsamp: int) -> np.ndarray:
    return np.array(
        [np.sum(bb_signal[i : i + nsamp]) for i in range(0, len(bb_signal), nsamp)]
    )


def add_awgn_noise(signal, snr_db: float) -> np.ndarray:
    """Add real AWGN noise, used for real-valued bandpass signals."""
    signal = np.asarray(signal)
    signal_power = np.mean(np.abs(signal) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear

    noise = np.sqrt(noise_power) * np.random.normal(size=len(signal))

    return signal + noise


def add_awgn_noise_complex(signal, snr_db: float) -> np.ndarray:
    """Add complex AWGN noise, used directly on symbol-level I/Q values."""
    signal = np.asarray(signal)
    signal_power = np.mean(np.abs(signal) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear

    noise = np.sqrt(noise_power / 2) * (
        np.random.normal(size=signal.shape) + 1j * np.random.normal(size=signal.shape)
    )

    return signal + noise


def bit_error_probability(original_bits, recovered_bits) -> float:
    original_bits = np.asarray(original_bits)
    recovered_bits = np.asarray(recovered_bits)

    bit_errors = np.sum(original_bits != recovered_bits)
    return bit_errors / len(original_bits)


def simulate_ber_symbol_level(mod_scheme, snr_db: float, k: int = 100000) -> float:
    m = bits_per_symbol(mod_scheme)
    if k % m != 0:
        k = k - (k % m)

    bit_sequence = np.random.randint(0, 2, k)
    symbol_sequence = bit2symbol(bit_sequence, mod_scheme)
    noisy_symbol_sequence = add_awgn_noise_complex(symbol_sequence, snr_db)
    recovered_bit_sequence = symbol2bit(noisy_symbol_sequence, mod_scheme)

    return bit_error_probability(bit_sequence, recovered_bit_sequence)


def simulate_symbol_level_once(mod_scheme, snr_db: float, k: int = 200000) -> dict[str, np.ndarray | float]:
    """Simulate one pure symbol-channel transmission.

    Flow:
    Bits -> modulation symbols -> complex AWGN -> demodulation -> BER

    On symbol level, this intentionally skips pulse shaping, carrier modulation,
    and low-pass filtering.
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


def constellation_points(mod_scheme, tx_symbols) -> np.ndarray:
    """Return the ideal constellation points for a modulation scheme."""
    if hasattr(mod_scheme, "constellation"):
        return np.asarray(mod_scheme.constellation)

    # Fallback in case the komm object does not expose a constellation attribute.
    return np.unique(np.round(tx_symbols, 12))
