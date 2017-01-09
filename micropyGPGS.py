#modify by wjy @20170106
from math import floor

# Import pyb or time for fix time handling
try:
    # Assume running on pyboard
    import pyb
except ImportError:
    # Otherwise default to time module for non-embedded implementations
    # Note that this forces the resolution of the fix time 1 second instead
    # of milliseconds as on the pyboard
    import time





class MicropyGPRS(object):
    """GPRS Sentence Parser. Creates object that stores all relevant GPRS data and statistics.
    Include AT order , SMS and data from server.
    Parses sentences one character at a time using update(). """

    # Max Number of Characters a valid sentence can be (based on GGA sentence)
    SENTENCE_LIMIT = 1000
    #__HEMISPHERES.keys() = ('N', 'S', 'E', 'W')
    __HEMISPHERES = {'N':b'1', 'S':b'2', 'E':b'1', 'W':b'2'}
    __NO_FIX = 1
    __FIX_2D = 2
    __FIX_3D = 3
    
    
    def __init__(self, local_offset=0):
        '''
        Setup GPS Object Status Flags, Internal Data Registers, etc
        '''

        #####################
        # Object Status Flags
        self.sentence_data_active = False
        self.sentence_at_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gprs_segments = ['']
        self.crc_xor = 0
        self.char_count = 0
        self.fix_time = 0

        self.just_send_ats = ''
        self.just_send_dats = ''
        self.ats_dict = {}
        #####################
        # buf
        self.tx_buf = ''
        self.id = 'AP9904N0769'
        
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
        if self.char_count <= 1:
            return False
        try:
            at_order = self.gprs_segments[0]
            module_reply = self.gprs_segments[-1]
            # Skip timestamp if receiver doesn't have on yet
            if 'OK' == module_reply:
                self.ats_dict[at_order] = 1
            if 'CSQ' in at_order:
                dat = self.gprs_segments[1]
                ind = dat.index(',')
            
        except ValueError:
            return False



        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()
        self.update_gngga = True
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

    def data(self):
        self.tx_buf = ''
        return 1

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self,opt):
        """Adjust Object Flags in Preparation for a New dat Sentence"""
        if opt == 'AT':
            #self.gprs_segments[0] = 'AT'
            self.active_segment = 0
            #self.crc_xor = 0
            self.sentence_at_active = True
            #self.process_crc = True
            self.char_count = 2
        elif opt == 'data':
            self.active_segment = 0
            #self.gprs_segments[0] = self.id
            self.sentence_data_active = True
        else:
            pass
    
    def update(self, new_char):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_at_sentence = False
        valid_data_sentence = False

        # Validate new_char is a printable char
        ascii_char = ord(new_char)
        
        self.char_count += 1
        self.gprs_segments[self.active_segment] += new_char
        print('gprs_segments is {}'.format(self.gprs_segments))

        # Check if a new string is starting ('AT')
        if new_char == 'T' and self.gprs_segments[self.active_segment][-2] == 'A':
            self.new_sentence('AT')
            return None

        if self.sentence_at_active:
            # Validate new_char is a printable char
            if 10<= ascii_char <126:
                #print('new_char is {}'.format(new_char))
                # Check if sentence is ending ('\r\n' over three times or '>'(AT+CIPSEND=109,1))
                #print('self.gprs_segments[self.active_segment][-1]={}'.format(self.gprs_segments[self.active_segment][-1]))

                if (new_char == '\n') and (self.gprs_segments[self.active_segment][-2] == '\r'):
                    #self.process_crc = False
                    self.gprs_segments[self.active_segment] = self.gprs_segments[self.active_segment][:-2]
                    self.active_segment += 1
                    self.gprs_segments.append('')
                    if ('OK' or 'ERROR') in self.gprs_segments[self.active_segment-1] or self.active_segment > 4:
                        valid_at_sentence = True
                    
                if new_char == '>':
                    valid_at_sentence = True

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_at_sentence:
                    self.gprs_segments = [i for i in self.gprs_segments if i != '']
                    #self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_at_active = False  # Clear Active Processing Flag
                    #self.parsed_sentences += 1
                    print('self.gprs_segments is {}'.format(self.gprs_segments))
                    #return self.at()

                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_at_active = False

        if self.char_count == 11 and self.gprs_segments[0][:11] == self.id:
            
            self.new_sentence('data')
            return None
        if self.sentence_data_active:
            #if self.char_count == len(self.tx_buf):
            if self.gprs_segments[0] == self.tx_buf:
                valid_data_sentence = True

            # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
            if valid_data_sentence:

                #self.clean_sentences += 1  # Increment clean sentences received
                self.sentence_data_active = False  # Clear Active Processing Flag
                #self.parsed_sentences += 1
                #print('self.gprs_segments is {}'.format(self.gprs_segments))
                #print('self.tx_buf is        {}'.format(self.tx_buf))
                return self.data()

            # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
            if self.char_count > self.SENTENCE_LIMIT:
                self.sentence_data_active = False
        # Tell Host no new sentence was parsed
        return None

    def new_fix_time(self):
        """Updates a high resolution counter with current time when fix is updated. Currently only triggered from
        GGA, GSA and RMC sentences"""
        try:
            self.fix_time = pyb.millis()
        except NameError:
            self.fix_time = time.time()

    # All the currently supported NMEA sentences
    #supported_sentences = {'GNRMC': gnrmc, 'GNGGA': gngga,'GPRMC':gnrmc, 'GPGGA':gngga}
    # supported_sentences_ = {'GNRMC': gnrmc, 'GNGGA': gngga, 'GNVTG': gnvtg, 'GNGSA': gngsa, 'GNGSV': gngsv,'GNGLL': gngll}
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
    for sentence in test_sentence:
        for y in sentence:
            buf = my_gps.update(chr(y))
            if buf:
                print(buf)
            else:
                print(my_gps.gnss_buf)

aa = b'AT+CMGF=1\r\n\r\nOK\r\n'
my_gprs = MicropyGPRS()
my_gprs.tx_buf = aa.decode()
for y in aa:
    buf = my_gprs.update(chr(y))
    if buf:
        print(my_gprs.gprs_segments[0])