import pyb
import time

  

dis_buf = [[32]*16]*4
dis_buf[0] = 'G:0   M:0'
num_of_lock = 12
cursor = 0
cursor_addr = 0
banshou_table = {0:' ',1:'U',2:'N'}  #1:'N'  2:'U'
lock_table = {0:' ',1:'O',2:'C',3:'E',4:'K',5:'D'}  #1:'O'  2:'C'  3:'E'

#,cs,dio,clk,lcd_pow,lcd_a,lcd_rst
cs = pyb.Pin(pyb.Pin.cpu.B15, pyb.Pin.OUT_PP)   #RS
dio = pyb.Pin(pyb.Pin.cpu.B14, pyb.Pin.OUT_PP)  #RW
clk = pyb.Pin(pyb.Pin.cpu.A7, pyb.Pin.OUT_PP)   #E
#clk = pyb.Pin(pyb.Pin.cpu.D2, pyb.Pin.OUT_PP)   #E
#clk = pyb.Pin(pyb.Pin.cpu.C7, pyb.Pin.OUT_PP)  #E
lcd_pow = pyb.Pin(pyb.Pin.cpu.C4, pyb.Pin.OUT_PP)
lcd_a = pyb.Pin(pyb.Pin.cpu.C5, pyb.Pin.OUT_PP)
lcd_rst = pyb.Pin(pyb.Pin.cpu.A6, pyb.Pin.OUT_PP)
#lcd_rst = pyb.Pin(pyb.Pin.cpu.C12, pyb.Pin.OUT_PP)
#lcd_rst = pyb.Pin(pyb.Pin.cpu.C6, pyb.Pin.OUT_PP)
CS = cs
DIO = dio
CLK = clk
LCD_POW = lcd_pow
LCD_A = lcd_a
LCD_RST = lcd_rst

LCD_RST.high()
LCD_A.high()
LCD_POW.low()
#time.sleep_ms(20)


def send_byte(byte):
    for i in range(8):
        if (byte&0x80):
            DIO.high()
        else:
            DIO.low()
        CLK.low()
        CLK.high()
        byte = byte<<1
    time.sleep_ms(5)
        
def write_cmd(cmd):
    CS.high()
    #pyb.delay(5)
    send_byte(0xf8)
    send_byte(cmd & 0xf0)
    send_byte((cmd & 0x0f) << 4)
    time.sleep_us(200)
    CS.low()

def write_dat( dat):
    CS.high()
    #pyb.delay(5)
    send_byte(0xfa)
    send_byte(dat & 0xf0)
    send_byte((dat & 0x0f) << 4)
    time.sleep_us(200)
    CS.low()
def lcd_init():
    write_cmd(0x30)
    write_cmd(0x01)
    time.sleep_ms(1)
    write_cmd(0x06)
    write_cmd(0x0C)
def clear():
    write_cmd(0x30)
    write_cmd(0x01)
    time.sleep_ms(5)
def dis(x,y,datas):
    if x == 0:
        y = y | 0x80
    if x == 1:
        y = y | 0x90
    if x == 2:
        y = y | 0x88
    if x == 3:
        y = y | 0x98
    write_cmd(y)
    for data in datas:
        if type(data) == str:
            data = ord(data)
        write_dat(data)

def update_buf(g,n,ws,ls):
    '''
    g: GPS signal
       0: no siganl
       1: normal
    n: NET signal
       0: no siganl
       1: normal
    ws: banshou
        1: open
        2: close
    ls: lock
        1: open
        2: close
        3: unnormal
        4: gaizi open
    '''
    
    if max(ws) > 2 or max(ls)>4:
        print('check lock error')
        return None
    tmp_buf = ['   ']*num_of_lock
    if len(ws) > num_of_lock or len(ls) > num_of_lock:
        print('ws length is {} and ls length is {} and num_of_lock is {}'.format(len(ws),len(ls),num_of_lock))
        print('data length is not {}'.format(num_of_lock))
        return None
    for i in range(8):
        if ws[i] != 0 and ls[i] != 0:
            tmp_buf[i] = str(i+1)+banshou_table[ws[i]]+lock_table[ls[i]]
    dis_buf[1] = tmp_buf[0]+' '+tmp_buf[1]+' '+tmp_buf[2]+' '+tmp_buf[3]
    dis_buf[2] = tmp_buf[4]+' '+tmp_buf[5]+' '+tmp_buf[6]+' '+tmp_buf[7]

    dis_buf[0] = 'G:{}   M:{}'.format(g,n)

    
def dis_all(g,n,ws,ls):
    update_buf(g,n,ws,ls)
    #clear()
    for i in range(4):
        dis(i,0,dis_buf[i])
        time.sleep_ms(1)

def update_lock_info(lock_id,ws,ls):
    if lock_id > 7:
        return 0
    hang_dict = {0:1,1:1,2:1,3:1,4:2,5:2,6:2,7:2}
    addr_dict = {0:16,1:18,2:20,3:22,4:8,5:10,6:12,7:14}
    if ws in [1,2] and ls in [1,2,3,4,5]:
        tmp = str(lock_id+1)+banshou_table[ws]+lock_table[ls]
    else:
        tmp = '   '
    dis(hang_dict[lock_id],addr_dict[lock_id],tmp)
    
    time.sleep_ms(5)
def update_g_m(g,n):
    buf = 'G:{}   M:{}'.format(g,n)
    dis(0,0,buf)
    time.sleep_ms(5)
def update_err(n,opt = 1):
    code_dict={1:0,2:1,3:3,4:4,5:6}
    if opt:
        if n in [2,4]:
            buf = ' E{}'.format(n)
        elif n in [1,3,5]:
            buf = 'E{}'.format(n)
        else:
            debug_print('wrong error code')
    else:
        if n in [2,4]:
            buf = '   '
        elif n in [1,3,5]:
            buf = '  '
        else:
            GL.debug_print('wrong error code')
    dis(3,code_dict[n],buf)
    time.sleep_ms(5)
def set_a():
    LCD_A.value(0)
def clc_a():
    LCD_A.value(1)



lcd_lock = {'update_li':update_lock_info,'update_e':update_err,'s_a':set_a,'c_a':clc_a}

lcd_main = {'update_e':update_err,'s_a':set_a,'c_a':clc_a,}
