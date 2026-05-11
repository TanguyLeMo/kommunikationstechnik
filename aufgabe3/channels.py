import random
import numpy as np

def flipbits(bit_vector, position_list) -> np.array:
    result = np.array(bit_vector, dtype=int).copy()
    for pos in position_list:
        result[pos] ^= 1
    return result

class FixedErrorChannel:
    def __init__(self, num_errors):
        self.num_errors = num_errors
    def __call__(self, bit_vector) -> np.array:
        n = len(bit_vector)
        if self.num_errors > n:
            raise ValueError("anzahl fehler kann nicht größer sein, als der vector selbst du ghandi")
        positions = random.sample(range(n), self.num_errors)
        return flipbits(bit_vector, positions)
class BinarySymmetricChannel:
    def __init__(self, error_prob):
        if (not error_prob >= 0) or (not error_prob <= 1):
            raise ValueError(f"wahrscheinlichkeit ist gerade bissl dumm: {error_prob}")
        self.error_prob = error_prob
    def __call__(self, bit_vector)-> np.array:
        ret_bit_vector = bit_vector.copy()
        for i in range(len(bit_vector)):
            if random.random() < self.error_prob:
                ret_bit_vector[i] ^= 1
        return ret_bit_vector