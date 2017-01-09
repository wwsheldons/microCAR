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



class MicropyGPS(object):
    """GPS NMEA Sentence Parser. Creates object that stores all relevant GPS data and statistics.
    Parses sentences one character at a time using update(). """

    # Max Number of Characters a valid sentence can be (based on GGA sentence)
    SENTENCE_LIMIT = 76
    #__HEMISPHERES.keys() = ('N', 'S', 'E', 'W')
    __HEMISPHERES = {'N':b'1', 'S':b'2', 'E':b'1', 'W':b'2'}
    __NO_FIX = 1
    __FIX_2D = 2
    __FIX_3D = 3
    #__FIELD_LENGTH = (1,8,8,1,9,1,10,4,3,6,2,1,1,1,1,1,1,1,1,1) #the length of each field 
    
    def __init__(self, local_offset=0):
        '''
        Setup GPS Object Status Flags, Internal Data Registers, etc
        '''

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
        # Time
        self.timestamp = (0, 0, 0)
        self.date = (0, 0, 0)
        self.local_offset = local_offset

        # Position/Motion
        self.latitude = ''
        self.longitude = ''
        self.speed = 0
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

        #clear buf
        self.clear_buf()

    def clear_buf(self):
        self.gnss_buf = bytearray('216-06-0320:08:0023447.9072111335.68360123000000.00001111*****', 'utf-8')
        '''
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
            self.gnss_buf[0:1] = self.gps_segments[6].encode()
            
        except ValueError:
            return False

        # Process Location and Speed Data if Fix is GOOD
        if fix_stat:

            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[2]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[3]
                self.gnss_buf[18:27] = '{:0>09}'.format(self.gps_segments[2][:9]).encode()
                self.gnss_buf[27:28] = self.__HEMISPHERES[lat_hemi]
                
                # Longitude
                l_string = self.gps_segments[4]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[5]
                self.gnss_buf[28:38] = '{:0>010}'.format(self.gps_segments[4][:10]).encode()
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
                # Longitude
                l_string = self.gps_segments[5]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[6]
                self.gnss_buf[27:28] = self.__HEMISPHERES[lon_hemi]
                self.gnss_buf[28:38] = '{:>010}'.format(self.gps_segments[5][:10]).encode()

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
            '''
            self.latitude = (0, 0.0, 'N')
            self.longitude = (0, 0.0, 'W')
            self.speed = 0
            self.course = 0.0
            self.date = (0, 0, 0)
            '''
            self.valid = False
        self.update_gnrmc = True
        return True

    def gpgll(self):
        """Parse Geographic Latitude and Longitude (GLL)Sentence. Updates UTC timestamp, latitude,
        longitude, and fix status"""

        # UTC Timestamp
        try:
            utc_string = self.gps_segments[5]

            if utc_string:  # Possible timestamp found
                hours = int(utc_string[0:2]) + self.local_offset
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = (hours, minutes, seconds)
            else:  # No Time stamp yet
                self.timestamp = (0, 0, 0)

        except ValueError:  # Bad Timestamp value present
            return False

        # Check Receiver Data Valid Flag
        if self.gps_segments[6] == 'A':  # Data from Receiver is Valid/Has Fix

            # Longitude / Latitude
            try:
                # Latitude
                l_string = self.gps_segments[1]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[2]

                # Longitude
                l_string = self.gps_segments[3]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[4]
            except ValueError:
                return False

            if lat_hemi not in self.__HEMISPHERES.keys():
                return False

            if lon_hemi not in self.__HEMISPHERES.keys():
                return False

            # Update Object Data
            self.latitude = (lat_degs, lat_mins, lat_hemi)
            self.longitude = (lon_degs, lon_mins, lon_hemi)
            self.valid = True

            # Update Last Fix Time
            self.new_fix_time()

        else:  # Clear Position Data if Sentence is 'Invalid'
            self.latitude = (0, 0.0, 'N')
            self.longitude = (0, 0.0, 'W')
            self.valid = False

        return True

    def gpvtg(self):
        """Parse Track Made Good and Ground Speed (VTG) Sentence. Updates speed and course"""
        try:
            course = float(self.gps_segments[1])
            spd_knt = float(self.gps_segments[5])
        except ValueError:
            return False

        # Include mph and km/h
        self.speed = spd_knt * 1.852
        #self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
        self.course = course
        return True

    

    def gpgsa(self):
        """Parse GNSS DOP and Active Satellites (GSA) sentence. Updates GPS fix type, list of satellites used in
        fix calculation, Position Dilution of Precision (PDOP), Horizontal Dilution of Precision (HDOP), Vertical
        Dilution of Precision, and fix status"""

        # Fix Type (None,2D or 3D)
        try:
            fix_type = int(self.gps_segments[2])
        except ValueError:
            return False

        # Read All (up to 12) Available PRN Satellite Numbers
        sats_used = []
        for sats in range(12):
            sat_number_str = self.gps_segments[3 + sats]
            if sat_number_str:
                try:
                    sat_number = int(sat_number_str)
                    sats_used.append(sat_number)
                except ValueError:
                    return False
            else:
                break

        # PDOP,HDOP,VDOP
        try:
            pdop = float(self.gps_segments[15])
            hdop = float(self.gps_segments[16])
            vdop = float(self.gps_segments[17])
        except ValueError:
            return False

        # Update Object Data
        self.fix_type = fix_type

        # If Fix is GOOD, update fix timestamp
        if fix_type > self.__NO_FIX:
            self.new_fix_time()

        self.satellites_used = sats_used
        self.hdop = hdop
        self.vdop = vdop
        self.pdop = pdop

        return True

    def gpgsv(self):
        """Parse Satellites in View (GSV) sentence. Updates number of SV Sentences,the number of the last SV sentence
        parsed, and data on each satellite present in the sentence"""
        try:
            num_sv_sentences = int(self.gps_segments[1])
            current_sv_sentence = int(self.gps_segments[2])
            sats_in_view = int(self.gps_segments[3])
        except ValueError:
            return False

        # Create a blank dict to store all the satellite data from this sentence in:
        # satellite PRN is key, tuple containing telemetry is value
        satellite_dict = dict()

        # Calculate  Number of Satelites to pull data for and thus how many segment positions to read
        if num_sv_sentences == current_sv_sentence:
            sat_segment_limit = ((sats_in_view % 4) * 4) + 4  # Last sentence may have 1-4 satellites
        else:
            sat_segment_limit = 20  # Non-last sentences have 4 satellites and thus read up to position 20

        # Try to recover data for up to 4 satellites in sentence
        for sats in range(4, sat_segment_limit, 4):

            # If a PRN is present, grab satellite data
            if self.gps_segments[sats]:
                try:
                    sat_id = int(self.gps_segments[sats])
                except ValueError:
                    return False

                try:  # elevation can be null (no value) when not tracking
                    elevation = int(self.gps_segments[sats+1])
                except ValueError:
                    elevation = None

                try:  # azimuth can be null (no value) when not tracking
                    azimuth = int(self.gps_segments[sats+2])
                except ValueError:
                    azimuth = None

                try:  # SNR can be null (no value) when not tracking
                    snr = int(self.gps_segments[sats+3])
                except ValueError:
                    snr = None

            # If no PRN is found, then the sentence has no more satellites to read
            else:
                break

            # Add Satellite Data to Sentence Dict
            satellite_dict[sat_id] = (elevation, azimuth, snr)

        # Update Object Data
        self.total_sv_sentences = num_sv_sentences
        self.last_sv_sentence = current_sv_sentence
        self.satellites_in_view = sats_in_view

        # For a new set of sentences, we either clear out the existing sat data or
        # update it as additional SV sentences are parsed
        if current_sv_sentence == 1:
            self.satellite_data = satellite_dict
        else:
            self.satellite_data.update(satellite_dict)

        return True

    ##########################################
    # Data Stream Handler Functions
    ##########################################

    def new_sentence(self):
        """Adjust Object Flags in Preparation for a New Sentence"""
        self.gps_segments = ['']
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True
        self.char_count = 0

    def update(self, new_char):
        """Process a new input char and updates GPS object if necessary based on special characters ('$', ',', '*')
        Function builds a list of received string that are validate by CRC prior to parsing by the  appropriate
        sentence function. Returns sentence type on successful parse, None otherwise"""

        valid_sentence = False

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
                                return self.gnss_buf
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

    def update_add(self,control_cover,vcc_voltage,battery_voltage):
        if control_cover.read() > 3900:
            self.gnss_buf[54:55] = b'2'
        if GL.control_cover.read() < 300:
            self.gnss_buf[54:55] = b'1'
        if vcc_voltage.read() < 1699: #14V
            #bat_en.value(1)
            self.gnss_buf[56:57] = b'0'
            #lock_gnss['lp_off']()
            #gprs.send_1003()
        else:
            self.gnss_buf[56:57] = b'1'
        
        if vcc_voltage.read() > 2243: #19V
            self.gnss_buf[56:57] = b'1'
            if self.gnss_buf[56:57] == b'0':
                #lock_gnss['lp_ons']()
                GL.lock_status = [1]*12
                #lock_gnss['checks']()
        else:
            self.gnss_buf[56:57] == b'0'
        if battery_voltage.read() < 1216: #10V
            self.gnss_buf[55:56] = b'0'
            #if self.gnss_buf[56:57] == b'0':
                #lock_gnss['lp_offs']()
        if battery_voltage.read() > 1316:
            self.gnss_buf[55:56] = b'1'

    # All the currently supported NMEA sentences
    supported_sentences = {'GNRMC': gnrmc, 'GNGGA': gngga,'GPRMC':gnrmc, 'GPGGA':gngga}
    # supported_sentences_ = {'GNRMC': gnrmc, 'GNGGA': gngga, 'GNVTG': gnvtg, 'GNGSA': gngsa, 'GNGSV': gngsv,'GNGLL': gngll}
    @property
    def speed(self):
        return self.speed


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
                    print(buf)
                else:
                    print(my_gps.gnss_buf)