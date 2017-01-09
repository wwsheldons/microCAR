from box import get_box
nb = 4  # number of coloumn of State (for AES = 4)
nr = 10  # number of rounds ib ciper cycle (if nb = 4 nr = 10)
nk = 4  # the key length (in 32-bit words)

hex_symbols_to_int = {'a': 10, 'b': 11, 'c': 12, 'd': 13, 'e': 14, 'f': 15}



rcon = [[0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
]


def _encrypt(input_bytes, key):
    state = [[] for j in range(4)]
    for r in range(4):
        for c in range(nb):
            state[r].append(input_bytes[r + 4 * c])

    key_schedule = key_expansion(key)
    state = add_round_key(state, key_schedule)

    for rnd in range(1, nr):
        state = sub_bytes(state)
        state = shift_rows(state)
        state = mix_columns(state)
        state = add_round_key(state, key_schedule, rnd)

    state = sub_bytes(state)
    state = shift_rows(state)
    state = add_round_key(state, key_schedule, rnd + 1)

    output = [None for i in range(4 * nb)]
    for r in range(4):
        for c in range(nb):
            output[r + 4 * c] = state[r][c]

    return output


def _decrypt(cipher, key):
    state = [[] for i in range(nb)]
    for r in range(4):
        for c in range(nb):
            state[r].append(cipher[r + 4 * c])

    key_schedule = key_expansion(key)

    state = add_round_key(state, key_schedule, nr)

    rnd = nr - 1
    while rnd >= 1:
        state = shift_rows(state, inv=True)
        state = sub_bytes(state, inv=True)
        state = add_round_key(state, key_schedule, rnd)
        state = mix_columns(state, inv=True)

        rnd -= 1

    state = shift_rows(state, inv=True)
    state = sub_bytes(state, inv=True)
    state = add_round_key(state, key_schedule, rnd)

    output = [None for i in range(4 * nb)]
    for r in range(4):
        for c in range(nb):
            output[r + 4 * c] = state[r][c]

    return output


def sub_bytes(state, inv=False):
    '''
    if inv == False:  # encrypt
        box = sbox
    else:  # decrypt
        box = inv_sbox
    '''
    for i in range(len(state)):
        for j in range(len(state[i])):
            row = state[i][j] // 0x10
            col = state[i][j] % 0x10
            '''
            if inv == False:
                box_elem = sbox[16 * row + col]
            else:
                box_elem = inv_sbox[16 * row + col]

            state[i][j] = box_elem
            '''
            state[i][j] = get_box(inv,16 * row + col)
    return state


def shift_rows(state, inv=False):
    count = 1

    if inv == False:  # encrypting
        for i in range(1, nb):
            state[i] = left_shift(state[i], count)
            count += 1
    else:  # decryptionting
        for i in range(1, nb):
            state[i] = right_shift(state[i], count)
            count += 1

    return state


def mix_columns(state, inv=False):
    for i in range(nb):

        if inv == False:  # encryption
            s0 = mul_by_02(state[0][i]) ^ mul_by_03(state[1][i]) ^ state[2][i] ^ state[3][i]
            s1 = state[0][i] ^ mul_by_02(state[1][i]) ^ mul_by_03(state[2][i]) ^ state[3][i]
            s2 = state[0][i] ^ state[1][i] ^ mul_by_02(state[2][i]) ^ mul_by_03(state[3][i])
            s3 = mul_by_03(state[0][i]) ^ state[1][i] ^ state[2][i] ^ mul_by_02(state[3][i])
        else:  # decryption
            s0 = mul_by_0e(state[0][i]) ^ mul_by_0b(state[1][i]) ^ mul_by_0d(state[2][i]) ^ mul_by_09(state[3][i])
            s1 = mul_by_09(state[0][i]) ^ mul_by_0e(state[1][i]) ^ mul_by_0b(state[2][i]) ^ mul_by_0d(state[3][i])
            s2 = mul_by_0d(state[0][i]) ^ mul_by_09(state[1][i]) ^ mul_by_0e(state[2][i]) ^ mul_by_0b(state[3][i])
            s3 = mul_by_0b(state[0][i]) ^ mul_by_0d(state[1][i]) ^ mul_by_09(state[2][i]) ^ mul_by_0e(state[3][i])

        state[0][i] = s0
        state[1][i] = s1
        state[2][i] = s2
        state[3][i] = s3

    return state


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

    return key_schedule


def add_round_key(state, key_schedule, round=0):
    for col in range(nk):
        s0 = state[0][col] ^ key_schedule[0][nb * round + col]
        s1 = state[1][col] ^ key_schedule[1][nb * round + col]
        s2 = state[2][col] ^ key_schedule[2][nb * round + col]
        s3 = state[3][col] ^ key_schedule[3][nb * round + col]

        state[0][col] = s0
        state[1][col] = s1
        state[2][col] = s2
        state[3][col] = s3

    return state
def left_shift(array, count):
    res = array[:]
    for i in range(count):
        temp = res[1:]
        temp.append(res[0])
        res[:] = temp[:]

    return res


def right_shift(array, count):
    res = array[:]
    for i in range(count):
        tmp = res[:-1]
        tmp.insert(0, res[-1])
        res[:] = tmp[:]

    return res


def mul_by_02(num):
    if num < 0x80:
        res = (num << 1)
    else:
        res = (num << 1) ^ 0x1b

    return res % 0x100


def mul_by_03(num):
    return (mul_by_02(num) ^ num)


def mul_by_09(num):
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ num


def mul_by_0b(num):
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(num) ^ num


def mul_by_0d(num):
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(mul_by_02(num)) ^ num


def mul_by_0e(num):
    return mul_by_02(mul_by_02(mul_by_02(num))) ^ mul_by_02(mul_by_02(num)) ^ mul_by_02(num)

def encrypt(input_bytes, key):
    '''
    if isinstance(input_bytes,bytes) or isinstance(input_bytes,bytearray):
        input_bytes = [i for i in input_bytes]
    '''
    n,nod = divmod(len(input_bytes),16)
    output = []
    orig_len = len(input_bytes)
    if nod != 0:
        #input_bytes = input_bytes+[0]*(16-nod)
        input_bytes = input_bytes+b'x00'*(16-nod)
        n = n+1    
    for i in range(n):
        tmp = input_bytes[i*16:i*16+16]
        output.extend(_encrypt(tmp, key))
    #return output,orig_len
    return output

def decrypt(cipher, key,orig_len=0):
    n = int(len(cipher)/16)
    output = []
    for i in range(n):
        tmp = cipher[i*16:i*16+16]
        output.extend(_decrypt(tmp, key))
    if orig_len == 0:
        return output
    else:
        return output[0:orig_len]
'''
d = b'100213592683721!!!!00000000216-06-0320:08:0023447.9072111335.68360123000000.00001111*****'
dat = b"\xe2rEzE\xaa\xa9p\xc1\xa1\x86\xcb\xba)\xac8\xc1\x95\x06\xd3\xaa0v\x82\x1f\x04\x05p\xc5\xfd\x84@\x84\xd9\r\x0b\xf5\xad\xbd\x16\n'\xdb\x8b>5+\xc2oh\x93v\xe7\xb7bH\x92\xb1\xf1*\xd2i\xb4\xa4\xb0\x16NWP?\x85M\x06P\x8dL3s\x8f\xc6/8\xda\xf5\x9fO\xe9\t\xd3vq\x91C\xb2\xf8\x1a"
key = b'8\xf2\x92\xb9\xc2\xc9\x0e\x7f\xafe\xb8\xa4Zc\x84\xd9'
#d_en = encrypt([i for i in d],[i for i in key])
d_en = encrypt([i for i in d],key)
print(bytes(d_en))
d_de = decrypt(d_en,key,len(d))
print(bytes(d_de))
'''