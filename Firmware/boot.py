import uos, machine
import gc
try:
  import usocket as socket
except:
  import socket
import network
from machine import Pin
import esp
esp.osdebug(None)

import gc
gc.collect()

ap_ssid = 'MicroPython-AP'
ap_pword = '123456789'


ap = network.WLAN(network.AP_IF)
sta = network.WLAN(network.STA_IF)
ap.active(True)
sta.active(True)
ap.config(essid=ap_ssid, password=ap_pword)
led = Pin(2, Pin.OUT)
while ap.active() == False:
    led.on()
    utime.sleep_ms(200)
    led.off()
    utime.sleep_ms(200)
    pass

print('Connection successful')
print(ap.ifconfig())
led.on()
