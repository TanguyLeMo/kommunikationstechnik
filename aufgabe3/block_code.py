import numpy as np
from itertools import combinations

class BlockCode:
    def __init__(self, P, max_correction_bits = 1):
        self.P = np.array(P, dtype=int)
        self.max_corr_bits = max_correction_bits
        self.k = self.P.shape[0]
        self.p = self.P.shape[1]
        self.n = self.k + self.p

        I_k = np.eye(self.k, dtype=int)
        I_p = np.eye(self.p, dtype=int)

        self.G = np.concatenate((I_k, self.P), axis=1)
        self.H = np.concatenate((self.P.T, I_p), axis=1)
        self.S = self._build_syndrome_table()

    def _build_syndrome_table(self):
        syndrome_table = {}
        for num_errors in range(1, self.max_corr_bits + 1):
            for error_positions in combinations(range(self.n), num_errors):
                error_vector = np.zeros(self.n, dtype=int)
                for pos in error_positions:
                    error_vector[pos] = 1
                syndrome = self.H @ error_vector % 2
                syndrome_key = int(''.join([str(b) for b in syndrome]), 2) #[0,1,0]->2 [1,0,0]-> 4 [0,0,1]-> 1
                if syndrome_key not in syndrome_table:
                    syndrome_table[syndrome_key] = error_vector
                else:
                    syndrome_table[syndrome_key] = None
        return syndrome_table

    def encode(self, message:np.array)->np.array:
        if len(message) != self.k:
            raise ValueError(f"dikkah, dein scheiß vektor hat nicht die passende länge K:{self.k}")
        return message @ self.G % 2


    def decode(self, codeword:np.array)->tuple[np.array, int]:
        syndrome = (self.H @ codeword ) % 2
        syndrome_key = int(''.join([f'{b}' for b in syndrome]),2)
        if syndrome_key == 0: # passt kein Fehler
            return codeword[:self.k]
        error_code = self.S.get(syndrome_key, None)
        if error_code is None:
            print("Wallah krise")
            return None, 0
        #korrigierbarer Fehler:
        corrected = (codeword  + error_code) % 2
        num_errors = int(np.sum(error_code)) #[0100] : 1 -> [1001000] : 2
        final_message = corrected[:self.k]
        return final_message, num_errors




def main():
    # Beispiel P-Matrix (7,4)-Code
    P = [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
    ]

    bc = BlockCode(P, 1)

    # Zufällige Nachricht
    message = np.random.randint(0, 2, bc.k)
    print("Original message:      ", message)

    # Encoding
    codeword = bc.encode(message)
    print("Encoded codeword:      ", codeword)

    # Fehler simulieren (1 Bit flip)
    received = codeword.copy()
    #error_pos = np.random.randint(0, bc.n)
    received[6] ^= 1
    received[3] ^= 1

    print(f"Error at position:     {6},{3}")
    print("Received codeword:     ", received)

    # Decoding
    decoded, num_errors = bc.decode(received)

    print("Decoded message:       ", decoded)
    print("Corrected errors:      ", num_errors)

    # Vergleich
    if decoded is not None:
        print("Decoding successful:   ", np.array_equal(message, decoded))
    else:
        print("Decoding failed (ambiguous syndrome)")

if __name__ == "__main__":
    main()