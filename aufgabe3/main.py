import numpy as np
from channels import BinarySymmetricChannel, FixedErrorChannel
from block_code import BlockCode
from itertools import combinations
from simulation import simulate_transmission, simulate_many_transmissions
from pprint import pprint
def main():
    # Beispiel P-Matrix (7,4)-Code
    # passt für eine Fehler korrektur
    P1 = [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
    ]
    # Für 2 fehler matrix:
    P2 = [
    [1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 0, 1],
    ]
    #P3 =

    P= P1

    bc = BlockCode(P, 2)
    message = np.random.randint(0, 2, bc.k)
    codeword = bc.encode(message)

    channel = BinarySymmetricChannel(0.3) #FixedErrorChannel(2) # -> num errors
    received = channel(codeword)

    decoded, num_errors = bc.decode(received)
    print("Original message:      ", message)
    print("Encoded codeword:      ", codeword)
    print("Received codeword:     ", received)
    print("Decoded message:       ", decoded)
    print("Corrected errors:      ", num_errors)
    print("Bit errors before:     ", np.sum(codeword != received))
    if decoded is not None:
        print("Decoding successful:   ", np.array_equal(message, decoded))
    else:
        print("Decoding failed")

def scenario_one():

    P1 = [
    [1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 0, 1],
    ]
    block_code = BlockCode(P1, 2)
    channel = BinarySymmetricChannel(0.15)
    dict = simulate_many_transmissions(50, block_code, channel)
    pprint(dict)
#    ret_dict = simulate_transmission(block_code, channel)
    #print(ret_dict)

if __name__ == "__main__":
    #main()
    scenario_one()

    #todo: anschauen und verstehen von block codes, und simulation das bestimmen von corrected codewords
