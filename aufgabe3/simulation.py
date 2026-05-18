import numpy as np
from block_code import BlockCode
from channelss import BinarySymmetricChannel, FixedErrorChannel
from collections import Counter
#5.1
def simulate_transmission(block_code:BlockCode, channel):
    message = np.random.randint(0,2, block_code.k)
    codeword = block_code.encode(message)
    received = channel(codeword)
    decoded, corrected_bits = block_code.decode(received)
    bit_errors_before = int(np.sum(codeword != received))
    correction_performed = corrected_bits != 0
    bit_errors_after = 0

    if decoded is None:
        bit_errors_after = bit_errors_before
    else:
        corrected_codeword = block_code.encode(decoded)
        bit_errors_after = int(np.sum(codeword != corrected_codeword))

    return {
        "message" : message,
        "codeword" : codeword,
        "received" : received,
        "decoded" : decoded,
        "bit_errors_before" : bit_errors_before,
        "correction_performed" : correction_performed,
        "corrected_bits": corrected_bits,
        "bit_errors_after" : bit_errors_after,
    }

#5.2
def simulate_many_transmissions(count:int, block_code:BlockCode, channel):
    result = []
    for current_index in range(count):
        tmp = simulate_transmission(block_code, channel)
        result.append(tmp)
    error_free = 0
    corrected = 0
    faulty_not_corrected = 0
    successfully_corrected = 0
    wrongly_corrected = 0
    not_decoded = 0
    bit_errors_before_counter= Counter()
    corrected_bits_counter = Counter()
    bit_errors_after_counter = Counter()

    for simulation in result:
        bit_error_before = simulation["bit_errors_before"]
        bit_error_after = simulation["bit_errors_after"]
        decoded =  simulation["decoded"]
        corrected_bits = simulation["corrected_bits"]

        bit_errors_before_counter[bit_error_before] += 1
        corrected_bits_counter[corrected_bits] += 1
        bit_errors_after_counter[bit_error_after] += 1

        if decoded is None:
            not_decoded += 1
        if bit_error_before == 0:
            error_free += 1
        if decoded is not None and corrected_bits >= 1:
            corrected += 1
        if bit_error_before > 0 and corrected_bits == 0:
            faulty_not_corrected +=1
        if bit_error_before > 0 and decoded is not None and bit_error_after == 0:
            successfully_corrected += 1
        if bit_error_after > 0 and decoded is not None and bit_error_after > 0:
            wrongly_corrected += 1

    return {
            "N": count,
    "error_free_count": error_free,
    "corrected_count": corrected,
    "faulty_not_corrected_count": faulty_not_corrected,
    "successfully_corrected_count": successfully_corrected,
    "wrongly_corrected_count": wrongly_corrected,

    "error_free_ratio": error_free / count,
    "corrected_ratio": corrected / count,
    "faulty_not_corrected_ratio": faulty_not_corrected / count,
    "successfully_corrected_ratio": successfully_corrected / count,
    "wrongly_corrected_ratio": wrongly_corrected / count,

    "bit_errors_before_counter": bit_errors_before_counter,
    "corrected_bits_counter": corrected_bits_counter,
    "bit_errors_after_counter": bit_errors_after_counter,
    }
