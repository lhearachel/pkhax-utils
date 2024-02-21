from collections import namedtuple

def sint(i: int, n: int) -> int:
    return i if i < (1 << (n - 1)) else i - (1 << n)

class Label():
    def __init__(self, address: int):
        self.addr = sint(address, 32)
    
    def __str__(self):
        return f'Label(addr={self.addr})'
    
class SignedInt():
    def __init__(self, i: int):
        self.val = sint(i, 32)
    
    def __str__(self):
        return str(self.val)

class LoadedVal():
    def __init__(self, i: int):
        self.val = i        

Command = namedtuple('Command', 'name params')
