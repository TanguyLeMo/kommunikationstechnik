import numpy as np
from block_code import BlockCode
from channels import BinarySymmetricChannel, FixedErrorChannel
def simulate_transmission(block_code:BlockCode, channel):
    message = np.random.randint(0,2, block_code.k)
    codeword = block_code.encode(message)
    received = channel(codeword)
    decoded, corrected_bits = block_code.decode(received)
    bit_errors_before = int (np.sum(codeword != received))
    correction_performed = decoded is not None
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