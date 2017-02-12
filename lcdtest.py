# lcdtest.py Demo/test program for MicroPython scheduler with attached LCD display
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license
# Display must use the Hitachi HD44780 controller. This demo assumes a 16*2 character unit.

import pyb
from usched import Sched,wait
from lcdthread import LCD, PINLIST                          # Library supporting Hitachi LCD module

# HARDWARE
# Micropython board with LCD attached using the 4-wire data interface. See lcdthread.py for the
# default pinout. If yours is wired differently, declare a pinlist as per the details in lcdthread
# and instantiate the LCD using that list.

# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield fTim
    objSch.stop()
def lcd_a(mylcd,a,time=0):
    '''
    a = 0---clc
        1---set
    '''
    yield
    mylcd.LCD_A.value(not a)
    while True:
        if time:
            yield from wait(time)
            mylcd.LCD_A.value(a) #0---set lcd_a
            return
            


def lcd_thread(mylcd):
    i = 0
    
    yield
    while True:
        mylcd['G'] = 1
        mylcd['M'] = 0
        
        mylcd[2] = '2ND'
        yield 1

# USER TEST PROGRAM
# Runs forever unless you pass a number of seconds

def test(duration = 0):
    if duration:
        print("Test LCD display for {:3d} seconds".format(duration))
    objSched = Sched()
    lcd0 = LCD(PINLIST, objSched)
    objSched.add_thread(lcd_a(lcd0,1,3))
    objSched.add_thread(lcd_thread(lcd0))
    if duration:
        objSched.add_thread(stop(duration, objSched))
    objSched.run()

test(10)

