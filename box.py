
def get_box(inv,n):
    if inv:
        filename = 'inv_sbox.dat'
    else:
        filename = 'sbox.dat'
    try:
        with open(filename, 'rb') as f:
            f.seek(n*2)
            a = f.read(2)
            #print(a)
            return int(a.decode(),16)

    except OSError as error:
        print("Error: can not write to SD card. %s" % error)
        return None

