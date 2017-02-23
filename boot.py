# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

import machine
import pyb
beep_port = pyb.Pin(pyb.Pin.cpu.A8, pyb.Pin.OUT_PP)
beep_port.low()
#pyb.main('roundrobin.py')
pyb.main('test.py') # main script to run after this one
#pyb.usb_mode('CDC+MSC') # act as a serial and a storage device
#pyb.usb_mode('CDC+HID') # act as a serial device and a mouse
