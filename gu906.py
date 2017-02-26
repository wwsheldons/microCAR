#modify by wjy @20170106
import GL
from math import floor
from aes128 import encrypt,decrypt
from dd import get_key
import struct,os,time
try:
    from beep import alarm
except:
    pass
# Import pyb or time for fix time handling
try:
    # Assume running on pyboard
    import pyb
    GPRS_PORT = pyb.UART(4, 115200, read_buf_len=500)
    GPRS_EN = pyb.Pin(pyb.Pin.cpu.B4, pyb.Pin.OUT_PP)
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
    
    for i in range(256):
        cell = i
        for j in range(8):
            if cell & 1:
                cell = (cell >> 1) ^ POY
            else:
                cell >>= 1
        GL.dog.feed()
        yield cell
def get_table(n):
    for i, item in enumerate(_generate_crc_table()):
        if i == n:
            return item
    print('wrong crc_table index')
    return None
    
def crc32(datas):
    crc = 0xffffffff
    for c in datas:
        if type(c) == str:
            c = ord(c)
        
        crc = (crc >> 8) ^ get_table((crc ^ c) & 0xff)
        #crc = (crc >> 8) ^ crc_table[(crc ^ c) & 0xff]
    crc = crc ^ 0xfffffffF
    GL.dog.feed()
    return struct.pack(">I",crc)  # 4 bytes big

class MicropyGPRS(object):
    """GPRS Sentence Parser. Creates object that stores all relevant GPRS data and statistics.
    Include AT order , SMS and data from server.
    Parses sentences one character at a time using update(). """

    # Max Number of Characters a valid sentence can be (based on module limited)
    SENTENCE_LIMIT = 1000
    
    def __init__(self):
        '''
        Setup GPRS Object Status Flags, Internal Data Registers, etc
        '''
        GL.report_tick = 5
        GL.rx_order_dat = {}
        GL.m = 0
        GL.rssi = 0
        GL.send_9012 = 0
        GL.cme_error2 = 0
        '''
        GL.ERROR[0]  --- # invalid card
        GL.ERROR[1]  --- # out of gas station range
        GL.ERROR[2]  --- # error from server
        GL.ERROR[3]  --- # no_phone_card
        GL.ERROR[4]  --- # reserve
        '''
        GL.ERROR = [0]*5
        GL.SMS = False
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
        self.tx_buf = ''
        GL.rx_sms = {}
        self.admin_phone = '13592683720'
        GL.set_phone = ['','']
        self.tmp_record_flag = True
        self.tmp_record = b''
        
        # sms order
        
        GL.sms_opreat_lock = b''
        
        self.recv_set_sms = 0
        #GL.id = b'AP9904N0769'
        GL.sms_lock_power_on = False
        GL.sms_storage_phone = False
        GL.sms_storage_ip_id_port = False
        GL.sms_storage_pwd = False

        #####################
        # hardware init
        
        try:
            self.hw_port = GPRS_PORT
            self.hw_en = GPRS_EN
            self.gprs_init()
            #self.connect()
        except:
            print('simulation is starting')

    def gprs_init(self):
        self.hw_port.init(115200, read_buf_len=512)
        self.hw_en.low()
        self.send_at('AT')
        self.send_at('AT+CMGF=1')#TxtMode: english mode
    ########################################
    # opreate the gprs module
    ########################################
    def send_at(self,order,timeout = 1000):
        # GL.debug_print('send order is {}'.format(order))
        if self.hw_port.write('{}\r\n'.format(order)) == len(order)+2:
            self.ats_dict[order] = 0
            start_1 = time.ticks_ms()
            while True:
                GL.dog.feed()
                #print('9999999999')
                # print('time.ticks_diff(start_1, time.ticks_ms()) is {}'.format(time.ticks_diff(start_1, time.ticks_ms())))
                if time.ticks_diff(start_1, time.ticks_ms()) >= timeout:
                    return 0
                if self.update():
                    
                    return 1
        return 0
    def send_d(self,d,timeout = 1000):
        
        if not isinstance(d,bytearray):
            self.hw_port.write(bytearray(d))
            start_2 = time.ticks_ms()
            while True:
                GL.dog.feed()
                #print('888888888888')
                if time.ticks_diff(start_2, time.ticks_ms()) >= timeout:
                    return 0
                if self.update():
                    return 1
        if d == 0x1a:
            self.hw_port.writechar(0x1a)
            start_3 = time.ticks_ms()
            while True:
                GL.dog.feed()
                #print('7777777777777')
                if time.ticks_diff(start_3, time.ticks_ms()) >= timeout:
                    return 0
                if self.update():
                    return 1
        return None
    def send_dats(self,d,order = 0):
        '''
        if order:
            GL.debug_print('the order will be send is {}'.format(hex(order)[2:]))
        # 
        
        if GL.m == 0:
            connect()
        '''
        order = 'AT+CIPSEND={},1'.format(len(d))
        self.send_at(order)
        pyb.delay(50)
        # GL.debug_print('the dat will be send is{}'.format(d))
        self.send_d(d)
        #send_at('AT+CIPSEND={}'.format(len(d)))#bin type
        GL.dog.feed()
        return 1
    ## sms correlation 
    def rec_sms(self,num=1):
        return self.send_at('AT+CMGR={}'.format(num)) # the {num}th sms
    def del_sms(self):
        return self.send_at('AT+CMGD=1,4')#del all the sms
    def send_sms(self,phone_num,dat):
        #GL.debug_print('sms for {} will be sent'.format(phone_num))
        self.send_at('AT+CMGS=\"+86{}\"'.format(phone_num))
        #sleep_us(400)
        self.send_d(dat)#sms contents
        #sleep_us(400)
        self.send_d(0x1a)# send
        #sleep_us(400)
        pyb.delay(100)
        self.del_sms()
        #sleep_us(400)
        return 1
    def wait_set_sms(self,objSched):
        self.send_sms(self.admin_phone,'waiting for init by ip, port and id')
        tmp_n = 0
        while not self.recv_set_sms:
            objSched.add_thread(alarm())
            pyb.delay(1000)
            self.rec_sms()
            
            '''
            tmp_n += 1
            if tmp_n > 10:
                self.send_sms(self.admin_phone,'waiting for init by ip, port and id')
                tmp_n = 0
                pyb.delay(500)
            '''
            
        return 1
    def fac_reset(self):
        return self.send_at('ATZ')
    def check_phone_card(self):
        return self.send_at('AT+CNUM=?')
    def check_csq(self):
        return self.send_at('AT+CSQ')
    def get_location_gu(self):
        return self.send_at('AT+ENBR')
    #def conect_(ip = "101.201.105.176",port = 5050,apn='',usr = '',passwd=''):
    def connect(self):
        '''
        if apn != '' :
            send_at('AT+CSTT={},{},{}'.format(apn,usr,passwd))
            return GL.m
        '''
        if not GL.m:
            self.send_at('AT+CSTT="CMNET","",""')
            self.send_at('AT+CGATT=1')
            self.send_at('AT+CIPSTART="TCP","{}",{}'.format(GL.ip,GL.port))
        return 1
    ########################################
    # data from server Parsers
    ########################################
    def unpack_sms(self,num,context,opt = 0x01):
        GL.debug_print('num is {} and context is {}'.format(num,context))
        GL.SMS = True
        if 'password' in context:
            ind_password = context.index('password:')
            GL.pwd = context[ind_password+9:ind_password+14]
            GL.sms_storage_pwd = True
            #storage_gprs['m_pwd'](sms_password)
        if 'ip' in context and 'id' in context and 'port' in context:
            GL.sms_storage_ip_id_port = True
            ind_ip = context.index('ip:')
            ind_ip_end = context[ind_ip+1:].index('#')
            
            ind_port = context.index('port:')
            ind_id = context.index('id:')

            tmp_ip = context[ind_ip+3:ind_ip_end+ind_ip+1]
            tmp_id = context[ind_id+3:ind_id+14]
            tmp_port = int(context[ind_port+5:ind_port+9],10)
            try:
                if GL.ip != tmp_ip or tmp_port != GL.port or GL.id != tmp_id:
                    GL.ip = tmp_ip
                    GL.port = tmp_port
                    GL.id = tmp_id
                    self.send_sms(num,'ip port and id set OK')
            except:
                GL.ip = tmp_ip
                GL.port = tmp_port
                GL.id = tmp_id
                self.send_sms(num,'ip port and id set OK')
            finally:
                GL.debug_print('GL.ip = {} GL.id = {} GL.port = {}'.format(GL.ip,GL.id,GL.port))
                self.recv_set_sms = 1
            #GL.storage.modify_info(GL.storage.ipfn,GL.ip)
            #GL.storage.modify_info(GL.storage.portfn,str(GL.port))
            #GL.storage.modify_info(GL.storage.idfn,GL.id)
                
            
        if 'admin phone' in context:
            ind = context.index(':')
            ph1 = context[ind+1:ind+12]
            GL.sms_storage_phone = True
            if ',' in context:
                ind2 = context.index(',')
                ph2 = context[ind2+1:ind2+12]
                GL.set_phone[1] = ph1
                GL.set_phone[2] = ph2

                #storage_gprs['m_ap'](ph1+ph2)
            else:
                GL.set_phone[1] = ph1
                #storage_gprs['m_ap'](ph1)
            #send_sms(num,dat='admin phone set OK')
            return 1
        if 'ic' in context:
            ind = context.index('ic:')
            order = context[ind+3:]
            if num in [self.admin_phone]+GL.set_phone:
                GL.sms_opreat_lock = (order,num)
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
                GL.sms_lock_power_on = True
                '''
                GL.lock_status = [1]*12
                storage_gprs['m_ls'](0)
                lock_gprs['lp_ons']()
                send_sms(num,dat='locks have power on')
                '''
        return 1

    def pack_server_data(self,order,dat,opt = 0x01):
        GL.debug_print('send order is {}'.format(hex(order)))
        if not isinstance(dat,bytes):
            dat = bytes(dat)
        tmp_key_index = ('{:0>2}'.format(os.urandom(1)[0]%99)).encode()
        tmp_order = hex(order)[2:].encode() # 4 bytes
        tmp_data = tmp_order + dat
        if opt & 0x01:
            data = bytes(encrypt(tmp_data, get_key(int(str(tmp_key_index,'utf-8')))))
            #data = encrypt(tmp_data, get_key(int(str(tmp_key_index,'utf-8'))))
        else:
            data = tmp_data
        #len_dat = ('%04d'%(len(data))).encode()  # 4 bytes
        len_dat = ('{:0>4}'.format(len(data))).encode()
        tx_buf = len_dat+tmp_key_index+data
        crc_ = crc32(tx_buf)
        tx_buf = tx_buf + crc_
        tx_buf = transferred_meaning(tx_buf)
        self.tx_buf = b'~'+ tx_buf + b'~'
        GL.dog.feed()
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
            try:
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
                #GL.collect()
                

                #print('tmp_dat ={}'.format(tmp_dat))
                if (opt & 0x01):
                    #d = bytes(decrypt([i for i in tmp_dat],tmp_key,tmp_len_dat))
                    d = bytes(decrypt([i for i in tmp_dat],tmp_key,tmp_len_dat))

                else:
                    d = tmp_dat
                
                    #GL.collect()
                
                
                '''
                print('d ={}'.format(d))
                print('d[4:4+11] ={}'.format(d[4:4+11]))
                print('GL.id = {}'.format(GL.id))
                if d[4:4+11] != GL.id:
                    print('control id is wrong')
                    return False
                '''
                
                order = d[0:4].decode()
                #GL.debug_print('d = {}'.format(d))
                if order not in self.supported_order.keys():
                    print('wrong order from server')
                    return False

                if not GL.m:
                    GL.m = 1
                    GL.lcd_update(0)
                GL.cme_error2 = 0
                GL.send_9012 = 0
                if GL.ERROR[3]:
                    GL.ERROR[3] = 0
                    GL.lcd_update(9)
                
                if order in ['9002','9003','9005','9006','9012']:
                    
                    GL.debug_print('mmmmmmmmmmmmmmmmmmmmmmmmmmm')
                    GL.debug_print('order_from_server = {}'.format(order))
                    if order == '9002':
                        return self.handle_900a(0x1002)
                    if order == '9003':
                        return self.handle_900a(0x1003)
                    GL.rx_order_dat[order] = ''

                else:
                    start = 4+11  # length of order(4) and id(11)
                    if order in ['9000','9010','9007','9008','9009']:
                        len_of_frame = self.supported_order[order][0]-11
                        if order == '9010':
                            GL.report_tick = int(d[start:len_of_frame+start].decode())
                            GL.debug_print('GL.report_tick = {}'.format(GL.report_tick))
                            self.method1xxx(0x1010,GL.id,'{:0>4}'.format(GL.report_tick))
                            GL.dog.feed()
                            return self.send_dats(self.tx_buf,0x1010)
                            
                            
                    if order == '9004':
                        n = int(chr(d[4+11+1]))
                        len_of_frame = 13+59*n-11
                    if order == '9011':
                        n = d.index(b'y')
                        len_of_frame = n+1
                    if order == '9004' and '9004' in GL.rx_order_dat.keys():
                        GL.debug_print('-----------------------------9004')
                        GL.debug_print('order_from_server = {} and rx_dat = {}'.format(order,d[start:len_of_frame+start]))

                        GL.rx_order_dat['9004'] = [GL.rx_order_dat['9004'],d[start:len_of_frame+start]]
                    GL.rx_order_dat[order] = d[start:len_of_frame+start]
                    GL.debug_print('mmmmmmmmmmmmmmmmmmmmmmmmmmm')
                    GL.debug_print('order_from_server = {} and rx_dat = {}'.format(order,GL.rx_order_dat[order]))
                
                #GL.collect()
                
                GL.dog.feed()
                return 1
                #return self.supported_order[order][1](self)
            except:
                print('the data frame is broken')
                return False
        else:
            print('the data is not a frame')
            return False
    ########################################
    # Sentence Parsers
    ########################################
    def parser(self,opt):
        self.tmp_record_flag = True
        GL.debug_print('self.gprs_segments is {} and opt = {}'.format(self.gprs_segments,opt))
        tmp = False
        if opt == 'AT':
            tmp = self.at()
        if opt == 'data':
            tmp = self.data()
        if opt == 'server':
            tmp = self.server()

        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0

        if tmp:
            return True
        return False

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
        #self.tmp_record_flag = True
        try:
            at_order = self.gprs_segments[0]
            if b'CMGR' in at_order:
                return self.sms()
            order_reply_len = [3 if b'CSQ' in at_order else 2][0]
            if len(self.gprs_segments) != order_reply_len:
                return False
            

            module_reply = self.gprs_segments[-1]
            # Skip timestamp if receiver doesn't have on yet
            if b'AT+CNUM=?' in at_order:
                if b'OK' in module_reply:
                    if GL.ERROR[3]:
                        GL.ERROR[3] = 0
                        GL.lcd_update(9)
                else:
                    if not GL.ERROR[3]:
                        GL.ERROR[3] = 1
                        GL.lcd_update(9)

            if b'+CME ERROR: 15' in module_reply:
                if not GL.ERROR[3]:
                    GL.ERROR[3] = 1
                    GL.lcd_update(9)
            if b'+CME ERROR: 9' in module_reply:
                if GL.m:
                    GL.m = 0
                    GL.lcd_update(0)
                
                self.connect()
            if b'+CME ERROR: 2' in module_reply:
                GL.cme_error2 += 1
                #self.handle_900a(0x1002)
                GL.debug_print('GL.cme_error2 = {}'.format(GL.cme_error2))
                if GL.cme_error2 > 2:
                    if GL.m:
                        GL.m = 0
                        GL.lcd_update(0)
                    GL.cme_error2 = 0
                    self.send_at('AT+CIPCLOSE=0')

                '''
                if b'OK' in module_reply:
                    GL.m = 1
                '''
                #return None
            if b'OK' in module_reply or b'>' == module_reply:
                #print('at_order is {}'.format(at_order))
                self.ats_dict[at_order.decode()] = 1
            if b'CSQ' in at_order:
                dat = self.gprs_segments[1]
                try:
                    ind = dat.index(b',')
                    GL.rssi = int(self.gprs_segments[1][ind-2:ind])
                    if GL.rssi == 99:
                        if GL.m:
                            GL.m = 0
                            GL.lcd_update(0)
                except ValueError:
                    return False
        except ValueError:
            return False
        
        '''
        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()
        '''
        '''
        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        '''
        return True

    def sms(self):
        """Parse sms message
        'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n'
        'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
        """
        '''
        if len(self.gprs_segments) == 2 or b'ERROR' in self.gprs_segments[-1]:
            return False
        '''
        if  b'+CMS ERROR: 321' in self.gprs_segments[1]:
            return False

        try:
            phone_num = self.gprs_segments[1].split(b',')[1][1:-1].decode()
            if phone_num == '10086':
                self.del_sms()
                return False
            #GL.debug_print('phone_num is {} and sms is {}'.format(phone_num[3:],self.gprs_segments[2].decode()))
            self.phone_num = phone_num[3:]
            try:
                ph = [self.admin_phone]+GL.set_phone
            except:
                ph = [self.admin_phone]
            if phone_num[3:] in ph:
                #GL.rx_sms[phone_num[3:]] = self.gprs_segments[2].decode()
                #GL.rx_sms.append(self.gprs_segments[2].decode())
                self.unpack_sms(phone_num[3:],self.gprs_segments[2].decode())
                
            #print('phone_num is {}'.format(phone_num))
            

        except :  # Bad Timestamp value present
            return False
        '''
        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        '''
        return True

    def server(self):
        #print(self.gprs_segments)
        #self.tmp_record_flag = True
        '''
        if len(self.gprs_segments) != 3 or self.gprs_segments[2] != b'\r\n':
            print('gprs_segments format is wrong')
            return False
        '''
        try :

            rx_buf = self.gprs_segments[1]
            '''
            self.gprs_segments = [b'']
            self.active_segment = 0
            self.char_count = 0
            '''
            # print('rx_buf is {}'.format(rx_buf))
            return self.unpack_server_data(rx_buf)
        except ValueError:
            return False
    def data(self):
        
        #self.tmp_record_flag = True
        self.tx_buf = ''
        print('this data is just been sended')
        '''
        self.gprs_segments = [b'']
        self.active_segment = 0
        self.char_count = 0
        '''
        return 1

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self,mode,opt=1):
        """Adjust Object Flags in Preparation for a New dat Sentence"""
        #GL.debug_print('new_sentence {}'.format(mode))
        self.active_segment = 0
        self.tmp_record_flag = False
        self.tmp_record = b''
        if mode == 'AT':
            self.gprs_segments = [b'AT']
            self.sentence_at_active = True
            self.sentence_data_active = False
            self.sentence_server_active = False
            self.char_count = 2
        elif mode == 'data':
            if opt == 1:
                self.char_count = 11
                self.gprs_segments = [GL.id]
                self.sentence_data_active = True
            if opt == 2:
                return self.parser('data')
        elif mode == 'server':
            self.char_count = 4
            self.gprs_segments = [b'+IPD']
            self.sentence_server_active = True
        else:
            pass

    def update(self,new_char = 0):

        if not new_char:
            if self.hw_port.any():
                self._update(chr(self.hw_port.readchar()))
                
                #GL.collect()
                
                if GL.rx_order_dat or GL.SMS:
                    return 1
                else:
                    return 0
            return None
        else:
            self._update(new_char)
            
            #GL.collect()
            
            if GL.rx_order_dat:
                return 1
            else:
                return 0

    def _update(self, new_char):
        """Process a new input char and updates GPRS object if necessary based on special characters ('AT', '\r\n', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""
        '''
        try:
            if self.tmp_record[-2:] == b'\r\n':
                GL.debug_print('self.tmp_record is {}'.format(self.tmp_record))
        except:
            pass
        '''
        valid_at_sentence = False
        valid_data_sentence = False
        valid_server_sentence = False
        # Validate ascii_char is a printable char
        try:
        	ascii_char = ord(new_char)
        except:
        	print('new_char = {}'.format(new_char))
        self.char_count += 1

        #print('self.tmp_record = {}'.format(self.tmp_record))
        #print('gprs_segments is {}'.format(self.gprs_segments))
        if ascii_char == 0:
            if self.tmp_record_flag:
                self.tmp_record +=  b'\x00'
            else:
                self.gprs_segments[self.active_segment] += b'\x00'
        else:
            if self.tmp_record_flag:
                self.tmp_record += int_to_bytes(ascii_char)
            else:
                try:
                    self.gprs_segments[self.active_segment] += int_to_bytes(ascii_char)
                except:
                    self.gprs_segments = []
                    return None
        #

        # Check if a new string is starting ('AT')
        #if ascii_char == int_from_bytes(b'T') and self.gprs_segments[self.active_segment][-2] == int_from_bytes(b'A'):
        if len(self.tmp_record) >= 2 and self.tmp_record[-2:] == b'AT':
            self.new_sentence('AT')
            return False

        if self.sentence_at_active:
            # Validate ascii_char is a printable char
            if 10 <= ascii_char <= 126:
                #print('self.gprs_segments is {}'.format(self.gprs_segments))
                # Check if sentence is ending ('\r\n' over three times or '>'(AT+CIPSEND=109,1))
                '''
                b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
                '''
                '''
                if b'CSQ' in self.gprs_segments[0] and self.active_segment > 5:
                    return False
                if b'CMGD' in self.gprs_segments[0] and self.active_segment > 3:
                    return False
                if b'CMGR' in self.gprs_segments[0] and self.active_segment > 6:
                    return False
                if b'CSQ' not in self.gprs_segments[0]  and b'CMGR' not in self.gprs_segments[0] and self.active_segment > 3:
                    return False
                '''
                #if b'AT+CMGR' in self.gprs_segments[0] 
                #### \r\n   13 10
                if (ascii_char == 10) and (self.gprs_segments[self.active_segment][-2] == 13):
                    #self.process_crc = False
                    self.gprs_segments[self.active_segment] = self.gprs_segments[self.active_segment][:-2]
                    if self.active_segment >= 2:
                        if self.gprs_segments[self.active_segment] == self.gprs_segments[self.active_segment-1]:
                            del self.gprs_segments[self.active_segment]
                            self.active_segment -= 1
                    
                    self.active_segment += 1
                    self.gprs_segments.append(b'')
                    if b'ERROR' in self.gprs_segments[self.active_segment-1] or b'OK' in self.gprs_segments[self.active_segment-1]:
                        valid_at_sentence = True
                        #print('len(self.gprs_segments) ={}'.format(len(self.gprs_segments)))
                    #print('0 self.gprs_segments is {}'.format(self.gprs_segments))
                if ascii_char == int_from_bytes(b'>'):
                    valid_at_sentence = True

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_at_sentence:
                    self.gprs_segments = [i for i in self.gprs_segments if i != b'']
                    #self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_at_active = False  # Clear Active Processing Flag
                    #self.parsed_sentences += 1
                    #print('end at self.gprs_segments is {}'.format(self.gprs_segments))
                    return self.parser('AT')

                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_at_active = False
        #print('char_count is {}'.format(self.char_count))
        
        try:
            tmp = self.tx_buf.encode()
        except:
            tmp = self.tx_buf
        try:
            if len(self.tmp_record) >= len(self.tx_buf) > 0 and self.tmp_record[-len(self.tx_buf):] == tmp:
                return self.new_sentence('data',2)
        except:
            if self.tmp_record == 0x1a and self.tx_buf == 0x1a:
                return self.new_sentence('data',2)
        try:
            if len(self.tmp_record) >= 11 and self.tmp_record[-11:] == GL.id:
                self.new_sentence('data')
                return None
        except:
            pass
        if self.sentence_data_active:
            #print('gprs_segments is {}'.format(self.gprs_segments[0]))
            #print('self.tx_buf is {}'.format(self.tx_buf))
            if self.gprs_segments[0] == self.tx_buf:
                valid_data_sentence = True
                
            # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
            if valid_data_sentence:
                self.sentence_data_active = False  # Clear Active Processing Flag
                #self.parsed_sentences += 1
                #print('end data self.gprs_segments is {}'.format(self.gprs_segments))
                #print('self.tx_buf is        {}'.format(self.tx_buf))
                return self.parser('data')

            # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
            if self.char_count > self.SENTENCE_LIMIT:
                self.sentence_data_active = False
        
        #if self.char_count == 4 and self.gprs_segments[0][:4] == b'+IPD':
        if len(self.tmp_record) >= 4 and self.tmp_record[-4:] == b'+IPD':
            #print('000')
            self.new_sentence('server')
            return None
        #print('gprs_segments is {}'.format(self.gprs_segments))
        if self.sentence_server_active:
            #print('self.gprs_segments is {}  {}'.format(self.char_count,self.gprs_segments))
            if ascii_char == 126 and self.active_segment == 0:
                self.gprs_segments[0] = self.gprs_segments[0][:-1]
                self.active_segment += 1
                self.gprs_segments.append(b'~')
                return None
            if ascii_char == 126 and self.active_segment == 1 and len(self.gprs_segments[1]) > 5:
                self.active_segment += 1
                self.gprs_segments.append(b'')
            
            if self.active_segment == 2:
                if self.gprs_segments[1][-1] != 126 or len(self.gprs_segments[1]) > MicropyGPRS.SENTENCE_LIMIT:
                    self.active_segment = 0
                    self.gprs_segments = []
                    return None
                if self.gprs_segments[1][-1] == 126:
                    valid_server_sentence = True
            if self.gprs_segments[self.active_segment] == b'\r\n':
                valid_server_sentence = True
            if valid_server_sentence:
                #print('end server self.gprs_segments is {}'.format(self.gprs_segments))
                self.sentence_server_active = False
                #print('self.gprs_segments ={}'.format(self.gprs_segments))
                return self.parser('server')

        # Tell Host no new sentence was parsed
        return None

    

    ########################################
    # conmunication Protocol between control and server
    ########################################
    def method1xxx(self,order,*tupleArg):
        dat = b''.join([i.encode() if isinstance(i,str) else bytes(i) for i in tupleArg])
        #self.debug_print('dat before encrypt is {}'.format(dat))
        if self.pack_server_data(order,dat):
            return True


    def handle_900a(self,order,ic_id=''):
        lss = bytes(GL.lock_status)
        
        self.method1xxx(order,GL.id,lss,GL.gnss_buf,ic_id)
        if len(GL.gnss_buf) != 62:
            print('len(GL.gnss_buf) = {} and GL.gnss_buf = {}'.format(len(GL.gnss_buf),GL.gnss_buf))
        if self.send_dats(self.tx_buf,order):
            return 1
        else:
            return 0

    def send_1000(self):
        return self.handle_900a(0x1000,GL.ic_id)
    def send_1003(self):
        return self.handle_900a(0x1003)
    def send_1012(self):
        GL.send_9012 += 1
        if GL.send_9012 >= 2:
            GL.send_9012 = 0
            if GL.m:
                GL.m = 0
                GL.lcd_update(0)
            return self.connect()
        return self.handle_900a(0x1012)
    
    def handle_9000(self,objSched,my_lock,my_storage):
        for i in range(GL.N_lock):
            if GL.rx_order_dat['9000'][i] in [48,'0',b'0']:
                continue
            if GL.rx_order_dat['9000'][i] in [49,'1',b'1']:
                my_lock.open_lock(i)
            if GL.rx_order_dat['9000'][i] in [50,'2',b'2']:
                my_lock.close_lock(i)
                
            if GL.rx_order_dat['9000'][i] in [51,'3',b'3']:
                GL.ERROR[0] = 1 # line 3 E1
            if GL.rx_order_dat['9000'][i] in [52,'4',b'4']:
                GL.ERROR[1] = 1 # line 3 E2
            if GL.rx_order_dat['9000'][i] in [53,'5',b'5']:
                GL.ERROR[2] = 1 # line 3 E3
            if 1 in GL.ERROR[:3]:
                objSched.add_thread(alarm())

            GL.lcd_update(9) # line 3
        return self.handle_900a(0x1001)
    def handle_9002(self,objSched=0,my_lock=0,my_storage=0):
        return self.handle_900a(0x1002)
    def handle_9003(self,objSched=0,my_lock=0,my_storage=0):
        return self.send_1003()

    def handle_9004(self,objSched,my_lock,my_storage):
        step = 5
        if GL.rx_order_dat['9004'][0] == 48:
            mode = 'rewrite'
        elif GL.rx_order_dat['9004'][0] == 49:
            mode = 'add'
        else:
            print('write emergency data type is wrong')
            return None
        if isinstance(GL.rx_order_dat['9004'],bytes):
            GL.rx_order_dat['9004'] = [GL.rx_order_dat['9004']]
        for each_9004_dat in GL.rx_order_dat['9004']:
            num_of_gas = int(chr(each_9004_dat[1]),10)
            gas_data = each_9004_dat[2:num_of_gas*59+2]
            gas_data = [gas_data[i:i+59] for i in range(0,len(gas_data),59)]
            
            GL.debug_print('gas_data = {}'.format(gas_data))
            if my_storage.modify_infos(my_storage.gifn,gas_data,mode):
                info = GL.id+str(num_of_gas)+''.join([i[:6].decode() for i in gas_data[:num_of_gas]])
                GL.debug_print('send 1004 dat is {}'.format(info))
                self.method1xxx(0x1004,info)
                self.send_dats(self.tx_buf,0x1004)
                pyb.delay(100)
                GL.dog.feed()
                #GL.collect()
            else:
                continue
        return 1
    def handle_9005(self,objSched,my_lock,my_storage):
        step = 3
        n = my_storage.get_rows(my_storage.gifn)
        GL.debug_print('there is {} gas info'.format(n))
        if n == 0:
            self.method1xxx(0x1005,GL.id,'0')
            self.send_dats(self.tx_buf,0x1005)
        else:
            for infos in my_storage.get_infos(my_storage.gifn,step):
                GL.debug_print('s = {}, and infos = {}'.format(len(infos),infos))
                self.method1xxx(0x1005,GL.id,str(len(infos)),b''.join(infos))
                self.send_dats(self.tx_buf,0x1005)
                pyb.delay(100)
                GL.dog.feed()
        #GL.collect()
        return 1
    def handle_9006(self,objSched,my_lock,my_storage):
        n = my_storage.get_rows(my_storage.gifn)
        GL.debug_print('there is {} gas infos'.format(n))
        my_storage.modify_info(my_storage.gifn,'')
        self.method1xxx(0x1006,GL.id,str(n))
        if self.send_dats(self.tx_buf,0x1006):
            #GL.collect()
            
            return 1
        else:
            return 0
    def handle_9007(self,objSched,my_lock,my_storage):
        if int(GL.rx_order_dat['9007'][-2:]) == 0:
            filename = my_storage.eccfn
        elif int(GL.rx_order_dat['9007'][-2:]) > 0:
            filename = my_storage.eocfn
        else:
            return None
        my_storage.modify_info(filename,GL.rx_order_dat['9007'],'add')
        n = my_storage.get_rows(filename)
        # emergency card only can write one each time
        info = my_storage.get_info(filename,n)
        print('{}th info = {}'.format(n,info))
        self.method1xxx(0x1007,GL.id,info)
        if self.send_dats(self.tx_buf,0x1007):
            #GL.collect()
            return 1
        else:
            return 0
    def handle_9008(self,objSched,my_lock,my_storage):
        if GL.rx_order_dat['9008'] == b'1':
            my_lock.locks_power_on()
            my_storage.modify_info(my_storage.lsfn,'')
        elif GL.rx_order_dat['9008'] == b'2':
            my_lock.locks_power_off()
        else:
            return 0
        # my_lock.locks_power_status
        self.method1xxx(0x1008,GL.id,GL.rx_order_dat['9008'])
        self.send_dats(self.tx_buf,0x1008)
        
        #GL.collect()
        
        return 1
    def handle_9009(self,objSched,my_lock,my_storage):
        
        if GL.rx_order_dat['9009'] in [b'1',49]:
            pyb.delay(1000)
            pyb.hard_reset()
    def handle_9010(self,objSched,my_lock,my_storage):
        GL.report_tick = int(GL.rx_order_dat['9010'].decode())
        self.method1xxx(0x1010,GL.id,'{:0>4}'.format(GL.report_tick))
        if self.send_dats(self.tx_buf,0x1010):
            #GL.collect()
            return 1
        else:
            return 0
    def handle_9011(self,objSched,my_lock,my_storage):
        GL.debug_print('9011 rx_dat {}'.format(GL.rx_order_dat['9011']))
    def handle_9012(self,objSched,my_lock,my_storage):
        GL.send_9012 -= 1
        if GL.send_9012 < 0:
            GL.send_9012 = 0
        #GL.collect()
        return 1
    
    # All the currently supported at sentences
    '''
    supported_order = {'9000':(23,),'9010':(15,),'9007':(21,),
                       '9008':(12,),'9009':(12,),'9004':(72,),
                       '9005':(11,),'9006':(11,),'9002':(11,),
                       '9003':(11,),'9005':(11,),'9006':(11,),
                       '9011':(12,),'9012':(11,)}
    
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
    
    





'''
def test():
    test_sentence = [b'AT+CMGF=1\r\n\r\nOK\r\n',
                b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n',
                b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****',
                b'+IPD,28:~001674\xd1$\xdc\x9b\xa7-\xd4\xb93\x05(\x9c\xc1\x1d\xe2\x88\xffK\x0f\n~\r\nAT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CMGR=1\r\n\r\n+CMS ERROR: 321\r\n',
                b'AT+CSQ\r\n\r\n+CSQ: 31, 99\r\n\r\nOK\r\n',
                b'AT+CIPSEND=108,1\r\n\r\n>',
                b'\r\nCONNECT OK\r\n+IPD,28:~001652\x97a\xd9\xf7(\x9a\x81t\xc2\x99\xb3=\xa8\x1b\xca,T\x8e\xe3y~\r\n']
    a=b=1
    my_gprs = MicropyGPRS(a,b)
    my_gprs.tx_buf = b'AP9904N0769!\x00\x00\x00\x00\x00\x00!\x00\x00\x00\x00117-01-0309:53:5813447.7089111335.64990123000122.09161111*****'
    for sentence in test_sentence:
        print('sentence is {}'.format(sentence))
        for y in sentence:
            buf = my_gprs._update(chr(y))
            if buf:
                print('my_gprs.ats_dict = {}'.format(my_gprs.ats_dict))
                #print('my_gprs.tx_buf = {}'.format(my_gprs.tx_buf))
                print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
                print('my_gprs.rx_dat = {}'.format(my_gprs.rx_dat))
                print()

test()

my_gprs = MicropyGPRS()
sentence = b'AT+CMGR=1\r\n\r\n+CMGR: "REC READ","+8613592683720",,"2017/01/09 19:35:38+32"\r\n111111\r\n\r\nOK\r\n'
for y in sentence:
    buf = my_gprs._update(y)
    if buf:
        print(my_gprs.ats_dict)
        print(my_gprs.tx_buf)
        print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
        print()

'''