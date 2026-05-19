import math
from lempel_ziv import Lempel_Ziv

class LempelZivWelch:
    def encode(self, message, charL):
        dictionary = {char: i for i, char in enumerate(charL)}
        next_code = len(dictionary)

        w = ""
        codes = []

        for c in message:
            wc = w + c

            if wc in dictionary:
                w = wc
            else:
                codes.append(dictionary[w])
                dictionary[wc] = next_code
                next_code += 1
                w = c

        if w:
            codes.append(dictionary[w])

        #bits pro code berechnen
        bit_length = max(1, math.ceil(math.log2(max(codes) + 1)))

        bitstring = f"{bit_length:08b}"
        for code in codes:
            bitstring += f"{code:0{bit_length}b}"

        return bitstring

    def decode(self, bitstring, charL):
        if not bitstring:
            return ""

        bit_length = int(bitstring[:8], 2)
        data = bitstring[8:]

        codes = []
        for i in range(0, len(data), bit_length):
            codes.append(int(data[i:i + bit_length], 2))

        dictionary = {i: char for i, char in enumerate(charL)}
        next_code = len(dictionary)

        w = dictionary[codes[0]]
        message = w

        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == next_code:
                entry = w + w[0]
            else:
                raise ValueError("Ungültiger LZW-Code")

            message += entry

            dictionary[next_code] = w + entry[0]
            next_code += 1

            w = entry

        return message


def find_best_lz_params(text, max_left=15, max_right=15, verbose=False):
    best_len = float("inf")
    best_params = None
    results = []

    for left_bits in range(1, max_left + 1):
        for right_bits in range(1, max_right + 1):
            try:
                zivelMann = Lempel_Ziv(left_bits, right_bits)
                encoded_message, dic = zivelMann.encode(text)

                current_len = len(encoded_message)
                results.append((left_bits, right_bits, current_len))

                if current_len < best_len:
                    best_len = current_len
                    best_params = (left_bits, right_bits)

                if verbose:
                    print(f"left={left_bits}, right={right_bits} -> {current_len}")

            except Exception:
                # skip invalid combinations
                continue

    # sort results (best first)
    results.sort(key=lambda x: x[2])

    return best_params, best_len, results



if __name__ == "__main__":
    #with open("C:\repos\kommunikationstechnik\aufgabe2\rfc2324.txt", "r", encoding="utf-8") as file:
       # text = file.read()
    message = "FISCHERSFRITZFISCHTFRISCHEFISCHE"

    #vorkommenden Zeichen
    charL = set(message)
    lzw = LempelZivWelch()
    zivelMann = Lempel_Ziv(15,5)

    wels_bitstring = lzw.encode(message, charL)
    message, dic = zivelMann.encode(text)
    wels_decoded = lzw.decode(wels_bitstring, charL)
    decoded = zivelMann.decode(message, dic)
    print(decoded)

    print("länge vom text:                   " + str(len(text)))
    print(f"Länge ohne Wels:                     {len(message)}")
    print("Bitstringlänge mit dem Wels:       ", len(wels_bitstring))


    #print(message)
    #print(zivelMann.decode(message, dic))

    print(message)
    best_params, best_len, results = find_best_lz_params(text, 15, 15)
    print("ki optimum: ")
    print(f"best_param{best_params}")
    print(f"best_len{best_len}")
    print(f"result{results}")
    print(len(decoded))
    print(len(text))
    print(decoded == text)
    #print("Nachricht:       ", message)
    #print("Start-Wörterbuch:  ", charL)
    #print("Decodiert:       ", decoded)