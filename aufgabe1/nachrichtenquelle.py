from math import log2
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import seaborn as sns

class Nachrichtenquelle:
    def __init__(self, wort: str):
        self.wort = wort.lower()
        self.length = len(self.wort)
        self.char_counts = Counter(self.wort)

        self.probabilities = {}
        for char, count in self.char_counts.items():
            self.probabilities[char] = count / self.length

        self.information_content = {}
        for char, prob in self.probabilities.items():
            self.information_content[char] = -log2(prob)

        self.entropy = 0
        for char in self.probabilities:
            p = self.probabilities[char]
            i = self.information_content[char]
            self.entropy += p * i


    def get_sorted_list(self) -> list[tuple[chr, int]]:
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


def shannon_fano(symbol_list):
    if len(symbol_list) <= 1:
        return
    total = 0
    for entry in symbol_list:
        total += entry[1]

    sum = 0

    index = 0
    for i in range(len(symbol_list)):
        sum += symbol_list[i][1]
        if sum >= total / 2:
            index = i + 1
            break

    left = symbol_list[:index]
    right = symbol_list[index:]

    for item in left:
        item[2] += "0"
    for item in right:
        item[2] += "1"

    shannon_fano(left)
    shannon_fano(right)


if __name__ == "__main__":
    test_wort = "Hochschule"
    quelle1 = Nachrichtenquelle(test_wort)
    quelle1.print_results()

    with open("rfc2324.txt", "r", encoding="utf-8") as file:
        text = file.read()
    quelle2 = Nachrichtenquelle(text)

    #Test mit Stuff aus Vorlesung
    quelle3 = Nachrichtenquelle("HOCHSCHULE")
    prob_list = quelle3.get_sorted_prob_list(True)

    symbol_list = []
    for char, prob in prob_list:
        symbol_list.append([char, prob, ""])

    shannon_fano(symbol_list)
    print(symbol_list)



