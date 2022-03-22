from simple import MQTTClient
from wifi import do_connect
import ujson

def response_cb(topic_cb, msg):
    print (topic_cb)
    print (msg)
    
id_sensor=2
url="demo.thingsboard.io"
user="provision"
pword=""

do_connect("DAVITELWIFI34778","Ja5Achoh")

c = MQTTClient("provision",server=url,user=user,password=pword,port=1883,keepalive=30)
c.set_callback(response_cb)
c.connect()
c.subscribe("/provision/response")
PROVISION_REQUEST = ujson.dumps({"provisionDeviceKey": "444oijxepojfgh3n0oag","provisionDeviceSecret": "2peqabgnq5zkfyucnrp5","deviceName":"Luminaria 5"})
c.publish("/provision/request",PROVISION_REQUEST)

while 1:
    c.check_msg()
    
    
