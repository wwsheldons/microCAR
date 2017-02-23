import os,GLPATH = '/sd/log/'PX = '.txt'US = 'using_times'IP = 'ip'PORT = 'port'APN = 'apn'ID = 'id'PWD = 'passwd'AP = 'admin_phone'EOC = 'emergency_open_card'ECC = 'emergency_close_card'GI = 'gas_info'SR = 'swipe_record'SMS = 'sms_record'PDR = 'power_down_record'LOR = 'lock_open_record'COR = 'control_open_record'POS = 'pos_record'LS = 'lock_status'FN = [US,IP,PORT,APN,ID,PWD,AP,EOC,ECC,GI,SR,SMS,PDR,LOR,COR,POS,LS]def change(n):    n = n/100    n_int = int(n)    n_xiaoshu = (n-int(n))*100/60    return (n_int+n_xiaoshu)* 3.1415926 / 180.0def haversine(lon1, lat1, lon2, lat2):    '''    Calculate the great circle distance between two points    on the earth (specified in decimal degrees)    '''    radlat1 = change(lat1)    radlat2 = lat2* 3.1415926 / 180.0    a = change(lat1) - lat2* 3.1415926 / 180.0    b = change(lon1) - lon2* 3.1415926 / 180.0        from math import cos, sin, sqrt,asin    s = 2 * asin(sqrt((sin(a/2))**2 + cos(radlat1)*cos(radlat2)*(sin(b/2))**2))    return s * 6378137class MicropySTORAGE(object):    def __init__(self):                self.usfn     = PATH + US +PX        self.ipfn     = PATH + IP +PX        self.portfn   = PATH + APN +PX        self.apnfn    = PATH + ID +PX        self.idfn     = PATH + ID +PX        self.pwdfn    = PATH + PWD +PX        self.apfn     = PATH + AP +PX        self.eocfn    = PATH + EOC +PX        self.eccfn    = PATH + ECC +PX        self.gifn     = PATH + GI +PX        self.srfn     = PATH + SR +PX        self.smsfn    = PATH + SMS +PX        self.pdrfn    = PATH + PDR +PX        self.lorfn    = PATH + LOR +PX        self.corfn    = PATH + COR +PX        self.posfn    = PATH + POS +PX        self.lsfn     = PATH + LS +PX        self.load_sys_variable()        '''        self.path     = '/sd/log/'        self.usfn     = self.path + 'using_times.txt'        self.ipfn     = self.path + 'ip.txt'        self.portfn   = self.path + 'port.txt'        self.apnfn    = self.path + 'apn.txt'        self.idfn     = self.path + 'id.txt'        self.pwdfn    = self.path + 'passwd.txt'        self.apfn     = self.path + 'admin_phone.txt'        self.eocfn    = self.path + 'emergency_open_card.txt'        self.eccfn    = self.path + 'emergency_close_card.txt'        self.gifn     = self.path + 'gas_info.txt'        self.srfn     = self.path + 'swipe_record.txt'        self.smsfn    = self.path + 'sms_record.txt'        self.pdrfn    = self.path + 'power_down_record.txt'        self.lorfn    = self.path + 'lock_open_record.txt'        self.corfn    = self.path + 'control_open_record.txt'        self.posfn    = self.path + 'pos_record.txt'        self.lsfn     = self.path + 'lock_status.txt'        '''            def load_sys_variable(self):        try:            GL.id = self.get_info(PATH+ID+PX).decode()            GL.ip = self.get_info(PATH+IP+PX).decode()            GL.port = int(self.get_info(PATH+PORT+PX))            GL.set_phone = self.get_infos(PATH+AP+PX)            GL.pwd = self.get_info(PATH+PWD+PX).decode()            if len(GL.pwd) != 6:                GL.pwd = '123456'            GL.debug_print('load_sys_variable finished')            return 1        except:            GL.debug_print('load_sys_variable failed')            return None        #self.load_emergency_variable()        def card_in_low(self):        speed_kmh = int(bytes(GL.gnss_buf[42:45]).decode())        if speed_kmh > 30:            print('the speed_kmh is over 30 Kmh')            return -2 # speed is over 30kmh        try:            n_gas_info = self.get_rows(PATH+GI+PX)            lat1 = float(bytes(GL.gnss_buf[18:27]).decode())            lon1 = float(bytes(GL.gnss_buf[28:38]).decode())            for i in range(n_gas_info):                gas_info  = self.get_info(PATH+GI+PX,i)                ####################################################                # gas_num              --- gas_info.decode()[:6]                # ic_open              --- gas_info.decode()[6:14]                # ic_close             --- gas_info.decode()[14:22]                # gas_latitude         --- float(gas_info.decode()[24:33])                # gas_longitude        --- float(gas_info.decode()[33:43])                # distance             --- float(gas_info.decode()[43:47])                # ic_using_times       --- int(gas_info.decode()[22:24])                # oprerate_lock_status --- gas_info.decode()[47:]                if GL.ic_id == gas_info.decode()[6:14]:                    tmp_dis = haversine(lat1,lon1,float(gas_info.decode()[24:33]),float(gas_info.decode()[33:43]))                    if tmp_dis < float(gas_info.decode()[43:47]):                        ic_using_times = int(gas_info.decode()[22:24])-1                        self.del_rows(PATH+GI+PX,i)                        if ic_using_times > 0:                            gas_info = bytearray(gas_info)                            gas_info[22:24] = '{:0>2}'.format(ic_using_times).encode()                            self.modify_info(PATH+GI+PX,bytes(gas_info),'add')                        return 1 #can open                    else:                        GL.ERROR[1] = 1                        GL.lcd_update(9)                        # update_err(2) #out of gas station range                        return 0 # out of gas station range                if GL.ic_id == gas_info.decode()[14:22]:                    return 2 # can close            for i,card in enumerate(_get_infos(PATH+EOC+PX,1)):                # emergency open                if GL.ic_id == card[:6]:                    ic_using_times = int(card[6:8])-1                    self.del_rows(PATH+EOC+PX,i)                    if ic_using_times > 0:                        card = bytearray(card)                        card[6:8] = '{:0>2}'.format(ic_using_times).encode()                        self.modify_info(PATH+EOC+PX,bytes(card),'add')                    return 3 # can emergency open            for i,card in enumerate(_get_infos(PATH+ECC+PX,1)):                # emergency close                if GL.ic_id in card:                    return 4 # can emergency close                                GL.ERROR[0] = 1            GL.lcd_update(9)            #update_err(1)  # invalid card            return -1 # invalid card        except:            GL.ERROR[0] = 1            GL.lcd_update(9)            return -1 # invalid card        def prepare(self):        all_file = os.listdir('/sd')        if 'log' in all_file:            log_file = os.listdir('/sd/log')            for i in log_file:                os.remove('/sd/log/'+i)            os.rmdir('log')                os.mkdir('/sd/log')        #os.mkdir('/sd/log/pos_record')        self.prepare_file()        return True    def prepare_file(self):        for fn in FN:            filename = PATH+fn+PX            if self.modify_info(filename,''):                continue            else:                print('create {} caused error'.format(filename))        return 1        '''        self.modify_using_times(0)        self.modify_ip('')        self.modify_port(0)        self.modify_ls(0)        self.modify_id('')        self.modify_pwd('')        self.modify_adimin_phone('')        self.modify_emergency_open_card('')        self.modify_emergency_close_card('')        self.modify_gas_info('')        self.modify_swipe_record('')        self.modify_sms_record('')        self.modify_power_down_record('')        self.modify_lock_open_record('')        self.modify_control_open_record('')        self.modify_pos_record('')        '''    def write_line_to_file(self,filename,dat,mode):        try:            with open(filename, mode) as f:                f.write(dat)                if dat:                    try:                        f.write('\r\n')                    except:                        f.write(b'\r\n')                f.close()                #pyb.sync()                #pyb.delay(50)                return 1        except OSError as error:            print("Error: can not write to SD card. {} and filename = {} dat = {}".format(error,filename,dat))            return None            def modify_info(self,filename,dat,opt = 'rewrite'):        if opt == 'add':            mode = 'a'        elif opt == 'rewrite':            mode = 'wb'        else:            print('wrong type for writing')            return None        if isinstance(dat,str):            dat = dat.encode()        if isinstance(dat,bytearray):            dat = bytes(dat)        elif isinstance(dat,int):            #dat = ((dat).to_bytes(4, "little"))            dat = str(dat).encode()        elif isinstance(dat,bytes):            pass        else:            print('{} wrong data type'.format(filename))            return None        n = self.get_rows(filename)        for i in range(n):            if dat == self.get_info(filename,i):                GL.debug_print('the repeat data {} will not be saved into {}'.format(dat,filename))                return 1        if filename == PATH+GI+PX:            if dat:                if len(dat) != 59:                    print('the data is invalid {}'.format(dat))                    return None                for i in range(59):                    if 48<= dat[i]<=122 or dat[i] == b'.'[0]:# b'0' --- b'z'                        continue                    else:                        print('the data is invalid {}'.format(dat))                        return None        try:            self.write_line_to_file(filename,dat.decode(),mode)        except:            self.write_line_to_file(filename,dat,mode)        GL.debug_print('the  data {} will be saved into {}'.format(dat,filename))        return 1    def modify_infos(self,filename,dats,opt = 'rewrite'):        for i in range(1,len(dats)):            if len(dats[0]) != len(dats[i]):                print('{} data format is wrong'.format(filename))                return None        n = 0        for i in range(len(dats)):            if i == 0:                mode = opt            else:                mode = 'add'            if self.modify_info(filename,dats[i],mode):                n= n+1        if n == len(dats):            #self.load_sys_variable()            return 1        else:            return None        def read_line_from_file(self,filename):        nth = 0        try:            with open(filename, 'rb') as f:                line = f.readline()                while line:                    yield nth,line                    nth = nth +1                    line = f.readline()                f.close()                yield 0,b''        except OSError as error:            print("Error: can not read to SD card. {} and filename = {}".format(error,filename))            return None    def get_rows(self,filename):        n = 0         for line in self.read_line_from_file(filename):            if not line[1]:                if line[1] in [b'\r\n',b'\r','\r','\r\n']:                    return n-1                return n            n = n+1        return None        def get_info(self,filename,n=0):        for line in self.read_line_from_file(filename):            if line[0] == n:                tmp = line[1]                if tmp == b'':                    return b'0'                if tmp[-2:] == b'\r\n':                    tmp = tmp[:-2]                if tmp[-1:] == b'\r':                    tmp = tmp[:-1]                return tmp        return b'0'    def _get_infos(self,filename,step = 3):        n = self.get_rows(filename)        d,mod = divmod(n,step)        if mod:            all_loops = d+1        else:            all_loops = d        for i in range(all_loops):            tmp = []            if i == d and mod:                s = mod            else:                s = step            for j in range(step):                a = self.get_info(filename,j+i*step).decode()                if a != '0':                    tmp.append(a)            yield s,tmp    def get_infos(self,filename):        n = self.get_rows(filename)        infos = []        if n <= 50:            for i in range(n):                infos.append(self.get_info(filename,i).decode())                #infos.append(get_info(filename,i+1))            if infos == ['0']:                pass            if len(infos) >= 2 and '0' in infos:                del infos[infos.index('0')]            return infos        else:            print('RAM is not enough')            def del_rows(self,filename,row):        # from 0 not 1 row        if isinstance(row,int):            row = [row]        n = self.get_rows(filename)        print('{} has {} rows'.format(filename,n))        for i in range(len(row)):            if row[i] >= n:                print('the {}th row is not exsit'.format(row[i]))                return None        na,su = filename.split('.')        new_filename = na+'_.'+su        try:            with open(new_filename, 'wb') as g:                for i in range(n):                    if i in row:                    #if i+1 in row:                        continue                    g.write(self.get_info(filename,i))                    #g.write(self.get_info(filename,i+1))                    g.write(b'\r\n')            os.remove(filename)            os.rename(new_filename, filename)            self.load_sys_variable()            return 1        except OSError as error:            print("del row acting is failed. %s" % error)            return None                    '''    def del_one_group_emergency_variable(self,n):        return del_rows(PATH+GI+PX,n)    def load_emergency_variable(self):        self.gas_num = []        self.ic_open  = []        self.ic_close = []        self.ic_using_times = []        self.gas_latitude = []        self.gas_longitude = []        self.distance = []        self.oprerate_lock_status = []        self.emergency_close_card = []        self.emergency_open_card = []        try:            self.emergency_open_card,self.emergency_open_card_times = self.get_emergency_open_card()            self.emergency_close_card = self.get_emergency_close_card()        except:            pass        try:            n, gas_info = self.get_gas_info()            self.n_gas = n            for i in range(n):                self.gas_num.extend([gas_info[i][:6]])                self.ic_open.extend([gas_info[i][6:14]])                self.ic_close.extend([gas_info[i][14:22]])                self.ic_using_times.extend([int(gas_info[i][22:24])])                self.gas_latitude.extend([float(gas_info[i][24:33])])                self.gas_longitude.extend([float(gas_info[i][33:43])])                self.distance.extend([int(gas_info[i][43:47])])                self.oprerate_lock_status.extend([[int(j) for j in gas_info[i][47:]]])        except:            pass    def get_using_times(self):        #return int.from_bytes(get_info(usfn),'little') #b'0' ->48        return int(self.get_info(PATH+US+PX),10)    def modify_using_times(self,num = 1):        if num == 0:            return self.modify_info(PATH+US+PX,0)        return self.modify_info(PATH+US+PX,self.get_using_times()+1)        def get_ip(self):        return self.get_info(PATH+IP+PX).decode()    def modify_ip(self,ip):        return self.modify_info(PATH+IP+PX,ip)        def get_port(self):        return int(self.get_info(PATH+PORT+PX))    def modify_port(self,port):        return self.modify_info(PATH+PORT+PX,port)            def get_ls(self):        return int(self.get_info(PATH+LS+PX),10)    def modify_ls(self,ls):        return self.modify_info(PATH+LS+PX,ls)        def get_apn(self):        return int(self.get_info(PATH+APN+PX))    def modify_apn(self,apn):        return self.modify_info(PATH+APN+PX,apn)            def get_id(self):        return self.get_info(PATH+ID+PX).decode()    def modify_id(self,local_id,len_id = 11):        if local_id and len(local_id) != len_id:            print('the corect length of id is {}'.format(len_id))            return None        return self.modify_info(PATH+ID+PX,local_id)            def get_pwd(self):        return self.get_info(PATH+PWD+PX).decode()    def modify_pwd(self,pwd):        return self.modify_info(PATH+PWD+PX,pwd)            def get_adimin_phone(self):        return self.get_infos(PATH+AP+PX)    def modify_adimin_phone(self,ap):        if isinstance(ap,str) or isinstance(ap,bytes) or isinstance(ap,bytearray):            ap = [ap]        elif isinstance(ap,list):            pass        else:            print('the format of adimin phone is wrong')        return self.modify_infos(PATH+AP+PX,ap)            def _get_emergency_open_card(self):        for i in _get_infos(PATH+EOC+PX,1):            yield i[0][:-2],int(i[-2:])    def get_emergency_open_card(self):        tmp_card = self.get_infos(PATH+EOC+PX)        card = [i[:-2] for i in tmp_card]        times = [int(i[-2:]) for i in tmp_card]        return card,times    def modify_emergency_open_card(self,eoc,mode = 'rewrite'):        if isinstance(eoc,str) or isinstance(eoc,bytes) or isinstance(eoc,bytearray):            eoc = [eoc]        elif isinstance(eoc,list):            pass        else:            print('the format of emergency_open_card is wrong')        return self.modify_infos(PATH+EOC+PX,eoc,mode)    def _substruction_for_emergency_open_card(self,n):        for i in range(self.get_rows(PATH+EOC+PX)):            if i == n:                tmp_card = self.get_info(PATH+EOC+PX,i)                card = tmp_card[:-2]                times = int(tmp_card[-2:])                self.del_one_emergency_open_card(n)                return self.modify_info(PATH+EOC+PX,card+'{:0>2}'.format(times-1),'add')        return None    def substruction_for_emergency_open_card(self,n):        card,times = self.get_emergency_open_card()        self.del_one_emergency_open_card(n)        return self.modify_info(PATH+EOC+PX,card[n]+'{:0>2}'.format(times[n]-1),'add')    def del_one_emergency_open_card(self,n):        # from 1 not 0        return self.del_rows(PATH+EOC+PX,n)    def _get_emergency_close_card(self):        for i in _get_infos(PATH+ECC+PX,1):            yield i    def get_emergency_close_card(self):        return self.get_infos(PATH+ECC+PX)    def modify_emergency_close_card(self,ecc):        if isinstance(ecc,str) or isinstance(ecc,bytes) or isinstance(ecc,bytearray):            ecc = [ecc]        elif isinstance(ecc,list):            pass        else:            print('the format of emergency_close_card is wrong')        return self.modify_infos(PATH+ECC+PX,ecc)            def _get_gas_info(self,step = 3):        for i in get_infos(PATH+GI+PX,3):            yield str(step)+''.join(i)    def get_gas_info(self):        return self.get_infos(PATH+GI+PX)    def split_plus(self,d,n):        return [d[i:i+n] for i in range(0,len(d),n)]    def modify_gas_info(self,gi):        if gi == [] or gi == '':            return self.modify_info(PATH+GI+PX,'')        if isinstance(gi,list):            return self.modify_infos(PATH+GI+PX,gi)        order = gi[0]        num_of_gas = int(chr(gi[1]),10)        if order in [48,'0',b'0']:            mode = 'rewrite'        elif order in [49,'1',b'1']:            mode = 'add'        else:            print('write emergency data type is wrong')            return None        gas_data = gi[2:]        if len(gas_data)%59 != 0:            print('length of emergency data is wrong')            return None        return self.modify_infos(PATH+GI+PX,self.split_plus(gas_data,59),mode)    def del_one_gas_info(self,n):        # from 1 not 0        return self.del_rows(PATH+GI+PX,n)    def _get_gas_id(self,step = 3):        tmp = ''        for i in get_infos(PATH+GI+PX,3):            for j in range(step):                tmp.append(i[j][:6])            yield str(step)+''.join(tmp)    def get_gas_id(self):        n = self.get_rows(PATH+GI+PX)        ids = []        for i in range(n):            ids.append(self.get_info(PATH+GI+PX,i)[:6])        return str(n)+''.join([i.decode() for i in ids])        def modify_record(self,info,fn):        ##  lss+gnss_buf+ic_id        if not info:            return self.modify_info(fn,'')        if not isinstance(info,bytearray):            info = bytearray(info)        info[12+53] = 50 #lss(12),gnss_buf 53th (b'1'--realtime,b'2'--no realtime)        return self.modify_info(fn,info,'add')        def get_swipe_record(self):        return self.get_infos(PATH+SR+PX)    def modify_swipe_record(self,sr):        return self.modify_record(sr,PATH+SR+PX)    def del_swipe_record(self,n):        # from 1 not 0        return self.del_rows(PATH+SR+PX,n)        def get_sms_record(self):        return self.get_infos(PATH+SMS+PX)    def modify_sms_record(self,sms):        return self.modify_record(sms,PATH+SMS+PX)    def del_sms_record(self,n):        # from 1 not 0        return self.del_rows(PATH+SMS+PX,n)        ############################################    ############################################        def get_power_down_record(self):        return self.get_info(PATH+PDR+PX)    def modify_power_down_record(self,pdr):        return self.modify_info(PATH+PDR+PX,pdr,'add')    def clear_power_down_record(self):        return self.modify_info(PATH+PDR+PX,'','rewrite')    def get_lock_open_record(self):        return self.get_infos(PATH+LOR+PX)    def modify_lock_open_record(self,lor):        return self.modify_info(PATH+LOR+PX,lor,'add')    def clear_lock_open_record(self):        return self.modify_info(PATH+LOR+PX,'')            def get_control_open_record(self):        return self.get_infos(PATH+COR+PX)    def modify_control_open_record(self,cor):        return self.modify_info(PATH+COR+PX,cor,'add')    def clear_control_open_record(self):        return self.modify_info(PATH+COR+PX,'')        ############################################    ############################################    def get_pos_record(self,n):        if n == 0:            return self.get_rows(PATH+POS+PX)        else:            return self.get_info(PATH+POS+PX,n)    def modify_pos_record(self,pos):        # lss+gnss_buf        if not pos:            return self.modify_info(PATH+POS+PX,'')        if not isinstance(pos,bytearray):            pos = bytearray(pos)        pos[53+12] = 50        return self.modify_info(PATH+POS+PX,pos,'add')    def del_pos_record(self,n):        return self.del_rows(PATH+POS+PX,n)    '''