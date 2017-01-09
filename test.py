import pyb
from usched import Sched,wait,Poller


from gu906 import MicropyGPRS
from n303 import MicropyGPS






def handle_gprs_thread(m):
    while True:
        if m.order_from_server:
            for i,order in enumerate(m.order_from_server):
                if order in server_orders:
                    handle(i)
                del m.order_from_server[i]

        if m.opreat_lock:
            if 'open' in m.opreat_lock:
                lock('opens')
            if 'close' in m.opreat_lock:
                lock('closes')
            m.opreat_lock = ''
        if m.lock_power_on:
            lock('powers_on')
            storage['modify_ls'](0)
            m.send_sms(num,dat='locks have power on')
            m.lock_power_on = False
        if m.storage_phone:
            storage('')
            m.storage_phone = False





def recv_gprs_thread(gprs):
    wf = Poller(gprs.recv_server_dats, (), 1)                        # Instantiate a Poller with 1 second timeout.
    while True:
        reason = (yield wf())
        if reason[1]:
            print("gprs.ats_dict={}".format(gprs.ats_dict))
        if reason[2]:
            print("Timeout waiting for accelerometer change")


def main():
    #beep_init()
    #dog = wdog()
    gc.enable()
    #dog.start(65535)
    
    GL.report_tick = 5
    
    
    gprs_port = pyb.UART(4, 115200, read_buf_len=1024)
    g_en = pyb.Pin(pyb.Pin.cpu.B4, pyb.Pin.OUT_PP)
    gprs = Gprs_erometer(gprs_port,g_en)
    
    
    
    objSched = Sched()
    objSched.add_thread(robin_5s_thread([gprs.connect_]))
    objSched.add_thread(gprs_thread(gprs.recv_server_dats))
    objSched.run()
    
    
if __name__ == '__main__':
    main()