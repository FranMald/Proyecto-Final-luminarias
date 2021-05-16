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

ssid = 'MicroPython-AP'
password = '123456789'


ap = network.WLAN(network.AP_IF)
sta = network.WLAN(network.STA_IF)
ap.active(True)
sta.active(True)
ap.config(essid=ssid, password=password)

while ap.active() == False:
  pass

print('Connection successful')
print(ap.ifconfig())

led = Pin(2, Pin.OUT)

gc.collect()