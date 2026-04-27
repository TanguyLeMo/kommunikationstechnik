import math


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






if __name__ == "__main__":
    message = "FISCHERSFRITZFISCHTFRISCHEFISCHE"

    #vorkommenden Zeichen
    charL = set(message)

    lzw = LempelZivWelch()

    bitstring = lzw.encode(message, charL)
    decoded = lzw.decode(bitstring, charL)

    print("Nachricht:       ", message)
    print("Start-Wörterbuch:  ", charL)
    print("Bitstring:       ", bitstring)
    print("Decodiert:       ", decoded)