import pyb
from usched import Timeout, Roundrobin

# **************************************************** LCD DRIVER ***************************************************


# *********************************** GLOBAL CONSTANTS: MICROPYTHON PIN NUMBERS *************************************

# Supply as board pin numbers as a tuple CS DIO CLK POW A RST

PINLIST = (pyb.Pin.cpu.B15,pyb.Pin.cpu.B14,pyb.Pin.cpu.A7,pyb.Pin.cpu.C4,pyb.Pin.cpu.C5,pyb.Pin.cpu.A6)

# **************************************************** LCD CLASS ****************************************************
# Initstring:
# 0x33, 0x32: See flowchart P24 send 3,3,3,2
# 0x28: Function set DL = 1 (4 bit) N = 1 (2 lines) F = 0 (5*8 bit font)
# 0x0C: Display on/off: D = 1 display on C, B = 0 cursor off, blink off
# 0x06: Entry mode set: ID = 1 increment S = 0 display shift??
# 0x01: Clear display, set DDRAM address = 0
# Original code had timing delays of 50uS. Testing with the Pi indicates that time.sleep() can't issue delays shorter
# than about 250uS. There also seems to be an error in the original code in that the datasheet specifies a delay of
# >4.1mS after the first 3 is sent. To simplify I've imposed a delay of 5mS after each initialisation pulse: the time to
# initialise is hardly critical. The original code worked, but I'm happier with something that complies with the spec.

# Threaded version:
# No point in having a message queue: people's eyes aren't that quick. Just display the most recent data for each line.
# Assigning changed data to the LCD object sets a "dirty" flag for that line. The LCD's runlcd thread then updates the
# hardware and clears the flag

# Note that the lcd_nybble method uses explicit delays rather than yields. This is for two reasons.
# The delays are short in the context of general runtimes and minimum likely yield delays, so won't
# significantly impact performance. Secondly, using yield produced perceptibly slow updates to the display text.

class LCD(object):                                          # LCD objects appear as read/write lists
    INITSTRING = (0x30, 0x01, 0x06, 0x0C)
    LCD_LINES = (0x80, 0x90, 0x88, 0x98)                    # LCD RAM address(0 and 40H)
    CHR = True
    CMD = False
    E_PULSE = 50                                            # Timing constants in uS
    E_DELAY = 80
    def __init__(self, pinlist, scheduler, cols = 16, rows = 4): # Init with pin nos for CS DIO CLK POW A RST
        self.initialising = True
        self.LCD_CS = pyb.Pin(pinlist[0], pyb.Pin.OUT_PP)
        self.LCD_DIO = pyb.Pin(pinlist[1], pyb.Pin.OUT_PP)
        self.LCD_CLK = pyb.Pin(pinlist[2], pyb.Pin.OUT_PP)
        self.LCD_POW = pyb.Pin(pinlist[3], pyb.Pin.OUT_PP)
        self.LCD_A = pyb.Pin(pinlist[4], pyb.Pin.OUT_PP)
        self.LCD_RST = pyb.Pin(pinlist[5], pyb.Pin.OUT_PP)
        self.LCD_RST.high()
        #self.LCD_A.high() #off
        self.LCD_A.low() #on
        self.LCD_POW.low()
        self.cols = cols
        self.rows = rows
        self.infos = {'G':0,'M':0,1:'   ',2:'   ',3:'   ',4:'   ',
                       5:'   ',6:'   ',7:'   ',8:'   ','E1':0,'E2':0,
                       'E3':0,'E4':0,'E5':1}
        self.dirty = [False]*self.rows
        self.lines = ['']*self.rows
        for thisbyte in LCD.INITSTRING:
            self.lcd_byte(thisbyte, LCD.CMD)
        scheduler.add_thread(runlcd(self))
    
    def _lcd_byte(self,byte):
        for i in range(8):
            if (byte & 0x80):
                self.LCD_DIO.high()
            else:
                self.LCD_DIO.low()
            self.LCD_CLK.low()
            self.LCD_CLK.high()
            byte = byte<<1
        if self.initialising:
            pyb.delay(5)
        else:
            pyb.udelay(LCD.E_DELAY)

    def lcd_byte(self, bits, mode):                         # Send byte to data pins: bits = data
        if mode:                                            # mode = True  for character, False for command
            pre = 0xfa #0b 1111 1010 chr
            #print('send dat and it is "{}"'.format(chr(bits)))
        else:
            pre = 0xf8 #0b 1111 1000 cmd
            #print('send cmd and it is {}'.format(hex(bits)))
            if bits == 0x01:
                self.initialising = False
        self.LCD_CS.high()
        self._lcd_byte(pre)
        self._lcd_byte(bits & 0xf0)
        self._lcd_byte((bits & 0x0f) << 4)
        
        self.LCD_CS.low()
        
    def __setitem__(self, key, message):                   # Send string to display line 0 or 1
                                                            # Strip or pad to width of display. Should use "{0:{1}.{1}}".format("rats", 20)
        #message = "%-*.*s" % (self.cols,self.cols,message)  # but micropython doesn't work with computed format field sizes
        if message != self.infos[key]:                     # Only update LCD if data has changed
            self.infos[key] = message                      # Update stored line
            if key in ['G','M']:
                self.lines[0] = 'G:{}   M:{}'.format(self.infos['G'],self.infos['M'])
                self.dirty[0] = True
            if key in [i+1 for i in range(4)]:
                self.lines[1] = '{} {} {} {} '.format(self.infos[1],self.infos[2],self.infos[3],self.infos[4])
                self.dirty[1] = True
            if key in [i+5 for i in range(4)]:
                self.lines[2] = '{} {} {} {} '.format(self.infos[5],self.infos[6],self.infos[7],self.infos[8])
                self.dirty[2] = True
            if key in ['E'+str(i+1) for i in range(5)]:
                tmp = ''.join([self.infos['E'+str(i+1)]*('E'+str(i+1)+' ') for i in range(5)])
                self.lines[3] = "%-*.*s" % (self.cols,self.cols,tmp)
                self.dirty[3] = True
    def __getitem__(self, key):
        return self.infos[key]

def runlcd(thislcd):                                        # Periodically check for changed text and update LCD if so
    wf = Timeout(0.05)
    rr = Roundrobin()
    while(True):
        for row in range(thislcd.rows):
            if thislcd.dirty[row]:
                msg = thislcd.lines[row]
                thislcd.lcd_byte(LCD.LCD_LINES[row] | row, LCD.CMD)
                for thisbyte in msg:
                    thislcd.lcd_byte(ord(thisbyte), LCD.CHR)
                    yield rr                                # Reshedule ASAP
                thislcd.dirty[row] = False
        yield wf()                                          # Give other threads a look-in


