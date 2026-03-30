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


    def plot_results(self):

        sorted_chars = []
        for char in self.probabilities:
            prob = self.probabilities[char]
            sorted_chars.append((char, prob))

        sorted_chars.sort(key=self.get_probability, reverse=True)

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
    quelle1.print_results()

    with open("rfc2324.txt", "r", encoding="utf-8") as file:
        text = file.read()
    cleaned_text = ""
    for char in text:
        if char.isprintable() and char not in ("\n", " "):
            cleaned_text += char
    quelle2 = Nachrichtenquelle(cleaned_text)
    quelle2.plot_results()

