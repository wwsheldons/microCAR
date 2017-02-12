# polltest.py Demonstrates the use of poll functions where a thread blocks pending the result of a callback function
# polled by the scheduler
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license

import pyb
from usched import Sched, Poller, wait
from n303 import MicropyGNSS
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


def gnss_thread():
    gnss_port = pyb.UART(2,9600,timeout=10,read_buf_len=64)
    gnss_reset_pin = pyb.Pin(pyb.Pin.cpu.B4, pyb.Pin.OUT_PP)
    battery_voltage = pyb.ADC(pyb.Pin.cpu.B1)
    vcc_voltage = pyb.ADC(pyb.Pin.cpu.B0)
    control_cover = pyb.ADC(pyb.Pin.cpu.A5)
    pins = (gnss_reset_pin,battery_voltage,vcc_voltage,control_cover)
    yield from wait(0.03)                                   # Allow accelerometer to settle
    my_gnss = MicropyGNSS(gnss_port,pins)
    wf = Poller(my_gnss.update, ())                        # Instantiate a Poller with 2 second timeout.
    while True:
        reason = (yield wf())
        #print(gnss_port.read())
        #print(my_gnss.gnss_buf)
        if reason[1]:                                       # Value has changed
            print(my_gnss.gnss_buf)
            if my_gnss.vcc_below_14V:
                my_gnss.vcc_below_14V = False
                print('vcc_below_14V is {}'.format(my_gnss.vcc_below_14V))
            if my_gnss.vcc_over_19V:
                my_gnss.vcc_over_19V = False
                print('vcc_over_19V is {}'.format(my_gnss.vcc_over_19V))
            if my_gnss.battery_below_10V:
                my_gnss.battery_below_10V = False
                print('battery_below_10V is {}'.format(my_gnss.battery_below_10V))
            
        

# USER TEST PROGRAM

def test(duration = 0):
    if duration:
        print("Output accelerometer values for {:3d} seconds".format(duration))
    else:
        print("Output accelerometer values")
    objSched = Sched()
    objSched.add_thread(gnss_thread())
    if duration:
        objSched.add_thread(stop(duration, objSched))           # Run for a period then stop
    objSched.run()

test(10)

