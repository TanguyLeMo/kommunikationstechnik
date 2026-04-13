import random
from math import log2
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')


import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
from arithmetic_compressor import AECompressor
from arithmetic_compressor.models import StaticModel

from shannon_fano import shannon_fano
#from shannon_Fano import ShannonFano
from huffmann import Huffman
#import shannon_fano as shannon_fano

class Nachrichtenquelle:
    def __init__(self, wort: str):
        self.wort = wort
        self.length = len(self.wort)
        self.char_counts = Counter(self.wort)

        self.probabilities = {}
        self.information_content = {}
        self.entropy = 0
        self.shannon_fano_codes = {}
        for char, count in self.char_counts.items():
            self.probabilities[char] = count / self.length

        for char, prob in self.probabilities.items():
            self.information_content[char] = -log2(prob)

        for char in self.probabilities:
            p = self.probabilities[char]
            i = self.information_content[char]
            self.entropy += p * i


    def get_sorted_list(self) -> list[tuple[str, int]]:
        return sorted(
        self.char_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    def print_results(self):
        print(f"Wort: {self.wort}")
        print("\nZeichenhäufigkeiten:")
        for char, count in self.char_counts.items():
            print(f"{char}: {count}")

        print("\nWahrscheinlichkeiten:")
        for char, prob in self.probabilities.items():
            print(f"{char}: {prob:.4f}")

        print("\nInformationsgehalt:")
        for char, info in self.information_content.items():
            print(f"{char}: {info:.4f}")

        print(f"\nEntropie der Quelle: {self.entropy:.4f}")

    def get_probability(self,tupel):
        return tupel[1]

    def get_sorted_prob_list(self, reverseList:bool) -> list[tuple[str, float]] :
        return sorted(
        [(char, prob) for char, prob in self.probabilities.items()],
        key=self.get_probability,
        reverse=reverseList
        )


    def plot_results(self):
        sorted_chars = self.get_sorted_prob_list(True)
        chars = []
        probs = []
        infos = []

        for element in sorted_chars:
            char = element[0]
            prob = element[1]
            info = self.information_content[char]

            chars.append(char)
            probs.append(prob)
            infos.append(info)

        plt.figure()
        sns.barplot(x=chars, y=probs)
        plt.xlabel("Zeichen")
        plt.ylabel("Häufigkeit (Wahrscheinlichkeit)")
        plt.title("Zeichenhäufigkeit")

        plt.figure()
        sns.barplot(x=chars, y=infos)
        plt.xlabel("Zeichen")
        plt.ylabel("Informationsgehalt")
        plt.title("Informationsgehalt der Zeichen")

        plt.show()

if __name__ == "__main__":
    test_wort = "Hochschule"
    quelle1 = Nachrichtenquelle(test_wort)
    #quelle1.print_results()

    with open("rfc2324.txt", "r", encoding="utf-8") as file:
        text = file.read()


    quelle2 = Nachrichtenquelle(text)
    encoder_shannon_fano = shannon_fano(quelle2)
    encoding = encoder_shannon_fano.encoding()

    sorted_list = quelle2.get_sorted_prob_list(True)

    chars = [char for char, _ in sorted_list]
    probs = [prob for _, prob in sorted_list]
    rand_char_list = random.choices(chars, weights=probs, k=100000)


    rand_char_word = "".join(rand_char_list)
    print(rand_char_word)

    encoded_string, avg_char_length, redundency = encoder_shannon_fano.encode(rand_char_word)
    print(f"average char length shannon_fano: {avg_char_length}")
    print(f"redundency shannon_fano:{redundency}")
    #print("encoded: " + encoded_string)
    encoder_huffmann = Huffman(quelle2)
    encoder_huffmann.encoding()
    encoder_string_huffmann, avg_char_length_huffmann, redundency_huffmann = encoder_huffmann.encode(rand_char_word)
    print(f"average char length huffmann: {avg_char_length_huffmann}")
    print(f"redundency huffmann: {redundency_huffmann}")

    decoded_string = encoder_shannon_fano.decode(encoded_string)
    #print(f"encoded length: {len(encoded_string)}")
    #print(f"decoded length: {len(decoded_string)}")
    model_aka_Hannes_bummele = StaticModel(dict(quelle2.get_sorted_prob_list(True)))
    coder = AECompressor(model_aka_Hannes_bummele)
    data = "iiiiiiiiieeeeeeeeeeeee"
    compressed_arithmetic_data = coder.compress(rand_char_word)

    #avg_char_length = len(ret) / len(word)
    #redundency = avg_char_length - self.source.entropy
    arithmetic_avg_char_legnth = len(compressed_arithmetic_data) / len(rand_char_word)
    artihemitc_redundency = avg_char_length - quelle2.entropy

    print(f"Arithmetic avg char length: {arithmetic_avg_char_legnth}")
    print(f"Arithmetic redundency {artihemitc_redundency}")


    data = {
    "Method": ["Shannon-Fano", "Huffman", "Arithmetic"],
    "Avg Char Length": [
        avg_char_length,
        avg_char_length_huffmann,
        arithmetic_avg_char_legnth
        ]
    }

    df = pd.DataFrame(data)

    plt.figure()

    sns.barplot(data=df, x="Method", y="Avg Char Length")

    plt.title("Average Encoding Length Comparison")
    plt.ylabel("Average Length per Character")
    plt.xlabel("Encoding Method")

    plt.ylim([4.5, 4.8])
    plt.show()