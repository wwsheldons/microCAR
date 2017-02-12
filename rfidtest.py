# lcdtest.py Demo/test program for MicroPython scheduler with attached LCD display
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license
# Display must use the Hitachi HD44780 controller. This demo assumes a 16*2 character unit.

import pyb
from usched import Sched,wait,Poller
from m3650b import MicropyRFID                          # Library supporting Hitachi LCD module

# HARDWARE
# Micropython board with LCD attached using the 4-wire data interface. See lcdthread.py for the
# default pinout. If yours is wired differently, declare a pinlist as per the details in lcdthread
# and instantiate the LCD using that list.

# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield fTim
    objSch.stop()

def rfid_thread():
    
    rfid_port = pyb.UART(3,9600,timeout=10,read_buf_len=12)
    yield from wait(0.03)
    rfid = MicropyRFID(rfid_port)
    wf = Poller(rfid.get_id, ())
    while(True):
        reason = (yield wf())
        if reason[1]:
            print(rfid.ic_id)

# USER TEST PROGRAM
# Runs forever unless you pass a number of seconds

def test(duration = 0):
    if duration:
        print("Test LCD display for {:3d} seconds".format(duration))
    objSched = Sched()
    
    objSched.add_thread(rfid_thread())
    if duration:
        objSched.add_thread(stop(duration, objSched))
    objSched.run()

test(10)

