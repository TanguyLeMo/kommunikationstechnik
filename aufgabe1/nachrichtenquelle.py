from math import log2
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import seaborn as sns
from shannon_Fano import ShannonFano
from huffmann import Huffman
#import shannon_fano as shannon_fano

class Nachrichtenquelle:
    def __init__(self, wort: str):
        self.wort = wort.lower()
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


    quelle2 = Nachrichtenquelle("hochschule")
    encoder = Huffman(quelle2)
    encoding = encoder.encoding()
    encoded_string, avg_char_length, redundency = encoder.encode("hhhh")
    print(f"average char length: {avg_char_length}")
    print(f"redundency:{redundency}")
    #print("encoded: " + encoded_string)
    
    decoded_string = encoder.decode(encoded_string)
    print(f"encoded length: {len(encoded_string)}")
    print(f"decoded length: {len(decoded_string)}")




