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



def int_to_bytes(x):
    #return x.to_bytes(len(bin(a)[2:])//8+1, 'little')
    #return x.to_bytes((x.bit_length() + 7) // 8, 'little')
    return (x).to_bytes(1, 'little')

def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'little')

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
def _generate_crc_table():
    POY = 0xEDB88320
    crc_table = [0]*256
    for i in range(256):
        cell = i
        for j in range(8):
            if cell & 1:
                cell = (cell >> 1) ^ POY
            else:
                cell >>= 1
        yield cell
def get_table(n):
    if n > 255:
        print('wrong crc_table index')
        return None
    for i, item in enumerate(_generate_crc_table()):
        if i == n:
            return item
def crc32(datas):
    crc = 0xffffffff
    for c in datas:
        if type(c) == str:
            c = ord(c)
        crc = (crc >> 8) ^ get_table((crc ^ c) & 0xff)
        #crc = (crc >> 8) ^ crc_table[(crc ^ c) & 0xff]
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
    
    def __init__(self, hw_port,hw_en, ip='101.201.105.176', port=8080, _id=b'AP9904N0769', pwd='123456', local_offset=0):
        '''
        Setup GPS Object Status Flags, Internal Data Registers, etc
        '''
        #####################
        # hardware
        self.hw_port = hw_port
        self.hw_en = hw_en

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
        self.m = 0
        #####################
        # buf
        self.tx_buf = b''
        self.active_order = 0
        self.order_from_server = []
        self.rx_dat = []
        self.rx_sms = []
        self.admin_phone = '13592683720'
        self.set_phone = ['','']
        self.tmp_record_flag = True
        self.tmp_record = b''
        self.rssi = 0
        # sms order
        self.pwd = pwd
        self.opreat_lock = ''
        self.ip = ip
        self.port = port
        self.id = _id
        #self.id = b'AP9904N0769'
        self.lock_power_on = False
        self.storage_phone = False
        self.storage_ip_id_port = False
        self.storage_pwd = False

        #####################
        # hardware init
        self.gprs_init()

    def gprs_init(self):
        self.hw_port.init(115200, read_buf_len=512)
        self.hw_en.low()
        self.send_at('AT+CMGF=1')#TxtMode: english mode
    ########################################
    # opreate the gprs module
    ########################################
    def send_at(self,order):
        #self.debug_print('send order is {}'.format(order))
        if self.hw_port.write('{}\r\n'.format(order)) == len(order)+2:
            self.ats_dict[order] = 0
            return 1
        return 0
    def send_d(self,d):
        if not isinstance(d,bytearray):
            return self.hw_port.write(bytearray(d))
        if d == 0x1a:
            return self.hw_port.writechar(0x1a)
        return 0
    def send_dats(self,d,order = 0):
        '''
        if order:
            self.debug_print('the order will be send is {}'.format(hex(order)[2:]))
        # self.debug_print('the dat will be send is{}'.format(d))
        
        if GL.m == 0:
            conect_()
        '''
        order = 'AT+CIPSEND={},1'.format(len(d))
        send_at(order)
        #send_at('AT+CIPSEND={}'.format(len(d)))#bin type
        if ats_dict[order]:
            return send_d(d)
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
        self.rssi = 0
        return self.send_at('AT+CSQ')
    def get_location_gu(self):
        return send_at('AT+ENBR')
    #def conect_(ip = "101.201.105.176",port = 5050,apn='',usr = '',passwd=''):
    def connect(self,ip,port):
        '''
        if apn != '' :
            send_at('AT+CSTT={},{},{}'.format(apn,usr,passwd))
            return GL.m
        '''
        send_at('AT+CSTT="CMNET","",""')
        if ats_dict['AT+CSTT="CMNET","",""']:
            send_at('AT+CGATT=1')
            if ats_dict['AT+CGATT=1']:
                return send_at('AT+CIPSTART="TCP","{}",{}'.format(ip,port))
    ########################################
    # data from server Parsers
    ########################################
    def unpack_sms(self,num,context,opt = 0x01):
        # self.debug_print('num is {} and context is {}'.format(num,context))
        if 'password' in context:
            ind_password = context.index('password:')
            self.pwd = context[ind_password+9:ind_password+14]
            self.storage_pwd = True
            #storage_gprs['m_pwd'](sms_password)
        if 'ip' in context and 'id' in context and 'port' in context:
            self.storage_ip_id_port = True
            ind_ip = context.index('ip:')
            ind_ip_end = context[ind_ip+1:].index('#')
            self.ip = context[ind_ip+3:ind_ip_end+ind_ip+1]
            #storage_gprs['m_ip'](ip)
            ind_port = context.index('port:')
            self.port = context[ind_port+5:ind_port+9]
            #storage_gprs['m_port'](port)
            ind_id = context.index('id:')
            self.id = context[ind_id+3:ind_id+14]
            #storage_gprs['m_id'](id)
            #self.send_sms(num,dat='ip port and id set OK')
            #storage_gprs['m_using_times']()
            #recv_set_sms = 1
        if 'admin phone' in context:
            ind = context.index(':')
            ph1 = context[ind+1:ind+12]
            self.storage_phone = True
            if ',' in context:
                ind2 = context.index(',')
                ph2 = context[ind2+1:ind2+12]
                self.set_phone[1] = ph1
                self.set_phone[2] = ph2

                #storage_gprs['m_ap'](ph1+ph2)
            else:
                self.set_phone[1] = ph1
                #storage_gprs['m_ap'](ph1)
            #send_sms(num,dat='admin phone set OK')
            return 1
        if 'ic' in context:
            ind = context.index('ic:')
            order = context[ind+3:]
            if num == self.admin_phone:
                self.opreat_lock = order
            #return sms_operate_lock(order,num)
        if 'power' in context:
            ind = context.index('power')+6
            order = context[ind:]
            if order == 'restart':
                self.send_sms(num,'the board will be restart after 2 seconds')
                try:
                    pyb.delay(2000)
                except NameError:
                    time.sleep(2)
                pyb.hard_reset()
        if 'lock' in context:
            ind = context.index('lock:')+5
            order = context[ind:]
            if order == 'on':
                self.lock_power_on = True
                '''
                GL.lock_status = [1]*12
                storage_gprs['m_ls'](0)
                lock_gprs['lp_ons']()
                send_sms(num,dat='locks have power on')
                '''
                return 1

    def pack_server_data(order,dat,opt = 0x01):
        if not isinstance(dat,bytes):
            dat = bytes(dat)
        tmp_key_index = ('{:0>2}'.format(os.urandom(1)[0]%99)).encode()
        tmp_order = hex(order)[2:].encode() # 4 bytes
        tmp_data = tmp_order + dat
        if opt & 0x01:
            data = bytes(encrypt(tmp_data, get_key(int(str(tmp_key_index,'utf-8')))))
        else:
            data = tmp_data
        #len_dat = ('%04d'%(len(data))).encode()  # 4 bytes
        len_dat = ('{:0>4}'.format(len(data))).encode()
        tx_buf = len_dat+tmp_key_index+data
        crc_ = crc32(tx_buf)
        tx_buf = tx_buf + crc_
        tx_buf = transferred_meaning(tx_buf)
        self.tx_buf = b'~'+ tx_buf + b'~'
        return True
        #return self.tx_buf
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
            if order not in self.supported_order.keys():
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
                    len_of_frame = self.supported_order[order][0]-11
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
                               'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
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
        self.tmp_record_flag = True
        try:
            at_order = self.gprs_segments[0]
            if b'CMGR' in at_order:
                return self.sms()
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
        """Parse sms message
        'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n'
        'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
        """

        if len(self.gprs_segments) == 2 or b'ERROR' in self.gprs_segments[-1]:
            return False
        try:
            phone_num = self.gprs_segments[1].split(b',')[1][1:-1].decode()
            if phone_num[3:] == self.admin_phone[0]:
                self.rx_sms.append(self.gprs_segments[2].decode())
            #print('phone_num is {}'.format(phone_num))
            print('self.rx_sms is {}'.format(self.rx_sms))

        except ValueError:  # Bad Timestamp value present
            return False

        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        return True

    def server(self):
        #print(self.gprs_segments)
        self.tmp_record_flag = True

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
        self.tmp_record_flag = True

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
        self.active_segment = 0
        self.tmp_record_flag = False
        self.tmp_record = b''
        if opt == 'AT':
            self.gprs_segments = [b'AT']
            self.sentence_at_active = True
            self.char_count = 2
        elif opt == 'data':
            self.char_count = 11
            self.gprs_segments = [self.id]
            self.sentence_data_active = True
        elif opt == 'server':
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
            if self.tmp_record_flag:
                self.tmp_record +=  b'\x00'
            else:
                self.gprs_segments[self.active_segment] += b'\x00'
        else:
            if self.tmp_record_flag:
                self.tmp_record +=  int_to_bytes(new_char)
            else:
                self.gprs_segments[self.active_segment] += int_to_bytes(new_char)
        #print('gprs_segments is {}'.format(self.gprs_segments))

        # Check if a new string is starting ('AT')
        #if new_char == int_from_bytes(b'T') and self.gprs_segments[self.active_segment][-2] == int_from_bytes(b'A'):
        if len(self.tmp_record) == 2 and self.tmp_record == b'AT':
            self.new_sentence('AT')
            return False

        if self.sentence_at_active:
            # Validate new_char is a printable char
            if 10 <= new_char <= 126:
                #print('self.gprs_segments is {}'.format(self.gprs_segments))
                # Check if sentence is ending ('\r\n' over three times or '>'(AT+CIPSEND=109,1))
                '''
                b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
                '''
                if b'CSQ' in self.gprs_segments[0] and self.active_segment > 5:
                    return False
                if b'CMGR' in self.gprs_segments[0] and self.active_segment > 6:
                    return False
                if b'CSQ' not in self.gprs_segments[0]  and b'CMGR' not in self.gprs_segments[0] and self.active_segment > 3:
                    return False
                #if b'AT+CMGR' in self.gprs_segments[0] 
                #### \r\n   13 10
                
                if (new_char == 10) and (self.gprs_segments[self.active_segment][-2] == 13):
                    #self.process_crc = False
                    self.gprs_segments[self.active_segment] = self.gprs_segments[self.active_segment][:-2]
                    self.active_segment += 1
                    self.gprs_segments.append(b'')
                    if b'ERROR' in self.gprs_segments[self.active_segment-1] or b'OK' in self.gprs_segments[self.active_segment-1]:
                        valid_at_sentence = True
                        #print('len(self.gprs_segments) ={}'.format(len(self.gprs_segments)))
                    #print('0 self.gprs_segments is {}'.format(self.gprs_segments))
                if new_char == int_from_bytes(b'>'):
                    valid_at_sentence = True

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_at_sentence:
                    self.gprs_segments = [i for i in self.gprs_segments if i != b'']
                    #self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_at_active = False  # Clear Active Processing Flag
                    #self.parsed_sentences += 1
                    print('end at self.gprs_segments is {}'.format(self.gprs_segments))
                    return self.at()

                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_at_active = False
        #print('char_count is {}'.format(self.char_count))
        #print('gprs_segments is {}'.format(self.gprs_segments[0][:11]))
        
        #if self.char_count == 11 and self.gprs_segments[0][:11] == self.id:
        if len(self.tmp_record) == 11 and self.tmp_record == self.id:
            self.new_sentence('data')
            return None

        if self.sentence_data_active:
            #print('gprs_segments is {}'.format(self.gprs_segments[0]))
            #print('self.tx_buf is {}'.format(self.tx_buf))
            if self.gprs_segments[0] == self.tx_buf:
                valid_data_sentence = True
                
            # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
            if valid_data_sentence:
                self.sentence_data_active = False  # Clear Active Processing Flag
                #self.parsed_sentences += 1
                print('end data self.gprs_segments is {}'.format(self.gprs_segments))
                #print('self.tx_buf is        {}'.format(self.tx_buf))
                return self.data()

            # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
            if self.char_count > self.SENTENCE_LIMIT:
                self.sentence_data_active = False
        
        #if self.char_count == 4 and self.gprs_segments[0][:4] == b'+IPD':
        if len(self.tmp_record) == 4 and self.tmp_record == b'+IPD':
            #print('000')
            self.new_sentence('server')
            return None
        #print('gprs_segments is {}'.format(self.gprs_segments))
        if self.sentence_server_active:
            #print('self.gprs_segments is {}  {}'.format(self.char_count,self.gprs_segments))
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
                print('end server self.gprs_segments is {}'.format(self.gprs_segments))
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
    
    

    ########################################
    # conmunication Protocol between control and server
    ########################################
    def method1xxx(self,order,*tupleArg):#bytes(i) elif isinstance(i,bytearray)
        dat = b''.join([i.encode() if isinstance(i,str)  else i for i in tupleArg])
        #self.debug_print('dat before encrypt is {}'.format(dat))
        if self.pack_server_data(order,dat):
            return True

    def handle_900x(self,lss,order,gnss_buf,ic_id=''):
        '''
        #lock_gprs['update_ls']()
        lss = bytes(GL.lock_status)
        while not GL.gnss_dat_OK:
            tmp = GL.gnss_port.readline()
            gnss_gprs['update_buf'](tmp)
        '''
        if method1xxx(order,self.id,lss,gnss_buf,ic_id):
            self.send_dats(self.tx_buf,order)
            return 1
    def handle_9000():
        # self.debug_print('9000 rx_dat {}'.format(self.rx_dat))
        for i in range(GL.N_lock):
            #print('GL.rx_dat[i] is {}'.format(GL.rx_dat[i]))
            if self.rx_dat[i] in [48,'0',b'0']:
                pass
            if self.rx_dat[i] in [49,'1',b'1']:
                lock_gprs['open'](i)
            if self.rx_dat[i] in [50,'2',b'2']:
                lock_gprs['close'](i)
            if self.rx_dat[i] in [51,'3',b'3']:
                update_err(1)
            if self.rx_dat[i] in [52,'4',b'4']:
                update_err(2)
            if self.rx_dat[i] in [53,'5',b'5']:
                update_err(3)
        if b'3' in self.rx_dat or b'4' in self.rx_dat or b'5' in self.rx_dat:
            alarm(3)
        return handle_900x(0x1001)


    # All the currently supported at sentences
    '''
    supported_at_order = {'AT':at, 'ATZ':atz, 'AT+CMGF=1':cmgf, 'AT+CNUM=?':cnum, 'AT+CSQ':csq, 
                          'AT+CIPCLOSE=0':cipclose,'AT+CMGR=1':cmgr, 'AT+CMGD=1,4':cmgd, 'AT+CMGS':cmgs,
                          'AT+CSTT="CMNET","",""':cstt, 'AT+CGATT=1':cgatt, 'AT+CIPSTART':cipstart,
                          'AT+CIPSEND':cipsend, 'AT+ENBR':enbr,'AT+IPR':ipr, 'AT+FTPSERV': ftpserv,
                          'AT+FTPGETNAME':ftpgetname, 'AT+FTPUN':ftpun,
                          'AT+FTPPW':ftppw, 'AT+FTPGET=1':ftpget}
    '''
    supported_order = {'9000':(23,handle_9000),'9010':(15,handle_9010),'9007':(21,handle_9007),
                       '9008':(12,handle_9008),'9009':(12,handle_9009),'9004':(72,handle_9004),
                       '9005':(11,handle_9005),'9006':(11,handle_9006),'9002':(11,handle_9002),
                       '9003':(11,handle_9003),'9005':(11,handle_9005),'9006':(11,handle_9006),
                       '9011':(12,handle_9011),'9012':(11,handle_9012)}
    

    @property
    def csq(self):
        return self.rssi
    @property
    def gsm(self):
        return self.m



    
def test():
    test_sentence = [b'AT+CMGF=1\r\n\r\nOK\r\n',
                b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n',
                b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****',
                b'+IPD,28:~001674\xd1$\xdc\x9b\xa7-\xd4\xb93\x05(\x9c\xc1\x1d\xe2\x88\xffK\x0f\n~\r\nAT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n',
                b'AT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CIPSEND=108,1\r\n\r\n>']

    my_gprs = MicropyGPRS()
    my_gprs.tx_buf = b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****'
    for sentence in test_sentence:
        print('sentence is {}'.format(sentence))
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
sentence = b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
for y in sentence:
    buf = my_gprs.update(y)
    if buf:
        print(my_gprs.ats_dict)
        print(my_gprs.tx_buf)
        print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
        print()

'''