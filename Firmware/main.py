import dht
import machine
from simple import MQTTClient
from wifi import do_connect
import ujson
import utime
import ntptime
import random
from ina226 import INA226

def sub_cb(topic, msg):
    global tim,tim2, PWM,scan_state,scan_rate,AVG,Nsens
    print(topic)
    ATTR=ujson.loads(msg)
    
    for i in range (0,len(ATTR)):
        if ATTR.get('Scan status')!=None:                        #habilitar o deshabilitar el scaneo y reporte temporizado
            print('Scan status')
            if ATTR.get('Scan status')=='true':
                print(msg)
                tim.deinit()
                tim.init(period=scan_rate,callback=Scan_callback)
                scan_state=1
            if ATTR.get('Scan status')=='false':
                print(msg)
                tim.deinit()
                scan_state=0
        if ATTR.get('Scan Rate')!=None:                        #configuracion del Scan Rate
            print('Scan Rate')
            scan_rate=int(ATTR.get('Scan Rate'))
            if scan_state==b'on':
                tim2.deinit()
                tim.deinit()
                tim.init(period=scan_rate,callback=Scan_callback)        
            print(scan_rate)
        #if topic==b's/'+str(Nsens)+b'/CONFIG/ON_DEMAND':                   #pedido de medicion on demand
        #    Scan_callback(tim)
        if ATTR.get('PWM')!=None:                         # ingreso de valor del PWM
            print('PWM')
            PWM=ATTR.get('PWM')
            #pwm1.duty(PWM)
            print(PWM)
        if ATTR.get('Muestras Promedio')!=None:                         # ingreso de cantidad de muestras promedidadas por cada reporte (minimo 1 muestra por segundo)
            print('Muestras Promedio')
            AVG=ATTR.get('Muestras Promedio')
            print(AVG)
        print(i)
    #values_config[1]=scan_state
    #values_config[2]=scan_rate
    #values_config[3]=AVG
    #values_config[4]=PWM
    #a=utime.localtime()
    #values_config[0]=str(a[0])+'/'+str(a[1])+'/'+str(a[2])+' '+str(a[3])+':'+str(a[4])+':'+str(a[5])
    #values[0]=utime.time()
    #for i in range(0,len(tags_config)):   
    #    dict2[tags_config[i]] = values_config[i]
    #    OUT2=ujson.dumps(dict2)
    #c.publish(attributes)
    tim2.init(period=1000,callback=Sub_timer2_cb)
    
def Sub_timer2_cb(timer):
    global c
    #print("check")
    c.check_msg()
    
def Scan_callback(timer):                # calback para el escaneo de los sensores (agregar posibilidad de realizar promedio de mediciones)
    global d,c,values,led,Pin_STS,tags,x,muestras
    if led.value()==1 :  
	led.off()      
    else:
	led.on()
    x=x+1
    #print(x)
    #inicio de medicion
    try:                        #medicion de temperatura y humedad
        d.measure()
        values[1]=d.temperature()
        values[2]=d.humidity()
    except:
        values[1]="error"
        values[2]="error"
    
    values[5]=int.from_bytes(i2c.readfrom(35, 2),"big")/1.2     #medicion de luminosidad
    values[6]=Pin_STS.value()                                   #acuse de estado de lampara (bit interno)
    #values[6]=PWM
    #medicion de tension y corriente
    values[3]=ina.bus_voltage
    values[4]=ina.current
    #a=utime.localtime()
    #values[0]=str(a[0])+'/'+str(a[1])+'/'+str(a[2])+' '+str(a[3])+':'+str(a[4])+':'+str(a[5])
    values[0]=utime.time()
    
    muestras.append([values[1],values[2],values[3],values[4],values[5]])
    if len(muestras) > AVG:
        muestras=muestras[1:]
    print(muestras)
    #parseo json
    for i in range(0,len(tags)):
        dict[tags[i]] = values[i]
        OUT=ujson.dumps(dict)
    #publica en topic
    try:
        print(OUT)
        c.publish(topic, OUT)
    except:
        print ('fallo de publish')
        do_connect()
        c.connect()


dict = {}
dict2 = {}
#tags=['temperature','humidity','voltage','current','state','timestamp']
tags_config=['timestamp','SCAN','RATE','AVG','PWM']
values_config=['0','0','0','0','0']
tags=['timestamp','TEMP','HUM','V','I','LUM','STS']
values=['0','0','0','0','0','0','0']
muestras=[['0','0','0','0','0']]
Nsens=6
AVG=1
dt=-3600*3
scan_rate=5000
scan_state=b'on'
PWM=50
user="P0tW2dm4VqXcg0Grrt4F"
pwrd=""
topic="v1/devices/me/telemetry"
attributes="v1/devices/me/attributes"
url="sisconet.com.ar"
do_connect()

#seteo de hora
for i in range(0,5):
    try:
        t = ntptime.time()
        i=5
	FAIL_settime=0
    except:
        print("error al configurar hora")#volver a intentar cada tanto
	FAIL_settime=1
	
try:
    print (t)
except:
    t=0
    FAIL_settime=1 #volvler a tratar si no pudo configurar la hora al principio (IMPLEMENTAR)
    
tm = utime.localtime(t + dt)
tm = tm[0:3] + (0,) + tm[3:6] + (0,)
machine.RTC().datetime(tm) 

Pin_STS=machine.Pin(16,machine.Pin.IN)

#configuracion del sensor de temperatura humedad
d = dht.DHT11(machine.Pin(0))

#configuracion del i2c para sensor de luz
Pin_sda=machine.Pin(5)
Pin_scl=machine.Pin(4)
i2c = machine.I2C(freq=400000,sda=Pin_sda,scl=Pin_scl) 
i2c.writeto(35, b'\x10')
ina=INA226(i2c)
ina.set_calibration_custom(calValue=512, config=0x4127)
#configuracion de MQTT
#c = MQTTClient("umqtt_client", "test.mosquitto.org")
#c = MQTTClient("umqtt_client2",'192.168.43.188')
c = MQTTClient("sensor"+str(Nsens),server=url,port=1883,user=user,password=pwrd,keepalive=30)
c.set_callback(sub_cb)
for i in range(0,5):
    try:
        c.connect()
        i=5
    except:
        print("fallo en conexion MQTT")
  
##configuracion timer        
tim = machine.Timer(1)
tim2 = machine.Timer(2)
led = machine.Pin(2, mode=machine.Pin.OUT)
tim2.init(period=1000,callback=Sub_timer2_cb)
print("timers OK")      
if scan_state==b'on':
    tim.init(period=scan_rate,callback=Scan_callback)
if scan_state==b'off':
    tim.deinit()
##        
print ('Inicio de medicion')
x=0
#loop principal

print("Suscribirse a TOPIC")        
c.subscribe(attributes)
print(attributes)  

while True:
    utime.sleep(1)
    
    
# I2c solo puedo usarlo en pines 4 y 5, tengo que mover el PWM a otro lado 
'+IDEUPcontent+''+IDEUPcontent+'

'+IDEUPcontent+'