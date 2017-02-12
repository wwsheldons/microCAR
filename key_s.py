from dd import get_key
from box import get_box
nb = 4  # number of coloumn of State (for AES = 4)
nr = 10  # number of rounds ib ciper cycle (if nb = 4 nr = 10)
nk = 4  # the key length (in 32-bit words)
rcon = [[0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
]

def key_expansion(key):
    key_symbols = key

    if len(key_symbols) < 4 * nk:
        for i in range(4 * nk - len(key_symbols)):
            key_symbols.append(0x01)
    key_schedule = [[] for i in range(4)]
    for r in range(4):
        for c in range(nk):
            key_schedule[r].append(key_symbols[r + 4 * c])
    for col in range(nk, nb * (nr + 1)):  # col - column number
        if col % nk == 0:
            tmp = [key_schedule[row][col - 1] for row in range(1, 4)]
            tmp.append(key_schedule[0][col - 1])
            for j in range(len(tmp)):
                sbox_row = tmp[j] // 0x10
                sbox_col = tmp[j] % 0x10
                #sbox_elem = sbox[16 * sbox_row + sbox_col]
                sbox_elem = get_box(False,16 * sbox_row + sbox_col)
                tmp[j] = sbox_elem
            for row in range(4):
                s = (key_schedule[row][col - 4]) ^ (tmp[row]) ^ (rcon[row][int(col / nk - 1)])
                key_schedule[row].append(s)
        else:
            for row in range(4):
                s = key_schedule[row][col - 4] ^ key_schedule[row][col - 1]
                key_schedule[row].append(s)
    tmp = []
    
    for i in range(4):
        tmp.append(bytes(key_schedule[i]))
    #return bytearray(key_schedule)
    return tmp

for i in range(99):
    print(key_expansion(get_key(i)))
    print(',')
