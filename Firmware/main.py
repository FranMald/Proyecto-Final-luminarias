import dht
import machine
from robust import MQTTClient
#from umqtt.robust import MQTTClient
from wifi import do_connect
import ujson
import utime
import ntptime
import random
from ina226 import INA226
import esp

def web_page():
  global sta, APS
  APS=list()
  list_aps=""
  aps_near=sta.scan()
  i=0
  for AP in aps_near[0:10]:
    APS.append(AP[0].decode('utf-8'))
    list_aps=list_aps + '<option value="' + AP[0].decode('utf-8') +'">'+ AP[0].decode('utf-8') + '</option>'
    i=i+1
  f = open('Home.html')
  html=f.read()
  f.close()
  html=html.replace("@REDES@",list_aps)
  return html

def web_page_2():
  f = open('back.html')
  html=f.read()
  f.close()
  f = open('Config.txt', 'r')
  Config=f.read()
  f.close()
  html=html.replace("@CONFIG@",Config)
  return html

def sub_cb(topic, msg):
    global tim,tim2, PWM,scan_state,scan_rate,AVG,Nsens,muestras
    print(topic)
    ATTR=ujson.loads(msg)
    for i in range (0,len(ATTR)):
        if ATTR.get('Scan status')!=None:                        #habilitar o deshabilitar el scaneo y reporte temporizado
            if ATTR.get('Scan status')=='true':
                print(msg)
                tim.deinit()
                tim.init(period=scan_rate,callback=Scan_callback)
                scan_state='on'
            if ATTRget('Scan status')=='false':
                print(msg)
                tim.deinit()
                scan_state='off'
        if ATTR.get('Scan Rate')!=None:                        #configuracion del Scan Rate
            scan_rate=int(ATTR.get('Scan Rate'))
            if scan_state=='on':
                #tim.deinit()
                tim2.deinit()
                tim.init(period=scan_rate,callback=Scan_callback)        
            print(scan_rate)
        #if topic==b's/'+str(Nsens)+b'/CONFIG/ON_DEMAND':                   #pedido de medicion on demand
        #    Scan_callback(tim)
        if ATTR.get('PWM')!=None:                         # ingreso de valor del PWM
            PWM=int(ATTR.get('PWM'))
            ctrl_PWM.duty(PWM)
            print(PWM)
        if ATTR.get('Muestras Promedio')!=None:                         # ingreso de cantidad de muestras promedidadas por cada reporte (minimo 1 muestra por segundo)
            AVG=int(ATTR.get('Muestras Promedio'))
            muestras=[]
            print(AVG)
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
    Config='{"PWM":"'+str(PWM)+'" ,'+'"Muestras Promedio":"'+ str(AVG)+'" ,'+'"Scan Rate":"'+ str(scan_rate) +'" ,'+ '"Scan status":"'+str(scan_state) +'" '+'}'
    f = open('Config.txt', 'w')
    f.write(Config)
    f.close()
    tim2.init(period=1000,callback=Sub_timer2_cb)
    
def Sub_timer2_cb(timer):
    global c
    #print("Check")
    try:
        c.check_msg()
    except:
        print("Error en MQTT")
    
def Scan_callback(timer):                # calback para el escaneo de los sensores (agregar posibilidad de realizar promedio de mediciones)    
    global d,c,values,Pin_STS,tags,x,muestras
    try:                        #medicion de temperatura y humedad
        d.measure()
        values[1]=d.temperature()
        values[2]=d.humidity()
    except:
        values[1]="error"
        values[2]="error"
    
    values[5]=int.from_bytes(i2c.readfrom(35, 2),"big")/1.2     #medicion de luminosidad
    values[6]=Pin_STS.value()                                   #acuse de estado de lampara (bit interno)
#    #medicion de tension y corriente
    values[3]=ina.bus_voltage
    values[4]=ina.current
#    #a=utime.localtime()
#    #values[0]=str(a[0])+'/'+str(a[1])+'/'+str(a[2])+' '+str(a[3])+':'+str(a[4])+':'+str(a[5])
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
        #print(OUT)
        c.publish(topic, OUT)
    except:
        #print ('fallo de publish')
        c.connect()

pin_EN= machine.Pin(13,machine.Pin.OUT)
pin_EN.off()
pin_BOARD= machine.Pin(2,machine.Pin.OUT)
pin_BOARD.on()

dict = {}
dict2 = {}
#tags=['temperature','humidity','voltage','current','state','timestamp']
tags_config=['timestamp','SCAN','RATE','AVG','PWM']
values_config=['0','0','0','0','0']
tags=['timestamp','TEMP','HUM','V','I','LUM','STS']
values=['0','0','0','0','0','0','0']
muestras=[['0','0','0','0','0']]
Nsens=6

dt=-3600*3

#user="P0tW2dm4VqXcg0Grrt4F"
user="fTjc36ri98tEl7PK6lId"
#user="N5zwdPO48A6SgPiQ2jbq"
pwrd=""
topic="v1/devices/me/telemetry"
attributes="v1/devices/me/attributes"
url="sisconet.com.ar"
#url="test.mosquitto.org"
#url="68.183.146.169"

#carga de parametros desde archivo
f = open('Config.txt')
ATTR=ujson.loads(f.read())
ATTR_txt=ujson.dumps(ATTR)
PWM=int(ATTR.get('PWM'))
AVG=int(ATTR.get('Muestras Promedio'))
scan_rate=int(ATTR.get('Scan Rate'))
scan_state=ATTR.get('Scan status')
user=ATTR.get('mqtt_user')
pword=ATTR.get('mqtt_pword')
url=ATTR.get('mqtt_url')
wifi_ssid=ATTR.get('wifi_ssid')
wifi_pword=ATTR.get('wifi_pword')

f.close()
auxi=do_connect(wifi_ssid,wifi_pword)
print (auxi)
if auxi:

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

    #configuracion PWM
    pin_PWM= machine.Pin(2)
    ctrl_PWM = machine.PWM(pin_PWM)
    ctrl_PWM.freq(100)
    ctrl_PWM.duty(PWM)

    #configuracion del sensor de temperatura humedad
    d = dht.DHT11(machine.Pin(0))

    #configuracion del i2c para sensor de luz
    Pin_sda=machine.Pin(5)
    Pin_scl=machine.Pin(4)
    i2c = machine.I2C(freq=400000,sda=Pin_sda,scl=Pin_scl) 
    i2c.writeto(35, b'\x10')
    ina=INA226(i2c,addr=0x40)
    ina.set_calibration_custom(calValue=512, config=0x4127)

    #configuracion de MQTT
    c = MQTTClient("sensor"+str(Nsens),server=url,port=1883,user=user,password=pwrd,keepalive=30)
    c.set_callback(sub_cb)
    c.connect()
    #for i in range(0,5):
    #    try:
    #        c.connect()
    #        i=5
    #    except:
    #        print("fallo en conexion MQTT")

    #loop principal

    #configuracion timer        
    tim = machine.Timer(1)
    tim2 = machine.Timer(2)
    tim2.init(period=1000,callback=Sub_timer2_cb)
    print("timers OK")      
    if scan_state=='on':
        tim.init(period=scan_rate,callback=Scan_callback)
    if scan_state=='off':
        tim.deinit()
    ##        
    print ('Inicio de medicion')

    #print(ATTR_txt)
    #c.publish(attributes, ATTR_txt)


    print("Suscribirse a TOPIC")        
    c.subscribe(attributes)
    print(attributes) 

    pin_EN.on()
print("memoria libre ANTES: "+str(esp.freemem()))
print("Abrir socket")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(1)

while True:    
    utime.sleep_ms(1)
    global APS
    conn, addr = s.accept()
    print("memoria libre: "+str(esp.freemem()))
    form_data=[[0,0],[0,0],[0,0]]
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    request = str(request)
    request=request.split()
    print(request)
    request=request[1].split("?")
    print(request[0])
    if request[0]=='/':
        print("HOME")
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
    elif request[0]=='/Submit':
        parametros=request[1]
        parametros=parametros.replace('=','":"')
        parametros=parametros.replace('&','","')
        parametros='{"'+parametros+'"}'
        config_new=ujson.loads(parametros)
        f = open('Config.txt')
        config_old=ujson.loads(f.read())
        f.close()
        config_old["wifi_ssid"]=config_new["wifi_ssid"].replace('+',' ')
        config_old["wifi_pword"]=config_new["wifi_pword"]
        config_old["id"]=config_new["id"]
        config_old["mqtt_user"]=config_new["mqtt_user"]
        config_old["mqtt_pword"]=config_new["mqtt_pword"]
        config_old["mqtt_url"]=config_new["mqtt_url"]
        config_str=ujson.dumps(config_old)
        #print(config_str)
        f = open('Config.txt', 'w')
        f.write(config_str)
        f.close() 
        response = web_page_2()# buscar forma de insertar IP en href para que vuelva al inicio 
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        utime.sleep_ms(1000)
        conn.close()
    elif request[0]=='/Reset':
        print ("--------------------reset----------------------")
        machine.reset()
    #print('Content = %s' % request)
    
    response=""
    request=""
    parametros=[]
    print("memoria libre despues: "+str(esp.freemem()))
#final del codigo 