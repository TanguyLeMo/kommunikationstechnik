import Nachrichtenquelle
class shannon_fano:
    def __init__(self, narichtenquelle: Nachrichtenquelle):
        self.source:Nachrichtenquelle = narichtenquelle
        self.symbol_list = []
        for char, count in self.source.get_sorted_list():
            self.symbol_list.append([char, count, ""])
        self.codes = {}

    def _recursive(self, symbol_list: list[list]):
        # wenn am blatt, return
        if len(symbol_list) <= 1:
            return
        #add total probability of (sub) Branch
        total = 0
        for entry in symbol_list:
            total += entry[1]

        running_sum = 0
        index = 0
        half = total / 2
        #find the index of which approximates best the half of probability sum
        for i in range(len(symbol_list)):
            previous_sum = running_sum
            running_sum += symbol_list[i][1]

            if running_sum >= half:
                if abs(previous_sum - half) <= abs(running_sum - half):
                    index = i
                else:
                    index = i + 1
                break
            if running_sum >= half:
                index = i + 1
                break
        
        #divide both halfs
        left = symbol_list[:index]
        right = symbol_list[index:]
        # append encoding value
        for item in left:
            item[2] += "0"
        for item in right:
            item[2] += "1"
        
        self._recursive(left)
        self._recursive(right)
    def encoding(self):
        self._recursive(self.symbol_list)
        self.codes = {}
        for char, prob, code in self.symbol_list:
            self.codes[char] = code
        return self.codes
    
    def encode(self, word: str)-> str:
        ret:str = ""
        for char in word:
            if not char in self.codes:
                ret = "unvalid key: " + str(char)
                break
            ret += self.codes[char]
        return ret
    
    def decode(self, encoded: str) -> str:
        ret = ""
        current_index = 0
        current_word = ""
        inversed_map = {v: k for k, v in self.codes.items()}
        for bit in encoded:
            current_word += bit
            print()
            if current_word in inversed_map:
                ret += inversed_map[current_word]
                print(ret)
                current_word = ""
        return ret

    def __str__(self):
        ret = ""
        for char, prob, code in self.symbol_list:
            ret += f"char:{char}\tprob:{prob}\tcode:{code}\n"
        return ret


def main():
    print("hello there")

if __name__=="__main__":
    main()
