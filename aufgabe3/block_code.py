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



    def encode(self, message:str)->str:
        return ""
    
    def decode(self, codeword:str)->tuple[str, int]:
        return ("",0)