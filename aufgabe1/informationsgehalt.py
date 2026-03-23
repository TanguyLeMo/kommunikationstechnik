from math import log2
from collections import Counter, OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns

def get_num_words_with_n_at_index(char:str, index:str) -> int:
    ret: int = 0
    for current_word in words_length_dict:
        if len(current_word) < index:
            continue
        if not words_length_dict[current_word] == 7:
            continue
        if current_word[index].lower() == char:
            ret = ret + 1
    return ret


words_length_dict = {}
wordlength_amount_dict:dict = {}
if __name__ == "__main__":
    filePath: str = "wortliste.txt"
    with open(filePath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                words_length_dict[line] = len(line)
                wordlength_amount_dict[len(line)] = wordlength_amount_dict.get(len(line),0) + 1
    rawCollection_size: int = len(words_length_dict)
    wordlength_amount_dict = dict(sorted(wordlength_amount_dict.items()))
    print(f"Size of raw Collection: {rawCollection_size}")
    print(f"Number of Words which have exactly 5 letters: {wordlength_amount_dict[5]}")
    print(wordlength_amount_dict)
    y_axis = []
    x_axis= []
    for current_length in wordlength_amount_dict:
        current_plot_value = log2(rawCollection_size / wordlength_amount_dict[current_length])
        y_axis.append(current_plot_value)
        x_axis.append(current_length)
    sns.lineplot(x=x_axis, y=y_axis)
    plt.xlabel("Word length")
    plt.ylabel("Information Density")
    #plt.show()
    first_index =   get_num_words_with_n_at_index("x", 1)
    second_index =  get_num_words_with_n_at_index("y", 2)
    third_index =   get_num_words_with_n_at_index("l", 3)
    forth_index =   get_num_words_with_n_at_index("o", 4)
    fifth_index =   get_num_words_with_n_at_index("f", 5)
    sixth_index =   get_num_words_with_n_at_index("o", 6)
    seventh_index = get_num_words_with_n_at_index("n", 7)

    print(first_index)
    print(second_index)
    print(third_index)
    print(forth_index)
    print(fifth_index)
    print(sixth_index)
    print(seventh_index)


