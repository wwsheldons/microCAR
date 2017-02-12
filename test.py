import pyb
from usched import Sched,wait,Poller

from lcdthread import LCD, PINLIST
from gu906 import MicropyGPRS
from n303 import MicropyGNSS
from m3650b import MicropyRFID

def lcd_thread(P):
    '''
    P---LCD class
    '''
    while True:
        P[0] = 'G:{}   M:{}'.format(g,n)
        P[1] = ''
        yield 1 # update every 1 second


def card_in_low(ic_id,S):
    '''
    S---storage class
    '''
    if ic_id in S.ic_open:
        tmp_num = S.ic_open.index(ic_id)
        lat1,lon1 = (G.latitude,G.longitude)
        tmp_dis = haversine(lat1,lon1,S.gas_latitude[tmp_num],S.gas_longitude[tmp_num])

        if tmp_dis < S.distance[tmp_num]:
            S.ic_using_times[tmp_num] -= 1
            if S.ic_using_times[tmp_num] == 0:
                S.del_one_gas_info(tmp_num)
            return 1 #can open
        else:
            # update_err(2) #out of gas station range
            # GL.err1_start_time = ticks_ms()
            return -1 # out of gas station range
    elif ic_id in S.ic_close:
        return 2 # can close
    elif ic_id in S.emergency_close_card:
        return 4 # can emergency close
    elif ic_id in S.emergency_open_card:
        tmp_num = S.emergency_open_card.index(ic_id)
        S.emergency_open_card_times -= 1
        if S.emergency_open_card_times == 0:
            S.del_one_emergency_open_card(tmp_num)
        S.substruction_for_emergency_open_card(tmp_num)
        return 3 # can emergency open
    else:
        #update_err(1)  # invalid card
        return 0


def Implement_thread(G,M,R,S,L,P):
    '''
    G---GNSS class
    M---gprs class
    R---rfid class
    S---storage class
    L---lock class
    P---LCD class
    '''
    operate_dict = {1:L.opens,
                    2:L.closes,
                    3:L.opens,
                    4:L.closes,
                    0:alarm,
                    -1:alarm,-2:alarm,-3:alarm}
    while True:
        ########################################
        # handle rfid state variable
        ########################################
        if R.ic_id:
            tmp = card_in_low(R.ic_id,S)
            R.ic_id = ''
            operate_dict[]
        ########################################
        # handle gprs state variable
        ########################################
        if M.order_from_server:
            for i,order in enumerate(M.order_from_server):
                if order in server_orders:
                    print('handle({})'.format(order))
                del M.order_from_server[i]
                
        if M.opreat_lock:
            if 'open' in M.opreat_lock:
                print('lock({}S)'.format('open'))
            if 'close' in M.opreat_lock:
                print('lock({}S)'.format('close'))
            M.opreat_lock = ''
        
        if M.lock_power_on:
            print('lock({})'.format('powers_on'))
            print('storage({})'.format('modify_ls'))
            #M.send_sms(num,dat='locks have power on')
            M.lock_power_on = False
        
        if M.storage_phone:
            print('storage({})'.format('set_phone'))
            M.storage_phone = False
        yield




def recv_gprs_thread(gprs):
    wf = Poller(gprs.update, (), 1)                        # Instantiate a Poller with 1 second timeout.
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
    
    
    lcd0 = LCD(PINLIST, objSched)
    objSched = Sched()
    objSched.add_thread(lcd_thread(lcd0))
    objSched.add_thread(robin_5s_thread([gprs.connect_]))
    objSched.add_thread(gprs_thread(gprs.recv_server_dats))
    objSched.run()
    
    
if __name__ == '__main__':
    main()