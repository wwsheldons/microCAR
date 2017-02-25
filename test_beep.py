import pyb


BEEP_PORT=pyb.Pin(pyb.Pin.cpu.A8, pyb.Pin.OUT_PP)
BEEP_PORT.low()


def alarm(n = 3,time = 0.1):
    '''
    a = 0---clc
        1---set
    '''
    
    BEEP_PORT.low()
    while True:
        if not n:
            BEEP_PORT.high()
        else:
            for i in range(n):
                BEEP_PORT.high()
                pyb.delay(int(time*1000))
                BEEP_PORT.low()
                pyb.delay(int(time*1000))
        return

                    