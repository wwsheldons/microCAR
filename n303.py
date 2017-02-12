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

def int2bcd(a):
    '''int to bcd code'''
    return (a>>4)*10+ (a & 0x0f)
def bcd2int(a):
    '''bcd code to int'''
    return hex(((a / 10)<<4)+(a % 10))



class MicropyGNSS(object):
    """GPS NMEA Sentence Parser. Creates object that stores all relevant GPS data and statistics.
    Parses sentences one character at a time using update(). 

    """

    # Max Number of Characters a valid sentence can be (based on GGA sentence)
    SENTENCE_LIMIT = 76
    #__HEMISPHERES.keys() = ('N', 'S', 'E', 'W')
    __HEMISPHERES = {'N':b'1', 'S':b'2', 'E':b'1', 'W':b'2'}
    #__FIELD_LENGTH = (1,8,8,1,9,1,10,4,3,6,2,1,1,1,1,1,1,1,1,1) #the length of each field 
    
    def __init__(self, gnss_port,pins,local_offset=0):
        '''
        Setup GPS Object Status Flags, Internal Data Registers, etc
        '''
        self.gnss_port = gnss_port
        self.gnss_reset = pins[0]
        self.gnss_reset.low()
        self.battery_voltage = pins[1]
        self.vcc_voltage = pins[2]
        self.control_cover = pins[3]
        #####################
        # Object Status Flags
        self.sentence_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gps_segments = []
        self.crc_xor = 0
        self.char_count = 0
        self.fix_time = 0

        #####################
        # Sentence Statistics
        self.crc_fails = 0
        self.clean_sentences = 0
        self.parsed_sentences = 0

        #####################
        # Logging Related
        self.log_handle = None
        self.log_en = False

        #####################
        # Data From Sentences
        self.local_offset = local_offset

        # Position/Motion
        self.speed_kmh = 0
        self.latitude = 0.0
        self.longitude = 0.0
        
        self.course = ''
        self.altitude = ''
        self.geoid_height = ''

        # GPS Info
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used = []
        self.last_sv_sentence = 0
        self.total_sv_sentences = 0
        self.satellite_data = dict()
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid = False
        self.fix_stat = 0
        self.fix_type = 1

        # update status
        self.update_gnrmc = False
        self.update_gngga = False

        # flag bit for other thread
        self.vcc_below_14V = False
        self.vcc_over_19V = False
        self.battery_below_10V = False


        # clear buf
        self.clear_buf()

    def clear_buf(self):
        try:
            self.gnss_buf = bytearray('216-06-0320:08:0023447.9072111335.68360123000000.00001111*****', 'utf-8')
        except:
            self.gnss_buf = bytearray('216-06-0320:08:0023447.9072111335.68360123000000.00001111*****')
        '''
        #length of gnss_buf is 62
        self.gnss_buf = ['0']*20
        self.gnss_buf[0] = '2' # 2-invalid 1-valid
        self.gnss_buf[1] = '16-06-03' # date
        self.gnss_buf[2] = '20:08:00' # time
        self.gnss_buf[3] = '2' # 1--S 2--N
        self.gnss_buf[4] = '3447.9072' # Latitude
        self.gnss_buf[5] = '1' # 1-E 2-W
        self.gnss_buf[6] = '11335.6836' # Longitude
        self.gnss_buf[7] = '0123' # altitude
        self.gnss_buf[8] = '000' # speed Km/h
        self.gnss_buf[9] = '000.00' # course
        self.gnss_buf[10] = '00' # num of satellite
        self.gnss_buf[11] = '1' # runtime data-1 not runtime data-2
        self.gnss_buf[12] = '1' # control_cover 1- close 2-open
        self.gnss_buf[13] = '1' # lock power 0-power off 1-power on
        self.gnss_buf[14] = '1' # main power 0-power off 1-power on
        self.gnss_buf[15] = '*' # reserve 1
        self.gnss_buf[16] = '*' # reserve 2
        self.gnss_buf[17] = '*' # reserve 3
        self.gnss_buf[18] = '*' # reserve 4
        self.gnss_buf[19] = '*' # reserve 5
        '''
        
    ########################################
    # Logging Related Functions
    ########################################
    def start_logging(self, target_file, mode="append"):
        """
        Create GPS data log object
        """
        if mode == 'new':
            mode_code = 'w'
        else:
            mode_code = 'a'
        try:
            self.log_handle = open(target_file, mode_code)
        except AttributeError:
            print("Invalid FileName")
            return False

        self.log_en = True
        return True

    def stop_logging(self):
        """
        Closes the log file handler and disables further logging
        """
        try:
            self.log_handle.close()
        except AttributeError:
            print("Invalid Handle")
            return False

        self.log_en = False
        return True

    def write_log(self, log_string):
        """Attempts to write the last valid NMEA sentence character to the active file handler
        """
        try:
            self.log_handle.write(log_string)
        except TypeError:
            return False
        return True

    ########################################
    # Sentence Parsers
    ########################################

    def gngga(self):
        """Parse Global Positioning System Fix Data (GGA) Sentence. Updates UTC timestamp, latitude, longitude,
        fix status, satellites in use, Horizontal Dilution of Precision (HDOP), altitude, geoid height and fix status"""
        self.update_gngga = False
        try:
            # UTC Timestamp
            utc_string = self.gps_segments[1]

            # Skip timestamp if receiver doesn't have on yet
            if utc_string:
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.gnss_buf[9:17] = (utc_string[0:2]+':'+utc_string[2:4]+':'+utc_string[4:6]).encode()
                
            '''
            else:
                
                hours = 0
                minutes = 0
                seconds = 0.0
                '''
            # Number of Satellites in Use
            satellites_in_use = int(self.gps_segments[7])
            self.gnss_buf[51:53] = self.gps_segments[7].encode()
            # Horizontal Dilution of Precision
            hdop = float(self.gps_segments[8])

            # Get Fix Status
            fix_stat = int(self.gps_segments[6])
            #self.gnss_buf[0:1] = self.gps_segments[6].encode()
            
        except ValueError:
            return False

        # Process Location and Speed Data if Fix is GOOD
        if fix_stat:
            # Longitude / Latitude
            self.gnss_buf[0:1] = b'1'
            try:
                # Latitude
                l_string = self.gps_segments[2]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[3]
                self.gnss_buf[18:27] = '{:0>09}'.format(self.gps_segments[2][:9]).encode()
                self.gnss_buf[27:28] = self.__HEMISPHERES[lat_hemi]
                self.latitude = float(bytes(self.gnss_buf[18:27]).decode())
                # Longitude
                l_string = self.gps_segments[4]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[5]
                self.gnss_buf[28:38] = '{:0>010}'.format(self.gps_segments[4][:10]).encode()
                self.longitude = float(bytes(self.gnss_buf[28:38]).decode())
                self.gnss_buf[27:28] = self.__HEMISPHERES[lon_hemi]
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES.keys():
                return False

            if lon_hemi not in self.__HEMISPHERES.keys():
                return False

            # Altitude / Height Above Geoid
            try:
                altitude = float(self.gps_segments[9])
                self.gnss_buf[38:42] = ('{:0>4}'.format(int(altitude))).encode()
                geoid_height = float(self.gps_segments[11])
            except ValueError:
                return False

            # Update Object Data
            '''
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            self.altitude = altitude
            self.geoid_height = geoid_height
            '''
        else:
            self.gnss_buf[0:1] = b'2'
        # Update Object Data
        '''
        self.timestamp = (hours, minutes, seconds)
        self.satellites_in_use = satellites_in_use
        self.fix_stat = fix_stat
        '''
        self.hdop = hdop
        

        # If Fix is GOOD, update fix timestamp
        if fix_stat:
            self.new_fix_time()
        self.update_gngga = True
        return True

    def gnrmc(self):
        """Parse Recommended Minimum Specific GPS/Transit data (RMC)Sentence. Updates UTC timestamp, latitude,
        longitude, Course, Speed, Date, and fix status"""
        self.update_gnrmc = False
        # UTC Timestamp
        try:
            utc_string = self.gps_segments[1]

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
            date_string = self.gps_segments[9]

            # Date string printer function assumes to be year >=2000,
            # date_string() must be supplied with the correct century argument to display correctly
            if date_string:  # Possible date stamp found
                day = int(date_string[0:2])
                month = int(date_string[2:4])
                year = int(date_string[4:6])
                self.date = (day, month, year)
                self.gnss_buf[1:9] = (date_string[4:6]+'-'+date_string[2:4]+'-'+date_string[0:2]).encode()
            '''
            else:  # No Date stamp yet
                self.date = (0, 0, 0)
            '''
        except ValueError:  # Bad Date stamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[2] == 'A':  # Data from Receiver is Valid/Has Fix
            self.gnss_buf[0:1] = b'1'
            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[3]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[4]
                self.gnss_buf[17:18] = self.__HEMISPHERES[lat_hemi]
                self.gnss_buf[18:27] = '{:>09}'.format(self.gps_segments[3][:9]).encode()
                #print(self.gnss_buf[18:27])
                self.latitude = float(bytes(self.gnss_buf[18:27]).decode())
                # Longitude
                l_string = self.gps_segments[5]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[6]
                self.gnss_buf[27:28] = self.__HEMISPHERES[lon_hemi]
                self.gnss_buf[28:38] = '{:>010}'.format(self.gps_segments[5][:10]).encode()
                self.longitude = float(bytes(self.gnss_buf[28:38]).decode())
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES.keys():
                return False

            if lon_hemi not in self.__HEMISPHERES.keys():
                return False

            # Speed
            try:
                spd_knt = float(self.gps_segments[7])
            except ValueError:
                return False

            # Course
            try:
                course = float(self.gps_segments[8])
            except ValueError:
                return False

            # TODO - Add Magnetic Variation

            # Update Object Data
            '''
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            '''
            # Include mph and hm/h
            #self.speed_kmh = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
            self.speed_kmh = spd_knt * 1.852
            self.gnss_buf[42:45] = ('{:>03}'.format(int(self.speed_kmh))).encode()

            self.course = course
            self.gnss_buf[45:51] = ('%06.2f'%course).encode()

            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'

            self.gnss_buf[0:1] = b'2'

            '''
            self.latitude = (0, 0.0, 'N')
            self.longitude = (0, 0.0, 'W')
            self.speed_kmh = 0
            self.course = 0.0
            self.date = (0, 0, 0)
            '''
            self.valid = False
        self.update_gnrmc = True
        return True


    ##########################################
    # Data Stream Handler Functions
    ##########################################
    def update_voltage(self):
        if self.control_cover.read() > 3900:
            self.gnss_buf[54:55] = b'2'
        if self.control_cover.read() < 300:
            self.gnss_buf[54:55] = b'1'
        if self.vcc_voltage.read() < 1699: #14V
            #bat_en.value(1)
            self.gnss_buf[56:57] = b'0'
            self.vcc_below_14V = True
            #lock_gnss['lp_off']()
            #gprs.send_1003()
        else:
            self.gnss_buf[56:57] = b'1'
        
        if self.vcc_voltage.read() > 2243: #19V
            self.gnss_buf[56:57] = b'1'
            if self.gnss_buf[56:57] == b'0':
                self.vcc_over_19V = True
                #lock_gnss['lp_ons']()
                #self.lock_status = [1]*12
                #lock_gnss['checks']()
        else:
            self.gnss_buf[56:57] == b'0'
        if self.battery_voltage.read() < 1216: #10V
            self.gnss_buf[55:56] = b'0'
            if self.gnss_buf[56:57] == b'0':
                #lock_gnss['lp_offs']()
                self.battery_below_10V = True
        if self.battery_voltage.read() > 1316:
            self.gnss_buf[55:56] = b'1'
    def new_sentence(self):
        """Adjust Object Flags in Preparation for a New Sentence"""
        self.gps_segments = ['']
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True
        self.char_count = 0

    def update(self, new_char = 0):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_sentence = False
        try:
            if self.gnss_reset.value() == 1:
                print('N303 is Invalid, Please make the gnss_reset low')
                return None
            tmp = self.gnss_port.readchar()
            if tmp < 0 :
                #print('N303 is Invalid')
                return None
            new_char = chr(tmp)
        except:
            pass
        # Validate new_char is a printable char
        ascii_char = ord(new_char)

        if 10 <= ascii_char <= 126:
            self.char_count += 1

            # Write Character to log file if enabled
            if self.log_en:
                self.write_log(new_char)

            # Check if a new string is starting ($)
            if new_char == '$':
                self.new_sentence()
                return None

            elif self.sentence_active:

                # Check if sentence is ending (*)
                if new_char == '*':
                    self.process_crc = False
                    self.active_segment += 1
                    self.gps_segments.append('')
                    return None

                # Check if a section is ended (,), Create a new substring to feed
                # characters to
                elif new_char == ',':
                    self.active_segment += 1
                    self.gps_segments.append('')

                # Store All Other printable character and check CRC when ready
                else:
                    self.gps_segments[self.active_segment] += new_char

                    # When CRC input is disabled, sentence is nearly complete
                    if not self.process_crc:

                        if len(self.gps_segments[self.active_segment]) == 2:
                            try:
                                final_crc = int(self.gps_segments[self.active_segment], 16)
                                if self.crc_xor == final_crc:
                                    valid_sentence = True
                                else:
                                    self.crc_fails += 1
                            except ValueError:
                                pass  # CRC Value was deformed and could not have been correct

                # Update CRC
                if self.process_crc:
                    self.crc_xor ^= ascii_char

                # If a Valid Sentence Was received and it's a supported sentence, then parse it!!
                if valid_sentence:
                    self.clean_sentences += 1  # Increment clean sentences received
                    self.sentence_active = False  # Clear Active Processing Flag

                    if self.gps_segments[0] in self.supported_sentences:

                        # parse the Sentence Based on the message type, return True if parse is clean
                        if self.supported_sentences[self.gps_segments[0]](self):
                            
                            # Let host know that the GPS object was updated by returning parsed sentence type
                            self.parsed_sentences += 1
                            #return self.gps_segments[0]
                            if self.update_gnrmc and self.update_gngga:
                                self.update_gnrmc = self.update_gngga = False
                                #return self.gnss_buf
                                self.update_voltage()
                                return 1
                # Check that the sentence buffer isn't filling up with Garage waiting for the sentence to complete
                if self.char_count > self.SENTENCE_LIMIT:
                    self.sentence_active = False

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

    

    # All the currently supported NMEA sentences
    supported_sentences = {'GNRMC': gnrmc, 'GNGGA': gngga,'GPRMC':gnrmc, 'GPGGA':gngga}
    # supported_sentences_ = {'GNRMC': gnrmc, 'GNGGA': gngga, 'GNVTG': gnvtg, 'GNGSA': gngsa, 'GNGSV': gngsv,'GNGLL': gngll}
    @property
    def speed(self):
        return self.speed_kmh
    @property
    def get_pos(self):
        return (self.latitude,self.longitude)
    @property
    def g(self):
        if self.gnss_buf[0:1] == b'1':
            return 1
        else:
            return 0

def test():
    test_sentence = [b'$GPRMC,081836,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62\n',
                b'$GPGGA,180050.896,3749.1802,N,08338.7865,W,1,07,1.1,397.4,M,-32.5,M,,0000*6C\n'
                b'$GPVTG,232.9,T,,M,002.3,N,004.3,K,A*01\n'
                b'$GPGSV,3,1,12,28,72,355,39,01,52,063,33,17,51,272,44,08,46,184,38*74\n',
                b'$GPGLL,4916.45,N,12311.12,W,225444,A,*1D\n',
                b'$GPRMC,092751.000,A,5321.6802,N,00630.3371,W,0.06,31.66,280511,,,A*45\n']
    my_gps = MicropyGPS()
    for sentence in test_sentence:
        for y in sentence:
            buf = my_gps.update(chr(y))
            if buf:
                print(my_gps.gnss_buf)
        print('my_gps.latitude,my_gps.longitude = {},{}'.format(my_gps.latitude,my_gps.longitude))
        print('my_gps.speed_kmh= {}'.format(my_gps.speed_kmh))

#test()