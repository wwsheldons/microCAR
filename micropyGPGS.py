#modify by wjy @20170106
from math import floor
from aes128 import encrypt,decrypt
from dd import get_key
import struct
# Import pyb or time for fix time handling
try:
    # Assume running on pyboard
    import pyb
except ImportError:
    # Otherwise default to time module for non-embedded implementations
    # Note that this forces the resolution of the fix time 1 second instead
    # of milliseconds as on the pyboard
    import time


crc_table = [0x00000000, 0x77073096, 0xee0e612c, 0x990951ba,
 0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
 0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
 0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
 0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de,
 0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
 0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec,
 0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
 0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
 0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
 0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940,
 0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
 0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116,
 0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
 0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
 0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
 0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a,
 0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
 0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818,
 0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
 0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
 0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
 0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c,
 0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
 0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2,
 0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
 0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
 0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
 0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086,
 0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
 0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4,
 0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
 0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
 0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
 0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8,
 0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
 0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe,
 0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
 0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
 0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
 0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252,
 0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
 0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60,
 0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
 0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
 0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
 0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04,
 0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
 0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a,
 0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
 0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
 0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
 0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e,
 0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
 0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c,
 0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
 0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
 0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
 0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0,
 0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
 0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6,
 0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
 0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
 0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d]


def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'big')

def transferred_meaning(dat):
    if isinstance(dat,list):
        dat = bytes(dat)
    #return [i for i in dat.replace(b'\x7d', b'\x7d\x01').replace(b'\x7e',b'\x7d\x02')]
    return dat.replace(b'\x7d', b'\x7d\x01').replace(b'\x7e',b'\x7d\x02')
def retransferred_meaning(dat):
    if isinstance(dat,list):
        dat = bytes(dat)
    #return [i for i in dat.replace(b'\x7d\x01',b'\x7d').replace(b'\x7d\x02',b'\x7e')]
    return dat.replace(b'\x7d\x01',b'\x7d').replace(b'\x7d\x02',b'\x7e')

def crc32(datas):
    '''
    POY = 0xEDB88320
    crc_table = [0]*256
    for i in range(256):
        cell = i
        for j in range(8):
            if cell & 1:
                cell = (cell >> 1) ^ POY
            else:
                cell >>= 1
        crc_table[i] = cell
    '''
    crc = 0xffffffff
    for c in datas:
        if type(c) == str:
            c = ord(c)
        #crc = (crc >> 8) ^ get_table((crc ^ c) & 0xff)
        crc = (crc >> 8) ^ crc_table[(crc ^ c) & 0xff]
    crc = crc ^ 0xfffffffF
    return struct.pack(">I",crc)  # 4 bytes big

class MicropyGPRS(object):
    """GPRS Sentence Parser. Creates object that stores all relevant GPRS data and statistics.
    Include AT order , SMS and data from server.
    Parses sentences one character at a time using update(). """

    # Max Number of Characters a valid sentence can be (based on module limited)
    SENTENCE_LIMIT = 1000
    #__HEMISPHERES.keys() = ('N', 'S', 'E', 'W')
    __HEMISPHERES = {'N':b'1', 'S':b'2', 'E':b'1', 'W':b'2'}
    __NO_FIX = 1
    __FIX_2D = 2
    __FIX_3D = 3
    FRAME_LEN = {'9000':23,'9010':15,'9007':21,'9008':12,'9009':12,'9004':13+59,'9005':11,
                      '9006':11,'9002':11,'9003':11,'9005':11,'9006':11,'9011':12,'9012':11}
    
    def __init__(self, local_offset=0):
        '''
        Setup GPS Object Status Flags, Internal Data Registers, etc
        '''

        #####################
        # Object Status Flags
        self.sentence_server_active = False
        self.sentence_data_active = False
        self.sentence_at_active = False
        self.active_segment = 0
        self.gprs_segments = [b'']
        self.char_count = 0
        self.fix_time = 0

        self.ats_dict = {}
        #####################
        # buf
        self.tx_buf = b''
        self.id = b'AP9904N0769'
        self.active_order = 0
        self.order_from_server = []
        self.rx_dat = []
        
    ########################################
    # opreate the gprs module
    ########################################
    def send(self,dat):
        if dat[:2] == 'AT':
            return self.send_at(dat)
        elif dat == 0x1a:
            return self.gprs_port.writechar(0x1a)
        else:
            #GL.debug_print('the order will be send is {} and the dat is {}'.format(hex(order)[2:],dat))
            self.send_at('AT+CIPSEND={},1'.format(len(dat)))
            while not self.ats_dict['AT+CIPSEND={},1'.format(len(dat))]:
                pass
            self.send_d(dat)
    def send_at(self,order):
        #self.debug_print('send order is {}'.format(order))
        if self.gprs_port.write('{}\r\n'.format(order)) == len(order)+2:
            self.ats_dict[order] = 0
            return 1
        return 0
    def send_d(self,d):
        if not isinstance(d,bytearray):
            return self.gprs_port.write(bytearray(d))
        if d == 0x1a:
            return self.gprs_port.writechar(0x1a)
        return 0

    ## sms correlation 
    def rec_sms(self,num=1):
        return self.send_at('AT+CMGR={}'.format(num)) # the {num}th sms
    def del_sms(self):
        return self.send_at('AT+CMGD=1,4')#del all the sms
    def send_sms(phone_num,dat = 'hello world!'):
        self.send_at('AT+CMGS=\"+86{}\"'.format(phone_num))
        sleep_us(400)
        self.send_d(dat)#sms contents
        sleep_us(400)
        self.send_d(0x1a)# send
        sleep_us(400)
        self.del_sms()
        sleep_us(400)
    def fac_reset(self):
        return self.send_at('ATZ')
    def check_phone_card(self):
        return self.send_at('AT+CNUM=?')
    def check_csq(self):
        return self.send_at('AT+CSQ')
    ########################################
    # data from server Parsers
    ########################################

    def unpack_server_data(self,dat,opt = 0x01):
        '''
        opt = 0bxxxx xxxx
        the 0th bit: ase128 coding---1    not coding---0
        the 1-7th bit: reserve
        '''
        tmp = dat
        if 0x7d in tmp:
            tmp = retransferred_meaning(tmp)
        if tmp[0] == 126 and tmp[-1] == 126:
            tmp = tmp[1:-1]
            tmp_len_dat = int(tmp[:4].decode())
            tmp_key = get_key(int(tmp[4:6].decode()))
            tmp_frame = tmp[:-4]
            tmp_dat = tmp[6:-4]
            tmpcrc32 = tmp[-4:]
            print()
            if crc32(tmp_frame) == tmpcrc32:
                pass
            else:
                print ('crc32 error')
            length_frame = tmp_len_dat
            key = tmp_key
            #print('tmp_dat ={}'.format(tmp_dat))
            if (opt & 0x01):
                d = bytes(decrypt([i for i in tmp_dat],tmp_key,tmp_len_dat))
            else:
                d = tmp_dat
            '''
            print('d ={}'.format(d))
            print('d[4:4+11] ={}'.format(d[4:4+11]))
            print('self.id = {}'.format(self.id))
            if d[4:4+11] != self.id:
                print('control id is wrong')
                return False
            '''
            order = d[0:4].decode()
            if order not in self.FRAME_LEN.keys():
                print('wrong order from server')
                return False
            print('self.order_from_server = {}'.format(self.order_from_server))
            self.order_from_server.append(order)
            self.active_order += 1
            start = 4+11
            if order in ['9002','9003','9005','9006','9012']:
                self.rx_dat.append('')
            else:
                if order in ['9000','9010','9007','9008','9009']:
                    len_of_frame = self.FRAME_LEN[order]-11
                if order == '9004':
                    n = int(chr(d[4+11+1]))
                    len_of_frame = 13+59*n-11
                if order == '9011':
                    n = d.index(b'y')
                    len_of_frame = n+1
                self.rx_dat.append(d[start:len_of_frame+start])
            
            return True
        else:
            print('the data is not a frame')
            return False
    ########################################
    # Sentence Parsers
    ########################################

    def at(self):
        """Parse at order Include 'AT','ATZ','AT+CMGF=1','AT+CNUM=?','AT+CSQ','AT+CIPCLOSE=0',
        #AT             reply: 'AT\r\n\r\nOK\r\n'                               #test gprs module
        #ATZ            reply: 'ATZ\r\n\r\nOK\r\n'                              #Factory Reset
        #AT+CMGF=1      reply: 'AT+CMGF=1\r\n\r\nOK\r\n'                        #english mode
        #AT+CNUM=?      reply: 'AT+CNUM=?\r\n\r\nOK\r\n'                        #check sim card
        #AT+CSQ         reply: 'AT+CSQ\r\n\r\n+CSQ: 7, 99\r\n\r\nOK\r\n'        #check csq
                               'AT+CSQ\r\n\r\n+CSQ: 11, 99\r\n\r\nOK\r\n'
        #AT+CIPCLOSE=0  reply: 'AT+CIPCLOSE=0\r\n\r\nOK\r\n'  {+CME ERROR: 16}  #close the connect to server

        'AT+CMGR=1','AT+CMGD=1,4','AT+CMGS=phone_num',(read ,del ,send SMS order)
        #'AT+CMGR=1'    reply: 'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n'
        #'AT+CMGD=1,4'  reply: 'AT+CMGD=1,4\r\n\r\nOK\r\n'
        #'AT+CMGS=*'    reply: 'AT+CMGS="+8613592683720"\r\n\r\n> '
        'AT+CSTT="CMNET",'AT+CGATT=1','AT+CIPSTART="TCP","ip",port',(connect to the server)
        #               reply: b'AT+CSTT="CMNET","",""\r\n\r\nOK\r\n'
        #               reply: b'AT+CGATT=1\r\n\r\nOK\r\n'
        #               reply: b'AT+CIPSTART="TCP","101.201.105.176",5050\r\n\r\n+CME ERROR: 2\r\n'
        #               reply: b'AT+CGATT=1\r\n\r\nOK\r\n'
        'AT+CIPSEND={},1'
        #               reply: b'AT+CIPSEND=110,1\r\n\r\n>'
        'AT+ENBR'
                        reply: b'AT+ENBR\r\n\r\nERROR\r\n'

        'AT+IPR=band'
                        reply: b'AT+IPR=115200\r\n\r\nOK\r\n'
        'AT+FTPSERV=addr','AT+FTPGETNAME=filename',''AT+FTPUN=usr','AT+FTPPW=pwd','AT+FTPGET=1'(FTP order)
        """
        try:
            at_order = self.gprs_segments[0]

            order_reply_len = [3 if b'CSQ' in at_order else 2][0]
            if len(self.gprs_segments) != order_reply_len:
                return False

            module_reply = self.gprs_segments[-1]
            # Skip timestamp if receiver doesn't have on yet
            if b'OK' == module_reply or b'>' == module_reply:
                #print('at_order is {}'.format(at_order))
                self.ats_dict[at_order] = 1
            if b'CSQ' in at_order:
                dat = self.gprs_segments[1]
                try:
                    ind = dat.index(b',')
                    self.rssi = int(self.gprs_segments[1][ind-2:ind])
                except ValueError:
                    return False
        except ValueError:
            return False
        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        '''
        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()
        '''
        return True

    def sms(self):
        """Parse Recommended Minimum Specific GPS/Transit data (RMC)Sentence. Updates UTC timestamp, latitude,
        longitude, Course, Speed, Date, and fix status"""
        self.update_gnrmc = False
        # UTC Timestamp
        try:
            utc_string = self.gprs_segments[1]

            if utc_string:  # Possible timestamp found
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
                self.gnss_buf[9:17] = (utc_string[0:2]+':'+utc_string[2:4]+':'+utc_string[4:6]).encode()
            else:  # No Time stamp yet
                self.timestamp = (0, 0, 0)

        except ValueError:  # Bad Timestamp value present
            return False

        # Date stamp
        try:
            date_string = self.gprs_segments[9]

            # Date string printer function assumes to be year >=2000,
            # date_string() must be supplied with the correct century argument to display correctly
            if date_string:  # Possible date stamp found
                day = int(date_string[0:2])
                month = int(date_string[2:4])
                year = int(date_string[4:6])
                self.date = (day, month, year)
                self.gnss_buf[1:9] = (date_string[4:6]+'-'+date_string[2:4]+'-'+date_string[0:2]).encode()
            else:  # No Date stamp yet
                self.date = (0, 0, 0)

        except ValueError:  # Bad Date stamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gprs_segments[2] == 'A':  # Data from Receiver is Valid/Has Fix
            self.gnss_buf[0:1] = b'1'
            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gprs_segments[3]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gprs_segments[4]
                self.gnss_buf[17:18] = self.__HEMISPHERES[lat_hemi]
                self.gnss_buf[18:27] = '{:>09}'.format(self.gprs_segments[3][:9]).encode()
                # Longitude
                l_string = self.gprs_segments[5]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gprs_segments[6]
                self.gnss_buf[27:28] = self.__HEMISPHERES[lon_hemi]
                self.gnss_buf[28:38] = '{:>010}'.format(self.gprs_segments[5][:10]).encode()

            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES.keys():
                return False

            if lon_hemi not in self.__HEMISPHERES.keys():
                return False

            # Speed
            try:
                spd_knt = float(self.gprs_segments[7])
            except ValueError:
                return False

            # Course
            try:
                course = float(self.gprs_segments[8])
            except ValueError:
                return False

            # TODO - Add Magnetic Variation

            # Update Object Data
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            # Include mph and hm/h
            #self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
            self.speed = spd_knt * 1.852
            self.gnss_buf[42:45] = ('{:>03}'.format(int(self.speed))).encode()

            self.course = course
            self.gnss_buf[45:51] = ('%06.2f'%course).encode()

            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self.gnss_buf[0:1] = b'2'
            self.latitude = (0, 0.0, 'N')
            self.longitude = (0, 0.0, 'W')
            self.speed = 0
            self.course = 0.0
            self.date = (0, 0, 0)
            self.valid = False
        self.update_gnrmc = True
        return True

    def server(self):
        #print(self.gprs_segments)
        if len(self.gprs_segments) != 3 or self.gprs_segments[2] != b'\r\n':
            print('gprs_segments format is wrong')
            return False
        try :
            rx_buf = self.gprs_segments[1]
            self.gprs_segments = [b'']
            self.active_segment = 0
            self.char_count = 0
            # print('rx_buf is {}'.format(rx_buf))
            return self.unpack_server_data(rx_buf)
        except ValueError:
            return False
    def data(self):
        self.tx_buf = b''
        print('this data is just been sended')
        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        return 1

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self,opt):
        """Adjust Object Flags in Preparation for a New dat Sentence"""
        if opt == 'AT':
            self.gprs_segments = [b'AT']
            self.active_segment = 0
            #self.crc_xor = 0
            self.sentence_at_active = True
            #self.process_crc = True
            self.char_count = 2
        elif opt == 'data':
            self.active_segment = 0
            self.char_count = 11
            self.gprs_segments = [self.id]
            self.sentence_data_active = True
        elif opt == 'server':
            self.active_segment = 0
            self.char_count = 4
            self.gprs_segments = [b'+IPD']
            self.sentence_server_active = True
        else:
            pass
    
    def update(self, new_char):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_at_sentence = False
        valid_data_sentence = False
        valid_server_sentence = False
        # Validate new_char is a printable char
        # ascii_char = ord(new_char)
        
        self.char_count += 1
        #print('new_char is {}'.format(new_char))
        #print('active_segment is {}'.format(self.active_segment))
        #print('gprs_segments is {}'.format(self.gprs_segments))
        if new_char == 0:
            self.gprs_segments[self.active_segment] += b'\x00'
        else:
            self.gprs_segments[self.active_segment] += int_to_bytes(new_char)
        #print('gprs_segments is {}'.format(self.gprs_segments))

        # Check if a new string is starting ('AT')
        if new_char == int_from_bytes(b'T') and self.gprs_segments[self.active_segment][-2] == int_from_bytes(b'A'):
            self.new_sentence('AT')
            return False

        if self.sentence_at_active:
            # Validate new_char is a printable char
            if 10 <= new_char <= 126:
                #print('self.gprs_segments is {}'.format(self.gprs_segments))
                # Check if sentence is ending ('\r\n' over three times or '>'(AT+CIPSEND=109,1))
                
                if b'CSQ' in self.gprs_segments[0] and self.active_segment > 5:
                    return False
                if b'CSQ' not in self.gprs_segments[0] and self.active_segment > 3:
                    return False
                #### \r\n   13 10
                
                if (new_char == 10) and (self.gprs_segments[self.active_segment][-2] == 13):
                    #self.process_crc = False
                    self.gprs_segments[self.active_segment] = self.gprs_segments[self.active_segment][:-2]
                    self.active_segment += 1
                    self.gprs_segments.append(b'')
                    if b'ERROR' in self.gprs_segments[self.active_segment-1] or b'OK' in self.gprs_segments[self.active_segment-1]:
                        valid_at_sentence = True
                    #print('0 self.gprs_segments is {}'.format(self.gprs_segments))
                if new_char == int_from_bytes(b'>'):
                    valid_at_sentence = True

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_at_sentence:
                    self.gprs_segments = [i for i in self.gprs_segments if i != b'']
                    #self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_at_active = False  # Clear Active Processing Flag
                    #self.parsed_sentences += 1
                    print('self.gprs_segments is {}'.format(self.gprs_segments))
                    return self.at()

                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_at_active = False
        #print('char_count is {}'.format(self.char_count))
        #print('gprs_segments is {}'.format(self.gprs_segments[0][:11]))
        if self.char_count == 11 and self.gprs_segments[0][:11] == self.id:
            self.new_sentence('data')

            return None
        if self.sentence_data_active:
            #if self.char_count == len(self.tx_buf):
            #print('gprs_segments is {}'.format(self.gprs_segments[0]))
            #print('self.tx_buf is {}'.format(self.tx_buf))
            '''
            if isinstance(self.tx_buf,bytes):
                self.tx_buf = self.tx_buf.decode()
            '''
            #print('self.gprs_segments[0] is {}'.format(self.gprs_segments[0]))
            #print('self.tx_buf is {}'.format(self.tx_buf))
            if self.gprs_segments[0] == self.tx_buf:
                valid_data_sentence = True
                
            # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
            if valid_data_sentence:

                #self.clean_sentences += 1  # Increment clean sentences received
                #self.sentence_data_active = False  # Clear Active Processing Flag
                #self.parsed_sentences += 1
                print('self.gprs_segments is {}'.format(self.gprs_segments))
                #print('self.tx_buf is        {}'.format(self.tx_buf))
                return self.data()

            # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
            if self.char_count > self.SENTENCE_LIMIT:
                self.sentence_data_active = False
        #print('self.gprs_segments is {}  {}'.format(self.char_count,self.gprs_segments))
        if self.char_count == 4 and self.gprs_segments[0][:4] == b'+IPD':
            self.new_sentence('server')
            return None
        #print('gprs_segments is {}'.format(self.gprs_segments))
        if self.sentence_server_active:
            if new_char == 126 and self.active_segment == 0:
                self.gprs_segments[0] = self.gprs_segments[0][:-1]
                self.active_segment += 1
                self.gprs_segments.append(b'~')
                return None
            if new_char == 126 and self.active_segment == 1:
                self.active_segment += 1
                self.gprs_segments.append(b'')
            if self.gprs_segments[self.active_segment] == b'\r\n':
                valid_server_sentence = True
            if valid_server_sentence:
                self.sentence_server_active = False
                #print('self.gprs_segments ={}'.format(self.gprs_segments))
                return self.server()

        # Tell Host no new sentence was parsed
        return None

    def new_fix_time(self):
        """Updates a high resolution counter with current time when fix is updated. Currently only triggered from
        GGA, GSA and RMC sentences"""
        try:
            self.fix_time = pyb.millis()
        except NameError:
            self.fix_time = time.time()
    def time_since_fix(self):
        """Returns number of millisecond since the last sentence with a valid fix was parsed. Returns 0 if
        no fix has been found"""
        # Test if a Fix has been found
        if self.fix_time == 0:
            return -1
        # Try calculating fix time assuming using millis on a pyboard; default to seconds if not
        try:
            current = pyb.elapsed_millis(self.fix_time)
        except NameError:
            current = time.time() - self.fix_time
        return current
    # All the currently supported at sentences
    '''
    supported_at_order = {'AT':at, 'ATZ':atz, 'AT+CMGF=1':cmgf, 'AT+CNUM=?':cnum, 'AT+CSQ':csq, 
                          'AT+CIPCLOSE=0':cipclose,'AT+CMGR=1':cmgr, 'AT+CMGD=1,4':cmgd, 'AT+CMGS':cmgs,
                          'AT+CSTT="CMNET","",""':cstt, 'AT+CGATT=1':cgatt, 'AT+CIPSTART':cipstart,
                          'AT+CIPSEND':cipsend, 'AT+ENBR':enbr,'AT+IPR':ipr, 'AT+FTPSERV': ftpserv,
                          'AT+FTPGETNAME':ftpgetname, 'AT+FTPUN':ftpun,
                          'AT+FTPPW':ftppw, 'AT+FTPGET=1':ftpget}
    '''
    @property
    def csq(self):
        return self.rssi
    @property
    def gsm(self):
        return self.m



def test():
    test_sentence = [b'AT+CMGF=1\r\n\r\nOK\r\n',
                b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****',
                b'+IPD,28:~001674\xd1$\xdc\x9b\xa7-\xd4\xb93\x05(\x9c\xc1\x1d\xe2\x88\xffK\x0f\n~\r\nAT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n',
                b'AT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CIPSEND=108,1\r\n\r\n>']

    my_gprs = MicropyGPRS()
    my_gprs.tx_buf = b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****'
    for sentence in test_sentence:
        for y in sentence:
            buf = my_gprs.update(y)
            if buf:
                print(my_gprs.ats_dict)
                print(my_gprs.tx_buf)
                print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
                print()

test()
'''
my_gprs = MicropyGPRS()
sentence = b'+IPD,28:~001674\xd1$\xdc\x9b\xa7-\xd4\xb93\x05(\x9c\xc1\x1d\xe2\x88\xffK\x0f\n~\r\nAT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n'
for y in sentence:
    buf = my_gprs.update(y)
    if buf:
        print(my_gprs.ats_dict)
        print(my_gprs.tx_buf)
        print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
        print()

'''