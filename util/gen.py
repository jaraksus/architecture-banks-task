import numpy as np

class TNoRepetitionGenerator(object):
    def __init__(self):
        self.chars = [
            'a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F',
            'g', 'G', 'h', 'H', 'i', 'I', 'j', 'J', 'k', 'K', 'l', 'L',
            'm', 'M', 'n', 'N', 'o', 'O', 'p', 'P', 'q', 'Q', 'r', 'R',
            's', 'S', 't', 't', 'T', 'u', 'U', 'v', 'V', 'w', 'W', 'x',
            'X', 'y', 'Y', 'z', 'Z', '1', '2', '3' , '4', '5', '6', '7',
            '8', '9'
        ]

        self.was = set()
    
    def gen(self, len: int):
        while True:
            seq = ''.join(np.random.choice(self.chars, size=len, replace=True))
            if not seq in self.was:
                break

        self.was.add(seq)
        return seq

    def free(self, seq):
        if seq in self.was:
            self.was.remove(seq)
