import numpy as np
from channelss import BinarySymmetricChannel, FixedErrorChannel
from block_code import BlockCode
from itertools import combinations
from simulation import simulate_transmission, simulate_many_transmissions
from pprint import pprint
from collections import Counter
import matplotlib.pyplot as plt

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
    bc = BlockCode(P2, 2)
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
    P2 = [
    [1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 0, 1],
    ]
    block_code = BlockCode(P2, 1)
    channel = BinarySymmetricChannel(0.05)
    dict = simulate_many_transmissions(50, block_code, channel)
    x_axis_one = ["Anteil fehlerfrei übertragene Nachricht", "anteil korrigierter Nachrichten", "anteil fehlerbehafteter aber nicht korrigierter Nachrichten"]
    values_one =[dict["error_free_count"],dict["corrected_count"], dict["faulty_not_corrected_count"]]
    plt.bar(x_axis_one, values_one)
    plt.title("Grafik 1")
    plt.show()

    x_axis_two = ["Anteil Fehlerfrei Übertragenen Nachrichten", "Anteil erfolgreich korrigierte Nachrichten", "Anteil fehlerbehafteter aber nicht korrigierter nachrichten"]
    values_two = [dict["error_free_ratio"], dict["corrected_ratio"], dict["faulty_not_corrected_ratio"]]
    plt.bar(x_axis_two, values_two)
    plt.title("Grafik 2")
    plt.show()

    x_axis_three = ["Verteilung der Anzahl Bitfehler vor der Korrektur", "Verteilung der Anzahl korrigierter Bits",  "Verteilung der Anzahl Bitfehler nach der Korrektur"]
    before:Counter = dict["bit_errors_before_counter"]
    corrected:Counter = dict["corrected_bits_counter"]
    after:Counter =  dict["bit_errors_after_counter"] 

    max_x = max(max(before.keys(), default= 0),max(corrected.keys(),default=0),max(after.keys(),default=0))

    x = np.arange(max_x + 1)
    before_values = [before[i]for i in x]
    corrected_values = [corrected[i] for i in x]
    after_values = [after[i] for i in x]
    width=0.25
    plt.bar(x - width, before_values, width, label="anzahl bitfehler vor Korrektur")
    plt.bar(x, corrected_values, width, label="anzahl korrigierte Bits")
    plt.bar(x + width, after_values, width, label = "bitfehler nach korrektur")
    plt.xticks(x)
    plt.title("Grafik 3")
    plt.xlabel("Anzahl Bit")
    plt.ylabel("Anzahl Nachrichten")
    plt.legend()
    plt.show()


def scenario_two():
    P2 = [
    [1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 0, 1],
    ]
    block_code = BlockCode(P2, 2)
    channel = BinarySymmetricChannel(0.15)
    dict = simulate_many_transmissions(50, block_code, channel)
    x_axis_one = ["Anteil fehlerfrei übertragene Nachricht", "anteil korrigierter Nachrichten", "anteil fehlerbehafteter aber nicht korrigierter Nachrichten"]
    values_one =[dict["error_free_count"],dict["corrected_count"], dict["faulty_not_corrected_count"]]
    plt.bar(x_axis_one, values_one)
    plt.title("Grafik 1")
    plt.show()

    x_axis_two = ["Anteil Fehlerfrei Übertragenen Nachrichten", "Anteil erfolgreich korrigierte Nachrichten", "Anteil fehlerbehafteter aber nicht korrigierter nachrichten"]
    values_two = [dict["error_free_ratio"], dict["corrected_ratio"], dict["faulty_not_corrected_ratio"]]
    plt.bar(x_axis_two, values_two)
    plt.title("Grafik 2")
    plt.show()
    before:Counter = dict["bit_errors_before_counter"]
    corrected:Counter = dict["corrected_bits_counter"]
    after:Counter =  dict["bit_errors_after_counter"] 

    max_x = max(max(before.keys(), default= 0),max(corrected.keys(),default=0),max(after.keys(),default=0))

    x = np.arange(max_x + 1)
    before_values = [before[i]for i in x]
    corrected_values = [corrected[i] for i in x]
    after_values = [after[i] for i in x]
    width=0.25
    plt.bar(x - width, before_values, width, label="anzahl bitfehler vor Korrektur")
    plt.bar(x, corrected_values, width, label="anzahl korrigierte Bits")
    plt.bar(x + width, after_values, width, label = "bitfehler nach korrektur")
    plt.xticks(x)
    plt.title("Grafik 3")
    plt.xlabel("Anzahl Bit")
    plt.ylabel("Anzahl Nachrichten")
    plt.legend()
    plt.show()

def scenario_three():
    HC74 = [
            [1,1,0],
            [1,0,1],
            [1,1,1],
            [1,0,1]
            ]
    
    HC114 = [
            [1,1,1,1,0,0,0],
            [0,0,1,1,1,1,0],
            [1,0,1,0,1,0,1],
            [0,1,0,1,0,1,1]
            ]
    
    bc_HC74 = BlockCode(HC74, 1)
    bc_HC114 = BlockCode(HC114, 2)
    bitfeher_prob = [0.001, 0.005, 0.01, 0.02, 0.5, 0.1, 0.15, 0.2]
    bitfeher_prob_string = [str(bitfehler_float) for bitfehler_float in bitfeher_prob]
    rest_HC74 = []
    rest_HC114 = []


    for probabilty in bitfeher_prob:
        channel = BinarySymmetricChannel(0.12)
        simulations_stat_HC74 = simulate_many_transmissions(1000, bc_HC74, channel)
        simulations_stat_HC114 = simulate_many_transmissions(1000, bc_HC114, channel)
        rest_fehler_wahrscheinlichkeit_HC74 = (simulations_stat_HC74["faulty_not_corrected_count"] + simulations_stat_HC74["wrongly_corrected_count"] ) / simulations_stat_HC74["N"]
        rest_fehler_wahrscheinlichkeit_HC114 = (simulations_stat_HC114["faulty_not_corrected_count"] + simulations_stat_HC114["wrongly_corrected_count"] ) / simulations_stat_HC114["N"]
        rest_HC74.append(rest_fehler_wahrscheinlichkeit_HC74)
        rest_HC114.append(rest_fehler_wahrscheinlichkeit_HC114)

    x = np.arange(len(bitfeher_prob))
    width = 0.35
    plt.bar(x - width / 2,
            rest_HC74, 
            width,
            label="(7,4) hamming"
            )
    plt.bar(x + width / 2, 
            rest_HC114,
            width,
            label="(11,4) hamming"
            )
    plt.xticks(x, bitfeher_prob_string)
    plt.xlabel("Bitfehlerwahrscheinlichkeit")
    plt.ylabel("Restwahrscheinlichkeit")
    plt.legend()
    plt.show()    

if __name__ == "__main__":
    #main()
    #scenario_one()
    scenario_two()
    #scenario_three()

    #todo: anschauen und verstehen von block codes, und simulation das bestimmen von corrected codewords
