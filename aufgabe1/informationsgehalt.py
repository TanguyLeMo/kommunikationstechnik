from math import log2
from collections import Counter, OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns

words_length_dict = {}
wordlength_amount_dict:dict = {}
def exercise_one_two():
    num_words_with_7_letters:int = wordlength_amount_dict[7]
    first_index =   log2(num_words_with_7_letters / get_num_words_with_n_at_index("x", 0))
    second_index =  log2(num_words_with_7_letters / get_num_words_with_n_at_index("y", 1))
    third_index =   log2(num_words_with_7_letters / get_num_words_with_n_at_index("l", 2))
    forth_index =   log2(num_words_with_7_letters / get_num_words_with_n_at_index("o", 3))
    fifth_index =   log2(num_words_with_7_letters / get_num_words_with_n_at_index("f", 4))
    sixth_index =   log2(num_words_with_7_letters / get_num_words_with_n_at_index("o", 5))
    seventh_index = log2(num_words_with_7_letters / get_num_words_with_n_at_index("n", 6))

    word_index_information = {"0":first_index, "1":second_index, "2":third_index,"3": forth_index, "4" : fifth_index, "5":sixth_index, "6":seventh_index}

    sns.barplot(x=list(word_index_information.keys()), y=list(word_index_information.values()))
    plt.xlabel("index within the word Xylofon")
    plt.ylabel("Information density")
    plt.title("Information density of having a letter at its exact index in comparison with other words of the same length")
    plt.show()

    print(first_index)
    print(second_index)
    print(third_index)
    print(forth_index)
    print(fifth_index)
    print(sixth_index)
    print(seventh_index)


def exercise_one_one():
    y_axis = []
    x_axis= []
    for current_length in wordlength_amount_dict:
        current_plot_value = log2(rawCollection_size / wordlength_amount_dict[current_length])
        y_axis.append(current_plot_value)
        x_axis.append(current_length)
    sns.lineplot(x=x_axis, y=y_axis)
    plt.xlabel("Word length")
    plt.ylabel("Information Density")
    plt.title("Information Density of a word in relation to its length only")
    plt.show()
def get_num_words_with_n_at_index(char: str, index: int) -> int:
    ret: int = 0
    for current_word in words_length_dict:
        if len(current_word) <= index:
            continue
        if words_length_dict[current_word] != 7:
            continue
        if current_word[index].lower() == char:
            ret += 1
    return ret

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
           
    exercise_one_one()
    exercise_one_two()

    

