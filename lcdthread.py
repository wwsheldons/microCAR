import pyb,GL
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

'''
def lcd_a_thread(my_lcd,a,time=0):
    """
    a = 0---clc
        1---set
    """
    yield
    my_lcd.LCD_A.value(not a)
    while True:
        if time:
            yield from wait(time)
            my_lcd.LCD_A.value(a) #0---set lcd_a
            gc.collect()
            return
'''


class LCD(object):                                          # LCD objects appear as read/write lists
    INITSTRING = (0x30, 0x01, 0x06, 0x0C)
    LCD_LINES = (0x80, 0x90, 0x88, 0x98)                    # LCD RAM address(0 and 40H)
    CHR = True
    CMD = False
    E_PULSE = 50                                            # Timing constants in uS
    E_DELAY = 80
    def __init__(self, cols = 16, rows = 4): # Init with pin nos for CS DIO CLK POW A RST
        self.initialising = True
        
        self.LCD_CS = pyb.Pin(PINLIST[0], pyb.Pin.OUT_PP)
        self.LCD_DIO = pyb.Pin(PINLIST[1], pyb.Pin.OUT_PP)
        self.LCD_CLK = pyb.Pin(PINLIST[2], pyb.Pin.OUT_PP)
        self.LCD_POW = pyb.Pin(PINLIST[3], pyb.Pin.OUT_PP)
        self.LCD_A = pyb.Pin(PINLIST[4], pyb.Pin.OUT_PP)
        self.LCD_RST = pyb.Pin(PINLIST[5], pyb.Pin.OUT_PP)
        self.LCD_RST.high()
        #self.LCD_A.high() #off
        self.LCD_A.low() #on
        self.LCD_POW.low()
        self.cols = cols
        self.rows = rows
        '''
        self.infos = {'G':0,'M':0,1:'   ',2:'   ',3:'   ',4:'   ',
                       5:'   ',6:'   ',7:'   ',8:'   ',9:'   ',10:'   ',
                       11:'   ',12:'   ','E1':0,'E2':0,'E3':0,'E4':0,'E5':0}
        '''
        self.dirty = [False]*self.rows
        self.lines = ['']*self.rows
        
        for thisbyte in LCD.INITSTRING:
            self.lcd_byte(thisbyte, LCD.CMD)
        GL.g = GL.m = 0
        GL.N_lock = 12
        GL.lock_status = [0]*GL.N_lock
        '''
        GL.ERROR[0]  --- # invalid card
        GL.ERROR[1]  --- # out of gas station range
        GL.ERROR[2]  --- # error from server
        GL.ERROR[3]  --- # no_phone_card
        GL.ERROR[4]  --- # reserve
        '''
        GL.ERROR = [0]*5
        self.update(0)
        #scheduler.add_thread(runlcd(self))
        #self.scheduler = scheduler
        
        
    def tick2(self,timer):
        self.LCD_A.value(1) #clc
        timer.deinit()


    def start_ns_delay(self,n=60*3):
        self.LCD_A.value(0) #set
        #n_us < 1073741823
        #n_us =    1000000*n
        tim2 = pyb.Timer(2)
        tim2.init(prescaler=84, period=1000000*n)
        tim2.callback(self.tick2)
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
        self.LCD_CS.high()
        self._lcd_byte(pre)
        self._lcd_byte(bits & 0xf0)
        self._lcd_byte((bits & 0x0f) << 4)
        
        self.LCD_CS.low()
        if bits == 0x01 and pre == 0xf8:
            self.initialising = False
    '''
    def __setitem__(self, key, message):                   # Send string to display line 0 or 1
                                                           # Strip or pad to width of display. Should use "{0:{1}.{1}}".format("rats", 20)
        #message = "%-*.*s" % (self.cols,self.cols,message)  # but micropython doesn't work with computed format field sizes
        if message != self.lines[key]:                     # Only update LCD if data has changed
            self.lines[key] = message                      # Update stored line
            self.dirty[key] = True

    def __getitem__(self, key):
        return self.lines[key]
    '''
    def update(self,opt = -1):
        if opt in [4,1,2,3]:
            self.dirty[1] = True
        elif opt in [5,6,7,8]:
            self.dirty[2] = True
        elif opt == 9:
            self.dirty[3] = True
        elif opt == 0:
            self.dirty[0] = True
        elif opt == 10:
            self.dirty = [True]*self.rows
        else:
            pass
        if True in self.dirty:
            #self.scheduler.add_thread(lcd_a_thread(self,1))
            self.start_ns_delay()
        else:
            return 100
        bs = {0:' ',1:'U',2:'N'}  #1:'N'  2:'U'
        lt = {0:' ',1:'O',2:'C',3:'E',4:'K',5:'D'}  #1:'O'  2:'C'  3:'E'

        self.lines[0] = 'G:{}   M:{}'.format(GL.g,GL.m)
        for i,ele in enumerate(GL.lock_status):
            if ele & 0xf0 == 0 or ele & 0x0f == 0:
                GL.lock_status[i] = 0
        self.lines[1] = '{}{}{} {}{}{} {}{}{} {}{}{} '.format([1 if GL.lock_status[0]  else ' ' ][0],bs[(GL.lock_status[0] & 0xf0) >> 4],lt[GL.lock_status[0] & 0x0f],
                                                              [2 if GL.lock_status[1]  else ' ' ][0],bs[(GL.lock_status[1] & 0xf0) >> 4],lt[GL.lock_status[1] & 0x0f],
                                                              [3 if GL.lock_status[2]  else ' ' ][0],bs[(GL.lock_status[2] & 0xf0) >> 4],lt[GL.lock_status[2] & 0x0f],
                                                              [4 if GL.lock_status[3]  else ' ' ][0],bs[(GL.lock_status[3] & 0xf0) >> 4],lt[GL.lock_status[3] & 0x0f])
        self.lines[2] = '{}{}{} {}{}{} {}{}{} {}{}{} '.format([5 if GL.lock_status[4]  else ' ' ][0],bs[(GL.lock_status[4] & 0xf0) >> 4],lt[GL.lock_status[4] & 0x0f],
                                                              [6 if GL.lock_status[5]  else ' ' ][0],bs[(GL.lock_status[5] & 0xf0) >> 4],lt[GL.lock_status[5] & 0x0f],
                                                              [7 if GL.lock_status[6]  else ' ' ][0],bs[(GL.lock_status[6] & 0xf0) >> 4],lt[GL.lock_status[6] & 0x0f],
                                                              [8 if GL.lock_status[7]  else ' ' ][0],bs[(GL.lock_status[7] & 0xf0) >> 4],lt[GL.lock_status[7] & 0x0f])
        
        self.lines[3] = '{} {} {} {} {}'.format(['E1' if GL.ERROR[0] else '  '][0],
                                                ['E2' if GL.ERROR[1] else '  '][0],
                                                ['E3' if GL.ERROR[2] else '  '][0],
                                                ['E4' if GL.ERROR[3] else '  '][0],
                                                ['E5' if GL.ERROR[4] else '  '][0])
        for row in range(self.rows):
            if self.dirty[row]:
                msg = self.lines[row]
                self.lcd_byte(LCD.LCD_LINES[row], LCD.CMD)
                for thisbyte in msg:
                    self.lcd_byte(ord(thisbyte), LCD.CHR)
                self.dirty[row] = False
        if opt == 10:
            GL.debug_print('lcd init is finished...')
        return 1

