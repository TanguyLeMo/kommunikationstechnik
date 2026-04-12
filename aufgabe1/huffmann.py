import heapq

class Huffman:
    def __init__(self, nachrichtenquelle):
        self.source = nachrichtenquelle
        self.root = None
        self.counter = 0
        self.heap =[]
        self.codes = {}
        
        for char, count in self.source.get_sorted_list():
            current_node = Node(char, count)
            self.heap.append((count, self.counter, current_node))
            self.counter += 1
        heapq.heapify(self.heap)
        

    def encode(self, word:str):
        if not self.codes : 
            print("hund")
            return "hund"
        ret:str = ""
        if len(word) == 0:
            return
        for char in word:
            if not char in self.codes:
                ret = "unvalid key: " + str(char)
                break
            ret += self.codes[char]
        avg_char_length = len(ret) / len(word)
        redundency = avg_char_length - self.source.entropy

        return ret, avg_char_length, redundency

    def encoding(self):
        self._build_tree()
        if self.root:
            self._build_codes(self.root, "")


    def decode(self, word:str):
        ret = ""
        current_word = ""
        inversed_map = {v: k for k, v in self.codes.items()}
        for bit in word:
            current_word += bit
            if current_word in inversed_map:
                ret += inversed_map[current_word]
                
                current_word = ""
        return ret



    def _build_tree(self):
        while len(self.heap) > 1:
            first_weight, _, first_Node = heapq.heappop(self.heap)
            seconds_weight, _, seconds_Node = heapq.heappop(self.heap)
            merged = Node(
                char=None,
                weight=(first_weight+seconds_weight),
                left=first_Node,
                right=seconds_Node  
            )
            heapq.heappush(self.heap, (merged.weight, self.counter, merged))
            self.counter += 1
        _, _, self.root = heapq.heappop(self.heap)
        

    def _build_codes(self, node, prefix):
        if node.char is not None:
            self.codes[node.char] = prefix
            return
        if node.left:
            self._build_codes(node.left, prefix + "0" )
        if node.right:
            self._build_codes(node.right, prefix + "1")
        

class Node:
    def __init__(self, char, weight, left=None, right=None):
        self.char = char
        self.weight = weight
        self.left = left
        self.right = right

        
