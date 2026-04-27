import time
from math import log2, ceil
class Lempel_Ziv:
    def __init__(self,num_bit_Left, num_bit_right):
        self.char_set: set = set()
        self.num_bits_for_encoding = 0
        self.encoding_dict = {}
        self.leftnumbits = num_bit_Left
        self.rightnumbits = num_bit_right
        self.tupleSize = num_bit_right + num_bit_Left
        #0011110

    #shall be called with bitstring, charD = lempelZiv.encode(message)

    #10ß11001 10010
    def encode(self, message:str) -> tuple[str, str]:
        self.set_char_set(message)
        counter = 0
        self.encoding_dict = {}
        for index, char in enumerate(self.char_set):
            if char not in self.encoding_dict:
                self.encoding_dict[char] = f"{index:0{self.num_bits_for_encoding}b}"
                counter += 1
        current_index = 0
        ret_word = ""

        max_offset = 2 ** self.leftnumbits -1
        max_length = 2 ** self.rightnumbits -1

        while current_index < len(message):
            loop_index = current_index
            left_boundary_index = max(0, current_index - max_offset)
            message_window = message[left_boundary_index:loop_index]

            offset = 0
            length = 0
            next_char = ""

            while length < max_length and loop_index < len(message) -1:
                next_word = message[loop_index:loop_index + length + 1]
                current_pos = message_window.rfind(next_word)
                if current_pos == -1 :
                    break
                offset = loop_index - (left_boundary_index + current_pos)
                length += 1
            next_char   = message[loop_index + length]
            bin_offset  = f"{offset:0{self.leftnumbits}b}"
            bin_length  = f"{length:0{self.rightnumbits}b}"
            bin_char    = self.encoding_dict[next_char]

            ret_word += bin_offset + bin_length + bin_char
            ret_word_length = len(ret_word)
            if ret_word_length % 17 != 0:
                print("error")
            if len(bin_offset) != 5 or len(bin_length) != 5 or len(bin_char) != 7:
                print(f"adding: {len(bin_offset)}, {len(bin_length)}, {len(bin_char)} ")
            if (len(bin_char) > self.num_bits_for_encoding):
                print(bin_char)
            current_index = current_index + length + 1
        print(len(ret_word))
        return ret_word, self.encoding_dict
        """

            if len(current_word) > 0: #match gefunden
                offset = current_index - (left_boundary_index + message_window.rfind(current_word))
                length = len(current_word)
                if current_index >= len(message):
                    next_char = message[-1]
                else:
                    next_char = message[current_index + 1]
            else:
                offset = 0
                length = 0
                if current_index > len(message):
                    next_char = message[-1]
                else:
                    next_char = message[current_index + 1]
            current_word = ""
            current_index += 1



            longest_occurence = message[current_index]
            longest_occurence_index = message[left_boundary_index:current_index].find(longest_occurence)
            while longest_occurence_index > -1:
                longest_occurence_index_tmp = message[left_boundary_index:current_index].find(longest_occurence + message[current_index + 1])
                if longest_occurence_index_tmp == -1:
                    break
                else:
                    longest_occurence = message[longest_occurence_index + left_boundary_index : longest_occurence_index + len(longest_occurence) + 1]
                    longest_occurence_index = longest_occurence_index_tmp
            current_word += message[current_index]
            index_of_word = message[left_boundary_index:current_index].find(current_word)
            if index_of_word > -1:
                index_of_word += left_boundary_index # set index to whole word instead of the windows
            if len(current_word) > 2 ** self.rightnumbits:
                print("wort zu lang zum codieren")
                print("ganzes Wort wird jetzt binör reingehauen")
                for character in current_word:
                    binary_str_left  = f"{0:0{self.leftnumbits}b}"                 #f{i:0{n}b}  #format(index_of_word, 'b')
                    binary_str_right = f"{0:0{self.rightnumbits}b}"
                    ret_word += binary_str_left + binary_str_right + self.encoding_dict[character]
                    current_word = ""
            elif (current_index - len(index_of_word)) > (2** self.leftnumbits - 1):
                print("wort zu weit weg zum zurückspringen")
                print("dieser state sollte eigentlich niemals erreicht sein")
            offset = (current_index - index_of_word)
            binary_str_left  = f"{offset:0{self.leftnumbits}b}"                 #f{i:0{n}b}  #format(index_of_word, 'b')
            binary_str_right = f"{len(current_word):0{self.rightnumbits}b}"            # format(len(current_word), 'b')
            if current_index + 1  >= len(message):
                return ret_word + self.word_into_binary(current_word) + self.encoding_dict[message[current_index]]
            ret_word += binary_str_left + binary_str_right + self.encoding_dict[message[(current_index)]]
            current_index +=1
        """
    def word_into_binary(self, word:str) -> str:
        ret = ""
        for current_char in word:
            ret += self.encoding_dict[current_char]
        return ret


    def decode(self, bit_string:str, charD:dict):
        tuple_size = self.leftnumbits + self.rightnumbits + self.num_bits_for_encoding
        reversed_dict = {v:k for k,v in charD.items()}
        if len(bit_string) % tuple_size != 0:
            print("villager mmhh sound")
            print("bitsstringlen:" + str(len(bit_string)))
            print("tuple: " + str(tuple_size))
            print(len(bit_string) % tuple_size)
            return "villager mmhh sound"
        ret_word = ""
        for index in range(0, len(bit_string), tuple_size):
            current_tuple = bit_string[index:index + tuple_size]
            offset_bin = current_tuple[:self.leftnumbits]
            length_bin = current_tuple[self.leftnumbits:self.leftnumbits + self.rightnumbits]
            last_char = reversed_dict[current_tuple[self.rightnumbits+ self.rightnumbits:]]

            offset = int(offset_bin,2)
            length = int(length_bin, 2)
            if offset == 0 and length == 0:
                ret_word += last_char
            else:
                ret_word += ret_word[len(ret_word) - offset:len(ret_word) - offset + length] + last_char
        return ret_word


    def set_char_set(self, message):
        for character in message:
            if character not in self.char_set:
                self.char_set.add(character)
        self.num_bits_for_encoding = ceil(log2(len(self.char_set)))

if __name__ == "__main__":
    zivelMann = Lempel_Ziv(5,5)
    with open("rfc2324.txt", "r", encoding="utf-8") as file:
        text = file.read()
    message, dic = zivelMann.encode(text)
    #print(message)
    print(zivelMann.decode(message, dic))
