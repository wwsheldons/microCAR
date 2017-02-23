import GL,pyb

RFID_PORT = pyb.UART(3,9600,timeout=10,read_buf_len=12)

class MicropyRFID(object):
    def __init__(self):
        GL.ic_id = ''
        self.rfid_hw = RFID_PORT
        self.rfid_init()
        

    def rfid_init(self):
        self.rfid_hw.init(9600,timeout=10,read_buf_len=12)
    def get_id(self):
        if self.rfid_hw.any() == 12:
            self.rfid_hw.deinit()
            tmp = self.rfid_hw.read(12)
            GL.debug_print('card data is {}'.format(tmp))
            #print('card data is {}'.format(tmp))
            GL.ic_id = ''.join( [ '{:02X}'.format(x) for x in tmp[7:11] ] ).strip()
            self.rfid_init()
            return 1
        return None
    

