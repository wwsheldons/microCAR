import pyb
import os
import struct




#lock_key1=[0x29,0x23,0xbe,0x84,0xe1,0x6c,0xd6,0xae,0x52,0x90,0x49,0xf1,0xf1,0xbb,0xe9,0xeb,0xb3,0xa6,0xdb,0x3c,0x87,0x0c,0x3e,0x99,0x24,0x5e,0x0d,0x1c,0x06,0xb7,0x47,0xde,0xb3,0x12,0x4d,0xc8,0x43,0xbb,0x8b,0xa6,0x1f,0x03,0x5a,0x7d,0x09,0x38,0x25,0x1f,0x5d,0xd4,0xcb,0xfc,0x96,0xf5,0x45,0x3b,0x13,0x0d,0x89,0x0a,0x1c,0xdb,0xae,0x32,0x20,0x9a,0x50,0xee,0x40,0x78,0x36,0xfd,0x12,0x49,0x32,0xf6,0x9e,0x7d,0x49,0xdc,0xad,0x4f,0x14,0xf2,0x44,0x40,0x66,0xd0,0x6b,0xc4,0x30,0xb7,0x32,0x3b,0xa1,0x22,0xf6,0x22,0x91,0x9d,0xe1,0x8b,0x1f,0xda,0xb0,0xca,0x99,0x02,0xb9,0x72,0x9d,0x49,0x2c,0x80,0x7e,0xc5,0x99,0xd5,0xe9,0x80,0xb2,0xea,0xc9,0xcc,0x53,0xbf,0x67,0xd6,0xbf,0x14,0xd6,0x7e,0x2d,0xdc,0x8e,0x66,0x83,0xef,0x57,0x49,0x61,0xff,0x69,0x8f,0x61,0xcd,0xd1,0x1e,0x9d,0x9c,0x16,0x72,0x72,0xe6,0x1d,0xf0,0x84,0x4f,0x4a,0x77,0x02,0xd7,0xe8,0x39,0x2c,0x53,0xcb,0xc9,0x12,0x1e,0x33,0x74,0x9e,0x0c,0xf4,0xd5,0xd4,0x9f,0xd4,0xa4,0x59,0x7e,0x35,0xcf,0x32,0x22,0xf4,0xcc,0xcf,0xd3,0x90,0x2d,0x48,0xd3,0x8f,0x75,0xe6,0xd9,0x1d,0x2a,0xe5,0xc0,0xf7,0x2b,0x78,0x81,0x87,0x44,0x0e,0x5f,0x50,0x00,0xd4,0x61,0x8d,0xbe,0x7b,0x05,0x15,0x07,0x3b,0x33,0x82,0x1f,0x18,0x70,0x92,0xda,0x64,0x54,0xce,0xb1,0x85,0x3e,0x69,0x15,0xf8,0x46,0x6a,0x04,0x96,0x73,0x0e,0xd9,0x16,0x2f,0x67,0x68,0xd4,0xf7,0x4a,0x4a,0xd0,0x57,0x68,0x76]
#lock_key2=[0xfa,0x16,0xbb,0x11,0xad,0xae,0x24,0x88,0x79,0xfe,0x52,0xdb,0x25,0x43,0xe5,0x3c,0xf4,0x45,0xd3,0xd8,0x28,0xce,0x0b,0xf5,0xc5,0x60,0x59,0x3d,0x97,0x27,0x8a,0x59,0x76,0x2d,0xd0,0xc2,0xc9,0xcd,0x68,0xd4,0x49,0x6a,0x79,0x25,0x08,0x61,0x40,0x14,0xb1,0x3b,0x6a,0xa5,0x11,0x28,0xc1,0x8c,0xd6,0xa9,0x0b,0x87,0x97,0x8c,0x2f,0xf1,0x15,0x1d,0x9a,0x95,0xc1,0x9b,0xe1,0xc0,0x7e,0xe9,0xa8,0x9a,0xa7,0x86,0xc2,0xb5,0x54,0xbf,0x9a,0xe7,0xd9,0x23,0xd1,0x55,0x90,0x38,0x28,0xd1,0xd9,0x6c,0xa1,0x66,0x5e,0x4e,0xe1,0x30,0x9c,0xfe,0xd9,0x71,0x9f,0xe2,0xa5,0xe2,0x0c,0x9b,0xb4,0x47,0x65,0x38,0x2a,0x46,0x89,0xa9,0x82,0x79,0x7a,0x76,0x78,0xc2,0x63,0xb1,0x26,0xdf,0xda,0x29,0x6d,0x3e,0x62,0xe0,0x96,0x12,0x34,0xbf,0x39,0xa6,0x3f,0x89,0x5e,0xf1,0x6d,0x0e,0xe3,0x6c,0x28,0xa1,0x1e,0x20,0x1d,0xcb,0xc2,0x03,0x3f,0x41,0x07,0x84,0x0f,0x14,0x05,0x65,0x1b,0x28,0x61,0xc9,0xc5,0xe7,0x2c,0x8e,0x46,0x36,0x08,0xdc,0xf3,0xa8,0x8d,0xfe,0xbe,0xf2,0xeb,0x71,0xff,0xa0,0xd0,0x3b,0x75,0x06,0x8c,0x7e,0x87,0x78,0x73,0x4d,0xd0,0xbe,0x82,0xbe,0xdb,0xc2,0x46,0x41,0x2b,0x8c,0xfa,0x30,0x7f,0x70,0xf0,0xa7,0x54,0x86,0x32,0x95,0xaa,0x5b,0x68,0x13,0x0b,0xe6,0xfc,0xf5,0xca,0xbe,0x7d,0x9f,0x89,0x8a,0x41,0x1b,0xfd,0xb8,0x4f,0x68,0xf6,0x72,0x7b,0x14,0x99,0xcd,0xd3,0x0d,0xf0,0x44,0x3a,0xb4,0xa6,0x66,0x53,0x33,0x0b,0xcb,0xa1,0x10]

lock_key1 = b')#\xbe\x84\xe1l\xd6\xaeR\x90I\xf1\xf1\xbb\xe9\xeb\xb3\xa6\xdb<\x87\x0c>\x99$^\r\x1c\x06\xb7G\xde\xb3\x12M\xc8C\xbb\x8b\xa6\x1f\x03Z}\t8%\x1f]\xd4\xcb\xfc\x96\xf5E;\x13\r\x89\n\x1c\xdb\xae2 \x9aP\xee@x6\xfd\x12I2\xf6\x9e}I\xdc\xadO\x14\xf2D@f\xd0k\xc40\xb72;\xa1"\xf6"\x91\x9d\xe1\x8b\x1f\xda\xb0\xca\x99\x02\xb9r\x9dI,\x80~\xc5\x99\xd5\xe9\x80\xb2\xea\xc9\xccS\xbfg\xd6\xbf\x14\xd6~-\xdc\x8ef\x83\xefWIa\xffi\x8fa\xcd\xd1\x1e\x9d\x9c\x16rr\xe6\x1d\xf0\x84OJw\x02\xd7\xe89,S\xcb\xc9\x12\x1e3t\x9e\x0c\xf4\xd5\xd4\x9f\xd4\xa4Y~5\xcf2"\xf4\xcc\xcf\xd3\x90-H\xd3\x8fu\xe6\xd9\x1d*\xe5\xc0\xf7+x\x81\x87D\x0e_P\x00\xd4a\x8d\xbe{\x05\x15\x07;3\x82\x1f\x18p\x92\xdadT\xce\xb1\x85>i\x15\xf8Fj\x04\x96s\x0e\xd9\x16/gh\xd4\xf7JJ\xd0Whv'
lock_key2 = b"\xfa\x16\xbb\x11\xad\xae$\x88y\xfeR\xdb%C\xe5<\xf4E\xd3\xd8(\xce\x0b\xf5\xc5`Y=\x97'\x8aYv-\xd0\xc2\xc9\xcdh\xd4Ijy%\x08a@\x14\xb1;j\xa5\x11(\xc1\x8c\xd6\xa9\x0b\x87\x97\x8c/\xf1\x15\x1d\x9a\x95\xc1\x9b\xe1\xc0~\xe9\xa8\x9a\xa7\x86\xc2\xb5T\xbf\x9a\xe7\xd9#\xd1U\x908(\xd1\xd9l\xa1f^N\xe10\x9c\xfe\xd9q\x9f\xe2\xa5\xe2\x0c\x9b\xb4Ge8*F\x89\xa9\x82yzvx\xc2c\xb1&\xdf\xda)m>b\xe0\x96\x124\xbf9\xa6?\x89^\xf1m\x0e\xe3l(\xa1\x1e \x1d\xcb\xc2\x03?A\x07\x84\x0f\x14\x05e\x1b(a\xc9\xc5\xe7,\x8eF6\x08\xdc\xf3\xa8\x8d\xfe\xbe\xf2\xebq\xff\xa0\xd0;u\x06\x8c~\x87xsM\xd0\xbe\x82\xbe\xdb\xc2FA+\x8c\xfa0\x7fp\xf0\xa7T\x862\x95\xaa[h\x13\x0b\xe6\xfc\xf5\xca\xbe}\x9f\x89\x8aA\x1b\xfd\xb8Oh\xf6r{\x14\x99\xcd\xd3\r\xf0D:\xb4\xa6fS3\x0b\xcb\xa1\x10"






POWER_LIST = (pyb.Pin.cpu.C0,pyb.Pin.cpu.C1,pyb.Pin.cpu.C2,pyb.Pin.cpu.C3,pyb.Pin.cpu.A4,pyb.Pin.cpu.B9)

#################################
####  functions
def encrypt_add(dat,key_index):
    if isinstance(key_index,bytes):
        key_index = key_index[0]
    return bytes([i^lock_key1[key_index]^lock_key2[key_index] for i in dat])
    
def crc_add(dat):
    return struct.pack(">H",sum(dat)) # low 2 bytes




class MicropyLOCK(object):
    FIFO = 0
    STA = {'open':1,'close':2,'unnormal':3,'cover_open':4}

    order_list = bytes([0x10,0x11])
    reply_status     = 0x90
    operate_confirm  = 0x91
    can_timeout_ms = 200
    def __init__(self, can_port, pinlist):

        ##############
        # hardware port
        self.p = [pyb.Pin(pin_name, pyb.Pin.OUT_PP) for pin_name in pinlist]
        self.can = can_port

        ##############
        # status
        self.N_lock = 12 # num of locks
        self.ws = [0]*self.N_lock # banshou status
        self.ls = [0]*self.N_lock # lock status
        self.lock_status=[1]*self.N_lock
        self.lose_lock = [10]*self.N_lock

        ##############
        # dat
        self.rx_dat = []
        self.tx_dat = []
        self.rx_dat = 0
        self.random_num = []
        self.current_lock_id = 0

        ##############
        # flag used in other program
        self.lcd_on = False
        self.update_lcd_ls = False

        ###############
        self.check_locks()


    def lock_power_opreate(self,n,mode):
        '''n---channel(1-8)
           mode-on(1) or off(0)
        '''
        try:
            self.p[n].value(not mode)
            return 1
        except:
            print('there is no {}th channel'.format(n))
            return None
    def lock_power_on(self,n=1):
        return self.lock_power_opreate(n,1)
    def lock_power_off(self,n=1):
        return self.lock_power_opreate(n,0)
    def lock_power_status(self,n=1):
        try:
            return self.p[n].value()
        except:
            print('there is no {}th channel'.format(n))
            return None

    def locks_power_opreate(self,mode):
        '''
           mode-on(1) or off(0)
        '''
        for i in self.p:
            i.value(not mode)
        return 1
    def locks_power_on(self):
        return self.locks_power_opreate(n,1)
    def locks_power_off(self):
        return self.locks_power_opreate(n,0)
    def locks_power_status(self):
        out = bytearray()
        for i in range(len(self.p)):
            out.extend(lock_power_status(i+1))
        return out


    def lose_lock_init(self):
        for i in range(self.N_lock):
            self.lose_lock[i] = [5 if self.lock_status[i] else 0][0]
    def update_lock_status(self):
        for i in range(self.N_lock):
            if self.ws[i] == 0:
                self.ls[i] = 0
        self.lock_status = [int(hex(i<<4),16) + j for i,j in zip(self.ws,self.ls)]





    def pack_lock_data(self,dat_type,dat,lock_id,opt = 0x01):
        if isinstance(dat_type,int):
            dat_type = (dat_type).to_bytes(1,'little')
        if isinstance(lock_id,int):
            lock_id = (lock_id).to_bytes(1,'little')
        key_index = os.urandom(1)
        if 0 <= lock_id[0] <= 15:
            length_dat = len(dat)+1
            if length_dat > 255:
                print('data is too long, Please make it less than 255')
                return None
            if dat_type not in MicropyLOCK.order_list:
                print('dat_type is not in the list')
                return None
            data = dat_type + dat
            if (opt & 0x01):
                data = encrypt_add(data, key_index[0])
            tmp_head = lock_id+(length_dat).to_bytes(1,'little') + key_index
            crc_ = crc_add( tmp_head + data)
            tx_buf = tmp_head + data + crc_
            tx_buf = tx_buf.replace(b'\x7d', b'\x7d\x01').replace(b'\x7e',b'\x7d\x02')
            lock_tx_buf = b'~' + tx_buf+ b'~'
            #return lock_tx_buf
            return self.split_by_n(lock_tx_buf)
        else:
            print('The lock id is not in the list')
    def split_by_n(self,dat,n=8):
        if isinstance(dat,bytes):
            dat = [i for i in dat]
        out_n = len(dat[::n])
        out = [bytearray(n)]*out_n
        for i in range(out_n):
            try:
                out[i] = bytearray(dat[i*n:i*n+n])
            except:
                out[i] = bytearray(dat[i*n:])
        #tx_dat = out
        self.tx_dat = out
        return 1
    def opreate_lock_frame(self,lock_id,random_num,order):
        '''order 0-check lock   1-open lock   2-close lock'''
        if order == 0:
            tmp1 = os.urandom(6)
            comm = MicropyLOCK.order_list[0:1]
        elif order in [1,2]:
            tmp1 = (order).to_bytes(1,'little')+ bytes(random_num)
            comm = MicropyLOCK.order_list[1:2]
        else:
            print('order is wrong')
            return None
        tmp2 = crc_add(comm + tmp1)
        return self.pack_lock_data(comm,tmp1 + tmp2,lock_id)
    def check_lock_frame(self,lock_id,random_num):
        return self.opreate_lock_frame(lock_id,random_num,0)
    def open_lock_frame(self,lock_id,random_num):
        return self.opreate_lock_frame(lock_id,random_num,1)
    def close_lock_frame(self,lock_id,random_num):
        return self.opreate_lock_frame(lock_id,random_num,2)





    def send_lock_dat(self):
        host_can_id = 0x7ff
        print('the data will be sent soon is for {}th lock'.format(self.tx_dat[0][1]))
        for i in range(len(self.tx_dat)):
            try:
                self.can.send(self.tx_dat[i], host_can_id)
            except:
                continue
        self.lose_lock[self.tx_dat[0][1]] -= 1
        self.current_lock_id = self.tx_dat[0][1]
        return 1

    def rec_lock_dat(self,lock_id = 100,timeover=0):

        flag = 0
        rx_buf = []
        if lock_id == 100:
            lock_id = self.current_lock_id
        if timeover == 0 :
            time_tmp = MicropyLOCK.can_timeout_ms
        else:
            time_tmp = timeover
        while True:
            try:
                tmp = self.can.recv(0,timeout=time_tmp)
            except:
                return None
            #print('recv1 can data is ()'format(tmp))
            if tmp[3][0] == 126 and flag == 0:
                rx_buf.extend([tmp])
                flag = 1
                continue
            if tmp[3][-1] == 126 and flag == 1:
                rx_buf.extend([tmp])
                flag = 2
                break
            if 126 not in tmp[3] and flag == 1:
                rx_buf.extend([tmp])
                flag = 2
                continue
            if tmp[3][-1] == 126 and flag == 2:
                rx_buf.extend([tmp])
                flag = 3
                break
            print('can bus data frame is wrong flag= {} dat is {}'.format(flag,tmp))
            return None
        if flag == 2:
            d1 = rx_buf[0][3]+rx_buf[1][3]
        if flag == 3 :
            d1 = rx_buf[0][3]+rx_buf[1][3]+rx_buf[2][3]
        #pp = [i for i in d1]
        return self.unpack_lock_data(d1,lock_id)
    def unpack_lock_data(self,dat,lock_id=0,opt=0x01):
        print('unpack_lock_data function')
        tmp = dat
        if tmp[0] == 126 and tmp[-1] ==126:
            if 0x7d in tmp:
                tmp = tmp.replace(b'\x7d\x01',b'\x7d').replace(b'\x7d\x02',b'\x7e')
            tmp = tmp[1:-1]
            tmp_id = tmp[0]
            #print('tmp_id {}'.format(tmp_id))
            tmp_length_dat = tmp[1]
            tmp_key_ind = tmp[2]
            tmp_dat_type = tmp[3:4]
            tmp_dat = tmp[4:-2]
            tmpcrc_add = tmp[-2:]
            crc_add_frame = crc_add(tmp[:-2])
            if tmpcrc_add == crc_add_frame:
                length_dat = tmp_length_dat
                if (opt & 0x01):
                    d = encrypt_add(tmp_dat_type+tmp_dat, tmp_key_ind)
                else:
                    d = tmp_dat_type+tmp_dat
                tmp3 = d[-2:]
                dcrc_add = crc_add(d[:-2])
                
                if tmp3 == dcrc_add:
                    dat_type = d[0]
                    rec_order_type = dat_type
                    if tmp_id in [i for i in range(self.N_lock)]:
                        current_ls = d[1] & 0x0f
                        current_ws = (d[1] & 0xf0)>>4
                        self.lose_lock[tmp_id] += 1
                        print('the {}th lock,  lock_status is {}, current_ws is {}'.format(tmp_id,current_ls,current_ws))

                        if current_ls == 4:
                            locks_power_off()
                            self.lcd_on = True
                            #lcd_lock['s_a']()
                        if current_ls != self.ls[tmp_id] or current_ws != self.ws[tmp_id]:
                            self.lcd_on = True
                            self.update_lcd_ls = True
                            #lcd_lock['s_a']()
                        self.ls[tmp_id] = current_ls
                        self.ws[tmp_id] = current_ws

                        '''
                        if tmp_id < 8:
                            lcd_lock['update_li'](tmp_id,current_ws,current_ls)
                        '''
                    self.rx_dat = d[1]
                    self.random_num = d[2:7]
                    return 1
                    #return rx_dat,random_num
                    #return d[1:7]
                else:
                    print('data crc_add is wrong')
                    return None
            else:
                print ('crc_add error')
                return None
            #self.lock_timeout[tmp_id] = ticks_ms()
        else: 
            print('data is not one frame')
            return None





    def opteate_lock(self,lock_id,order,n = 1):
        '''
        order = 0---check
                1---open
                2---close
        '''
        frame_type_dict = {2:self.close_lock_frame,1:self.open_lock_frame,0:self.check_lock_frame}
        for i in range(n):
            if frame_type_dict[order](lock_id,self.random_num):
                if self.send_lock_dat():
                    if  self.lose_lock[lock_id] <= 0:
                        print('the {}th lock has losed for 5 times'.format(lock_id))
                        self.ls[lock_id] = 5
                        #lcd_lock['update_li'](lock_id,self.ws[lock_id],self.ls[lock_id])
                    return self.rec_lock_dat(lock_id)

    def check_lock(self,lock_id=0):
        return self.opteate_lock(lock_id,0)
    def open_lock(self,lock_id=0):
        return self.opteate_lock(lock_id,1)
    def close_lock(self,lock_id=0):
        return self.opteate_lock(lock_id,2)





    def clear_fifo(self):
        if self.can.any(0):
            while self.can.any(0):
                self.rec_lock_dat()
        return 1
    def opteate_locks(self,order):
        self.clear_fifo()
        order_dict = {'check':self.check_lock,'open':self.open_lock,'close':self.close_lock}
        for i in range(self.N_lock):
            if not self.lock_status[i]:
                continue
            else:
                order_dict[order](i)
        return 1

    
    def check_locks(self):
        self.opteate_locks('check')
        self.update_lock_status()
        return 1
    def open_locks(self):
        return self.opteate_locks('open')
    def close_locks(self):
        return self.opteate_locks('close')

