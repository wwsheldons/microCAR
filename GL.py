# Global share data
#########################################
# tja1040.py
'''
GL.N_lock                  # variable
GL.lock_status             # variable
GL.lose_lock               # variable
'''
#########################################
# gu906.py
'''
GL.m                       # variable
GL.rssi                    # variable
GL.send_9012               # variable
GL.cme_error2              # variable
GL.report_tick             # variable
GL.rx_order_dat            # variable
GL.update_lcd              # variable
'''
#########################################
# n303.py
'''
GL.g                       # variable
GL.gnss_buf                # variable
GL.vcc_below_14V           # variable
GL.locks_on_checks_vcc19V  # variable
GL.locks_off               # variable
'''
#########################################
# m3650b.py
'''
GL.ic_id                   # variable
'''
#########################################
# storage.py
'''
GL.ip                      # variable
GL.ic                      # variable
GL.port                    # variable
GL.pwd                     # variable
'''
#########################################
# test.py
'''
GL.init
Gl.dog
GL.lcd_update              # function
'''

debug = True

def debug_print(mess=''):
    if debug:
        print(mess)