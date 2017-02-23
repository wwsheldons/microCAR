
def read_line_from_file(filename):
    nth = 0
    try:
        with open(filename, 'rb') as f:
            line = f.readline()
            while line:
                yield nth,line
                nth = nth +1
                line = f.readline()
            f.close()
            yield None
    except OSError as error:
        print("there is no file. %s" % error)
        return None

def get_key(n,length = 32,filename = 'k.dat'):
    for i,line in enumerate(read_line_from_file(filename)):
        if i == n:
            if line[1][:-2] == b'':
                return b'0'
            tmp = line[1].decode()
            if tmp[-2:] == '\r\n':
                tmp = tmp[:-2]
            k = bytearray(16)
            for i in range(0,len(tmp),2):
                k[i//2] = int(tmp[i:i+2],16)
            return bytes(k)
    return None

def get_(inv,n,fn):

    if inv:
        filename = fn[0]
    else:
        filename = fn[1]

    try:
        with open(filename, 'rb') as f:
            f.seek(n*2)
            a = f.read(2)
            # print('seek step is {} and read raw data is {}'.format(2*n,a))
            return int(a.decode(),16)

    except OSError as error:
        print("Error: can not write to SD card. %s" % error)
        return None

def get_box(inv,n,fn=['inv_sbox.dat','sbox.dat']):
    return get_(inv,n,fn)
def get_lk(inv,n,fn=['l1.dat','l2.dat']):
    if inv == 2:
        inv = 0
    return get_(inv,n,fn)


def _get_key_schedule(n,length = 352,filename = 'ks.dat'):
    for i,line in enumerate(read_line_from_file(filename)):
        if n == i:
            if line[1][:-2] == b'':
                return b'0'
            
            tmp = line[1].decode()
            
            if tmp[-2:] == '\r\n':
                tmp = tmp[:-2]
            
            ks = bytearray(44*4)
            # [0:88] [88:176] [176:264] [264:352]
            for i in range(0,352,2):
                ks[i//2] = int(tmp[i:i+2],16)
            #print(len(ks))
            return (bytes(ks[0:44]),bytes(ks[44:88]),bytes(ks[88:132]),bytes(ks[132:176]))
        
    return b'0'
def get_key_schedule(n,line,row,filename = ['ks.dat']):
    if n > 98:
        print('n must less than 98 and it = {}'.format(n))
        return None
    if line > 3:
        print('n must less than 3 and it = {}'.format(line))
        return None
    if row > 43:
        print('n must less than 43 and it = {}'.format(row))
        return None
    # 354 bytes every lines(include '\r\n') ,and offset is 177(354//2)

    return get_(True,n*177+line*44+row,filename)  


