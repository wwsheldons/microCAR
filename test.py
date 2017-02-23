
from storage import MicropySTORAGE
from gu906 import MicropyGPRS
from n303 import MicropyGNSS
import pyb,GL,gc
from usched import Sched, Poller, wait,Timeout
from wdt import wdog
from beep import alarm
from lcdthread import LCD


from tja1040 import MicropyLOCK
from m3650b import MicropyRFID


def str2bcd(d):
    if len(d)%2:
        d='0'+d
    out = bytearray(8)
    for i in range(0,len(d),2):
        t = d[i:i+2]
        out[int(i/2)+8-int(len(d)/2)] = (int(t[0])<<4)+int(t[1])
    return out

def stop(fTim, objSch):                                     # Stop the scheduler after fTim seconds
    yield from wait(fTim)
    objSch.stop()


def robin_tick_thread(objSched,my_lcd,my_lock,my_gprs,my_storage):

    yield
    while True :
        print('robin_tick_thread is runing  111111111111111111')
        ####################################################
        # check the control's cover whether is opend or not
        # from n303
        '''
            if self.control_cover.read() > 3900:
                GL.gnss_buf[54:55] = b'2'
            if self.control_cover.read() < 300:
                GL.gnss_buf[54:55] = b'1'
        '''
        if 4 in my_lock.ls or GL.gnss_buf[54:55] == b'2':
            my_lock.locks_power_off()
            my_lcd.start_ns_delay()
            objSched.add_thread(alarm(4))
            if GL.m:
                my_gprs.send_1003()
                
            else:
                my_storage.modify_info(my_storage.lsfn,1)
            GL.dog.feed()
        ####################################################
        # check the net status
        if not GL.m:
            my_gprs.connect()
        # check locks status
        my_lock.check_locks()
        GL.dog.feed()
        my_gprs.check_csq()
        GL.dog.feed()
        my_gprs.check_phone_card()
        GL.dog.feed()
        my_gprs.rec_sms()
        GL.dog.feed()
        if GL.m:
            ##############################################
            # upload the offline data
            # upload the offline pos data
            n_pos = my_storage.get_rows(my_storage.posfn)
            times = 0
            while n_pos or 0 < times < 3:
                my_storage.get_info(my_storage.posfn,n_pos)
                my_gprs.send_dats(my_storage.get_info(my_storage.posfn,n_pos),0x1003)
                my_storage.del_rows(my_storage.posfn,n_pos)
                n_pos -= 1
                times += 1
            GL.dog.feed()
            # upload the offline sms opreate lock data
            n_sms = my_storage.get_rows(my_storage.smsfn)
            times = 0
            while n_sms or 0 < times < 3:
                my_storage.get_info(my_storage.smsfn,n_sms)
                my_gprs.send_dats(my_storage.get_info(my_storage.smsfn,n_sms),0x1000)
                my_storage.del_rows(my_storage.smsfn,n_sms)
                n_sms -= 1
                times += 1
            GL.dog.feed()

            my_gprs.send_1003()
            GL.dog.feed()

        GL.debug_print('send_1003 every          {} seconds'.format(GL.report_tick))
        GL.debug_print('the GNSS signal is       {}'.format(GL.g))
        GL.debug_print('the GPRS signal is       {}'.format(GL.m))
        GL.debug_print('the lock status is       {}'.format([hex(i) for i in GL.lock_status]))
        GL.debug_print('the rssi is              {}'.format(GL.rssi))
        GL.debug_print('GL.send_9012           = {}'.format(GL.send_9012))
        
        GL.dog.feed()
        gc.collect()
        
        yield from wait(GL.report_tick)



def rfid_thread(objSched,my_lcd,my_lock,my_rfid,my_storage,my_gprs):
    
    wf = Poller(my_rfid.get_id, ())
    while(True):
        reason = (yield wf())
        gc.collect()
        GL.dog.feed()
        if reason[1]:
            GL.debug_print('iiiiiiiiiiiiiiiiiiiiiiiiiii {}'.format(GL.ic_id))
            objSched.add_thread(alarm(1))
            # clear error on lcd
            GL.ERROR = [0]*5
            my_lcd.update(9) #  update line 3
            if GL.m:
                my_gprs.handle_900a(0x1000)
            else:
                tmp = my_storage.card_in_low()
                ###############################
                # -2 # speed is over 30kmh
                # 0 # out of gas station ranges
                # -1 # invalid card
                # 1 #can open
                # 2 # can close
                # 3 # can emergency open
                # 4 # can emergency close
                if tmp in [1,3]:
                    my_lock.open_locks()
                elif tmp in [2,4]:
                    my_lock.close_locks()
                elif tmp <= 0:
                    objSched.add_thread(alarm())
                else:
                    print('wrong return from cmy_storage.card_in_low() {}'.format(tmp))
                ##  lss+gnss_buf+ic_id
                info = bytearray(GL.lock_status)+GL.gnss_buf+GL.ic_id.encode()
                info[12+53] = 50 #lss(12),gnss_buf 53th (b'1'--realtime,b'2'--no realtime)
                my_storage.modify_info(my_storage.srfn,info,'add')
                GL.debug_print('offline swipe record add 1')
                gc.collect()
                GL.dog.feed()


def robin_9012_thread(my_gprs,timeout=60):
    yield
    while True :
        GL.debug_print('send_1012 every {} seconds'.format(timeout))
        if not GL.m:
            my_gprs.connect()

        
        if GL.m:
            GL.dog.feed()
            my_gprs.send_1012()
        gc.collect()
        GL.dog.feed()
        yield from wait(timeout)

def gprs_thread(objSched,my_gprs,my_lcd,my_lock,my_storage):
    wf0 = Timeout(0.5)
    wf = Poller(my_gprs.update, ())                        # Instantiate a Poller with 2 second timeout.
    
    while True:
        reason = (yield wf())
        gc.collect()
        GL.dog.feed()
        if reason[1]:
            print('gprs thread is runing')
            
            GL.debug_print('my_gprs.ats_dict = {}'.format(my_gprs.ats_dict))
            for order in my_gprs.ats_dict.keys():
                del my_gprs.ats_dict[order]
            if GL.sms_storage_ip_id_port:
                GL.sms_storage_ip_id_port = False
                my_storage.modify_info(my_storage.ipfn,GL.ip)
                my_storage.modify_info(my_storage.portfn,GL.port)
                if len(GL.id) == 11:
                    my_storage.modify_info(my_storage.idfn,GL.id)

            if GL.sms_storage_pwd:
                GL.sms_storage_pwd = False
                my_storage.modify_info(my_storage.pwdfn,GL.pwd)
            if GL.sms_storage_phone:
                GL.sms_storage_phone = False
                my_storage.modify_infos(my_storage.apfn,GL.set_phone)
            if GL.sms_lock_power_on:
                GL.sms_lock_power_on = False
                my_lock.locks_on()
                GL.lock_status = [1]*GL.N_lock
                my_lock.check_locks()
                my_gprs.send_sms(my_gprs.phone_num,'locks have power on')
            if GL.sms_opreat_lock:
                order = GL.sms_opreat_lock[0]
                num = GL.sms_opreat_lock[1]
                GL.sms_opreat_lock = False
                if 'open' in order:
                    order = 'open'
                    my_lock.open_locks()
                if 'close' in order:
                    order = 'close'
                    my_lock.close_locks()
                GL.dog.feed()
                sms_info = bytearray(GL.lock_status)+GL.gnss_buf+str2bcd(num)
                sms_info[53+12] = 50
                my_storage.modify_info(my_storage.smsfn,sms_info,'add')
                my_gprs.send_sms(num,'{} locks has finished'.format(order))
                GL.dog.feed()
            for order in GL.rx_order_dat.keys():
                GL.debug_print('trigger order = {}'.format(order))
                GL.dog.feed()
                if order == '9000' and (b'1' in GL.rx_order_dat['9000'] or b'2' in GL.rx_order_dat['9000']):
                    my_lcd.start_ns_delay()
                if my_gprs.supported_order[order][1](my_gprs,objSched,my_lock,my_storage):
                    del GL.rx_order_dat[order]
            yield wf0()
            GL.dog.feed()
            


def gnss_thread(my_lock,my_gnss,my_storage):
    
    wf = Poller(my_gnss.update, (my_storage,))
    while True:
        reason = (yield wf())
        gc.collect()
        GL.dog.feed()
        #GL.debug_print(gnss_port.read())
        #GL.debug_print(GL.gnss_buf)
        if reason[1]:                                       # Value has changed
            print('gnss thread is runing')
            GL.debug_print(GL.gnss_buf)
            GL.dog.feed()
            
            
            if GL.vcc_below_14V:
                GL.vcc_below_14V = False
            if GL.locks_on_checks_vcc19V:
                GL.locks_on_checks_vcc19V = False
                my_lock.locks_power_on()
                my_lock.check_locks()

            if GL.locks_off:
                GL.locks_off = False
                my_lock.locks_power_off()
        



def main():

    dog = wdog()
    GL.dog = dog

    gc.enable()
    
    GL.init = True
    objSched = Sched()

    ##############################
    '''
    GL.g = 0
    GL.m = 0
    GL.N_lock = 12
    GL.lock_status = [1]*GL.N_lock
    GL.ic_id = '12345678'
    '''
    

    
    
    my_lcd = LCD()
    GL.lcd_update =my_lcd.update
    GL.lcd_update(10) #lcd init

    my_lock = MicropyLOCK()
    
    my_storage = MicropySTORAGE()
    my_gprs = MicropyGPRS(gc.collect)
    my_gnss = MicropyGNSS()
    my_rfid = MicropyRFID()
    
    
    

    
    
    if int(my_storage.get_info(my_storage.usfn),10) == 0:
        my_storage.prepare()
        my_gprs.wait_set_sms(objSched)
    my_storage.modify_info(my_storage.usfn,int(my_storage.get_info(my_storage.usfn),10)+1)

    my_gprs.connect()
    

    GL.debug_print('init is over.............')
    GL.debug_print('')
    GL.debug_print('')
    GL.dog.start(65535)
    GL.init = False

    objSched.add_thread(gprs_thread(objSched,my_gprs,my_lcd,my_lock,my_storage))
    objSched.add_thread(gnss_thread(my_lock,my_gnss,my_storage))
    objSched.add_thread(robin_tick_thread(objSched,my_lcd,my_lock,my_gprs,my_storage))
    objSched.add_thread(rfid_thread(objSched,my_lcd,my_lock,my_rfid,my_storage,my_gprs))
    objSched.add_thread(robin_9012_thread(my_gprs))
    

    objSched.run()
    
    
if __name__ == '__main__':
    
    main()