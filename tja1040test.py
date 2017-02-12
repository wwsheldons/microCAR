# polltest.py Demonstrates the use of poll functions where a thread blocks pending the result of a callback function
# polled by the scheduler
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license

import pyb
from usched import Sched, Poller, wait
from tja1040 import MicropyLOCK,POWER_LIST
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


def lock_thread():
    can_port = pyb.CAN(2)
    can_port.init(pyb.CAN.NORMAL, extframe=False, prescaler=8,  sjw=1, bs1=12, bs2=8)#250K
    can_port.setfilter(0, pyb.CAN.LIST16,0,(1, 2, 4,0))

    yield from wait(0.02)
    my_lock = MicropyLOCK(can_port,POWER_LIST)
    wf = Poller(my_lock.rec_lock_dat, ())                        # Instantiate a Poller with 2 second timeout.
    
    while True:
        reason = (yield wf())
        
        if reason[1]:                                       # Value has changed
            print('my_lock.lock_status = {}'.format([hex(i)[2:] for i in my_lock.lock_status]))
            print('my_lock.lose_lock = {}'.format(my_lock.lose_lock))
            print('my_lock.lcd_on = {}'.format(my_lock.lcd_on))
            print('my_lock.update_lcd_ls = {}'.format(my_lock.update_lcd_ls))
            print()

                    
        
        
        

# USER TEST PROGRAM

def test(duration = 0):
    if duration:
        print("Output accelerometer values for {:3d} seconds".format(duration))
    else:
        print("Output accelerometer values")


    

    objSched = Sched()
    objSched.add_thread(lock_thread())
    
    if duration:
        objSched.add_thread(stop(duration, objSched))           # Run for a period then stop
    objSched.run()

test(30)

