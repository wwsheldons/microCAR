# polltest.py Demonstrates the use of poll functions where a thread blocks pending the result of a callback function
# polled by the scheduler
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license

import pyb
from usched import Sched, Poller, wait
from gu906 import MicropyGPRS
# Poll functions will be called by the scheduler each time it determines which task to run. The thread will be scheduled
# unless the poll function returns None. When scheduled the result of the poll function - which should be an integer -
# is returned to the thread.
# The intended use of poll functions is for servicing hardware which can't raise interrupts. In such a function
# the function would clear down the device before return so that (until the device again becomes ready) subsequent calls
# would return None. Pseudocode:
# my poll funtion()
#    if hardware is ready
#        service it so that subsequent test returns not ready
#        return an integer
#    return None

# This example polls the accelerometer with a timeout, only responding to changes which exceed a threshold.
# Also demonstrates returning data from a callback by using an object method as a callback function

# The poll function is a method of the Accelerometer class defined below. Using a class method enables the
# function to retain state between calls. In this example it determines the amount of change since the last
# update and returns None if the amount of change is below a threshold: this will cause the scheduler not to
# schedule the thread. If the amount of change exceeds the threshold the Accelerometer instance's data is
# updated and the function returns 1 causing the scheduler to resume the processing thread.


# Run on MicroPython board bare hardware
# THREADS:

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()
def gprs_robin_thread(gprs,timeout):
    yield
    i = 0
    while True :
        i = i+1
        if not gprs.gsm:
            gprs.connect()
            print('connect to the server {} times'.format(i))
        yield 
        print('send_1003 every {} seconds'.format(timeout))
        yield from wait(timeout)

def gprs_thread(objSched):
    gprs_port = pyb.UART(4, 115200, read_buf_len=1024)
    gprs_en = pyb.Pin(pyb.Pin.cpu.B4, pyb.Pin.OUT_PP)
    my_gprs = MicropyGPRS(gprs_port,gprs_en)
    yield from wait(0.02)
    wf = Poller(my_gprs.update, ())                        # Instantiate a Poller with 2 second timeout.
    objSched.add_thread(gprs_robin_thread(my_gprs,2))
    while True:
        reason = (yield wf())
        
        if reason[1]:                                       # Value has changed
            print('my_gprs.ats_dict = {}'.format(my_gprs.ats_dict))
            print('my_gprs.tx_buf = {}'.format(my_gprs.tx_buf))
            print('my_gprs.order_from_server = {}'.format(my_gprs.order_from_server))
            print('my_gprs.rx_dat = {}'.format(my_gprs.rx_dat))
            print()

            if my_gprs.order_from_server:
                for order in my_gprs.order_from_server:
                    
        
        
        

# USER TEST PROGRAM

def test(duration = 0):
    if duration:
        print("Output accelerometer values for {:3d} seconds".format(duration))
    else:
        print("Output accelerometer values")


    

    objSched = Sched()
    objSched.add_thread(gprs_thread(objSched))
    
    if duration:
        objSched.add_thread(stop(duration, objSched))           # Run for a period then stop
    objSched.run()

test(30)

