import dht
import machine
from robust import MQTTClient
from wifi import do_connect
import ujson
import utime
import ntptime
import random
from ina226 import INA226
import esp
from PID import PID


#rutina que se ejecuta cuando se detecta un nuevo mensaje en un topic suscripto
def response_cb(topic_cb, msg):
    global TOKEN
    response=ujson.loads(msg)
    if response.get('status')=="SUCCESS":
        TOKEN=response.get('credentialsValue')

def sub_cb(topic_cb, msg):
    global tim,tim2, PWM,light_state,scan_state,scan_rate,AVG,muestras,SUM,ATTR,topic_last,INH,PID_state,TOKEN
    INH=0
    tim2.deinit()
    print(msg)
    print(topic_cb)
    topic_last=topic_cb
    ATTR=ujson.loads(msg)
    #respuesta a  la consuta de PWM desde le servidor
    if ATTR.get('method')=='getPWM':
        topic_last=str(topic_last)[2:-1]
        topic_last=topic_last.replace("request","response")
        c.publish(topic_last,str(PWM))
    #respuesta a  la consuta de estado de escaneo desde el servidor
    if ATTR.get('method')=='getScanStat':
        topic_last=str(topic_last)[2:-1]
        topic_last=topic_last.replace("request","response")
        if scan_state=='on':
            c.publish(topic_last,'true')
        if scan_state=='off':
            c.publish(topic_last,'false')
    #respuesta a  la consuta de estado de habilitaicon del controlador de leds desde el servidor        
    if ATTR.get('method')=='getLightStat':
        topic_last=str(topic_last)[2:-1]
        topic_last=topic_last.replace("request","response")
        if light_state=='on':
            c.publish(topic_last,'true')
        if light_state=='off':
            c.publish(topic_last,'false')
    #respuesta a la consulta de estado del PID
    if ATTR.get('method')=='getPIDStat':
        topic_last=str(topic_last)[2:-1]
        topic_last=topic_last.replace("request","response")
        if PID_state=='on':
            c.publish(topic_last,'true')
        if PID_state=='off':
            c.publish(topic_last,'false')
    #ejecucion del comando de seteo de PWM
    if ATTR.get('method')=='setPWM':
        PWM=int(ATTR.get('params'))
        ctrl_PWM.duty(PWM)
        print(PWM)
    #ejecucion del comando de SCAN ON/OFF   
    if ATTR.get('method')=='setScanStat':                        
        if ATTR.get('params')==True:
            tim.deinit()
            tim.init(period=scan_rate,callback=Scan_callback)
            scan_state='on'
        if ATTR.get('params')==False:
            tim.deinit()
            scan_state='off'
    #ejecucion del comando de LIGHT ON/OFF         
    if ATTR.get('method')=='setLightStat':                        
        if ATTR.get('params')==True:
            pin_EN.on()
            light_state='on' 
        if ATTR.get('params')==False:
            pin_EN.off()
            light_state='off'  
    #ejecucion del comando de PID ON/OFF
    if ATTR.get('method')=='setPIDStat':                        
        if ATTR.get('params')==True:
            PID_state='on' 
        if ATTR.get('params')==False:
            PID_state='off'
    #modificacion de tiempo de escaneo
    if ATTR.get('Scan Rate')!=None:                        
        scan_rate=int(ATTR.get('Scan Rate'))
        if scan_state=='on':
            tim.init(period=scan_rate,callback=Scan_callback)        
    #modificacion de muestras para promedio    
    if ATTR.get('Muestras_AVG')!=None:    
        #recupera el valor enviado                    
        AVG=int(ATTR.get('Muestras_AVG'))
        SUM=[0,0,0,0,0,0]
        #se promedia todo el contenido del buffer de muestras actuales y se ingresa ese valor al primer elemento del nuevo buffer, borrando las anteriores
        for muestra in muestras:
            for i in range(0,5):
                SUM[i]=float(SUM[i])+float(muestra[i])
        for i in range(0,5):
            SUM[i]=SUM[i]/len(muestras)               
        muestras=[SUM]
    #otra manera para modificar el PWM    
    if ATTR.get('PWM')!=None:                         
        PWM=int(ATTR.get('PWM'))
        ctrl_PWM.duty(PWM)
    #se modifica el archivo con los nuevos parametros    
    f = open('conf_ctrl.txt', 'r')
    config_old=ujson.loads(f.read())
    f.close()
    print(config_old)
    config_old["PWM"]=str(PWM)
    config_old["Muestras_AVG"]=str(AVG)
    config_old["Scan Rate"]=str(scan_rate) 
    config_old["Scan status"]=str(scan_state) 
    config_old["Light status"]=str(light_state)
    config_old["PID_state"]=str(PID_state)  
    config_str=ujson.dumps(config_old)
    f = open('conf_ctrl.txt', 'w')
    f.write(config_str)
    f.close()
    #se publica los atriubutos mas recientes
    c.publish(attributes,config_str)
    INH=1
    tim2.init(period=100,callback=Sub_timer2_cb)
    
def Sub_timer2_cb(timer):
    global d,c,values,Pin_STS,tags,x,muestras,INH,ctrl_PWM
    if INH:
        tim2.deinit()
        #medicion de temperatura y humedad
        try:                        
            d.measure()
            values[1]=d.temperature()
            values[2]=d.humidity()
        except:
            values[1]=values[1]
            values[2]=values[2]
        
        #medicion de luminosidad    
        values[5]=int.from_bytes(i2c.readfrom(35, 2),"big")/1.2  
        values[6]=int.from_bytes(i2c.readfrom(92, 2),"big")/1.2    
        #medicion de tension y corriente
        values[3]=ina.bus_voltage
        values[4]=ina.current
        
        if PID_state=="on":
            values[7]=pid(int(values[5]-values[6]))
            #print(values[7],values[5],values[6],values[5]-values[6])
            ctrl_PWM.duty(int(values[7]))
        else:
            values[7]=PWM
        #se agrega la medicion actual al buffer
        muestras.append([values[1],values[2],values[3],values[4],values[5],values[6],values[7]])
        #si el largo del buffer supera el numero de muestras establecido se elimina el primer elemento
        if len(muestras) > AVG:
            muestras=muestras[1:]  

        #se verifica si se recibio algun mensaje por los topics
        try:
            c.check_msg()
        except:
            print("Error en MQTT")
        tim2.init(period=100,callback=Sub_timer2_cb)
            
def Scan_callback(timer):
    global d,c,values,Pin_STS,tags,x,muestras
    tim2.deinit()     
    tim.init(period=scan_rate,callback=Scan_callback)     
    values[0]=utime.time()
    SUM=[0,0,0,0,0,0,0]
    #calculo del promedio de todas las muestras del buffer
    print(len(muestras))
    for muestra in muestras:
        for i in range(0,len(SUM)):
            SUM[i]=SUM[i]+muestra[i]
    for i in range(0,len(SUM)):
        SUM[i]=SUM[i]/len(muestras)
    print(SUM)
    values[1]=SUM[0]
    values[2]=SUM[1]
    values[3]=SUM[2]
    values[4]=SUM[3]
    values[5]=SUM[4]
    values[6]=SUM[5]
    values[7]=SUM[6]
    values[8]=len(muestras)
    #parseo json
    for i in range(0,len(tags)):
        dict[tags[i]] = values[i]
        OUT=ujson.dumps(dict)
    #publica en topic
    muestras=[]    
    try:
        c.publish(topic_tm, OUT)
    except:
        try:
            c.connect()
        except:
            machine.reset()
    tim2.init(period=100,callback=Sub_timer2_cb)
    
#si no encontro red y no se lo configuro despues de 1 min se resetea
def Reset_callback(timer): 
    machine.reset()
    
def leerCONF():
    global ATTR,user,pword, url,wifi_ssid,wifi_pword,id_sensor,PWM,AVG,scan_rate,scan_state,light_state,PID_state
    try:
        f = open('conf_net.txt')
        ATTR=ujson.loads(f.read())

        user=ATTR.get('mqtt_user')
        pword=""
        url=ATTR.get('mqtt_url')
        wifi_ssid=ATTR.get('wifi_ssid')
        wifi_pword=ATTR.get('wifi_pword')
        id_sensor=ATTR.get('NAME')
        f.close()

        f = open('conf_ctrl.txt')
        ATTR=ujson.loads(f.read())

        PWM=int(ATTR.get('PWM'))
        AVG=int(ATTR.get('Muestras_AVG'))
        scan_rate=int(ATTR.get('Scan Rate'))
        scan_state=ATTR.get('Scan status')
        light_state=ATTR.get('Light status')
        PID_state=ATTR.get('PID_state')
        f.close()
    except Exception as e:
        return e
    return 0

def abrirCONF():
    global APS  
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(1)

    while True: 
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request1 = str(conn.recv(1024))
        print(request1)
        request=request1[2:-1].split("\\r\\n")
        conf=ujson.loads(request[-1])
        print(request[-1])
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Configuracion\n')
        conn.send('Connection: close\n\n')
        conn.sendall("holo")
        conn.close()
            
        if conf.get('wifi_ssid')!=None and conf.get('wifi_pword')!=None and conf.get('mqtt_url')!=None and conf.get('mqtt_user')!=None:
            print("guardar")
            f = open('conf_net.txt','w')
            f.write(ujson.dumps(conf))
            f.close() 
            
        if conf.get('command')=="reset":
            print("RESET")
            f = open('conf_net.txt')
            net_conf=ujson.loads(f.read())
            f.close()
            if net_conf.get('mqtt_user')=="provision":
                print('provision')
                do_connect(net_conf.get('wifi_ssid'),net_conf.get('wifi_pword'))
                cp = MQTTClient("provision",server=net_conf.get('mqtt_url'),user="provision",password="",port=1883,keepalive=30)
                cp.set_callback(response_cb)
                cp.connect()
                cp.subscribe("/provision/response")
                f=open('conf_provision.txt')
                PROVISION_REQUEST = ujson.loads(f.read())
                if net_conf.get('NAME')!="":
                    PROVISION_REQUEST['deviceName']=net_conf.get('NAME')
                cp.publish("/provision/request",ujson.dumps(PROVISION_REQUEST))
                cp.wait_msg()
                print(TOKEN)
                net_conf['mqtt_user']=TOKEN
                f = open('conf_net.txt','w')
                f.write(ujson.dumps(net_conf))
                f.close() 
            machine.reset()
#--------------- comienzo del programa----------------------
    
try:
    f=open('conf_net.txt')
except:
    abrirCONF()

pin_EN= machine.Pin(13,machine.Pin.OUT)
pin_EN.off()
pin_BOARD= machine.Pin(2,machine.Pin.OUT)
pin_BOARD.on()

INH=1
dict = {}
dict2 = {}
tags=['timestamp','TEMP','HUM','V','I','LUM1','LUM2','PWM','MUESTRAS']
values=[0,0,0,0,0,0,0,0,0,0]
muestras=[[0,0,0,0,0,0,0,0]]
STOP=0
watchdog=600000
reset=0
topic_tm="v1/devices/me/telemetry"
attributes="v1/devices/me/attributes"
RPC_commands="v1/devices/me/rpc/request/+"
tim = machine.Timer(1)
tim2 = machine.Timer(2) 
#carga de parametros de configuracion desde archivo
f = open('conf_net.txt')

if leerCONF()==0:
    if do_connect(wifi_ssid,wifi_pword):
        #seteo de hora
        for i in range(0,5):
            try:
                t = ntptime.time()
                i=5
                FAIL_settime=0
            except:
                #volver a intentar cada tanto
                FAIL_settime=1  
        try:
            print (t)
        except:
            t=0
            FAIL_settime=1 #volvler a tratar si no pudo configurar la hora al principio (IMPLEMENTAR) 
        dt=-3600*3 # configuracion de zona horaria    
        tm = utime.localtime(t + dt)
        tm = tm[0:3] + (0,) + tm[3:6] + (0,)
        machine.RTC().datetime(tm) 
        #configurar GPIO16 como entrada
        Pin_STS=machine.Pin(16,machine.Pin.IN)
        #configuracion PWM
        pin_PWM= machine.Pin(2)
        ctrl_PWM = machine.PWM(pin_PWM)
        ctrl_PWM.freq(100)
        ctrl_PWM.duty(PWM)
        #configuracion del sensor de temperatura y humedad
        d = dht.DHT11(machine.Pin(0))
        #configuracion i2c
        Pin_sda=machine.Pin(5)
        Pin_scl=machine.Pin(4)
        i2c = machine.I2C(freq=400000,sda=Pin_sda,scl=Pin_scl) 
        #inicializacion de sensor de luz (modificar rango para facilitar el control)
        i2c.writeto(35, b'\x10')
        i2c.writeto(92, b'\x10')
        #inicializacion de sensor de tension y corriente
        ina=INA226(i2c,addr=0x40)
        ina.set_calibration_custom(calValue=512, config=0x4127)
        #Configuracion PID
        pid = PID(scale='s')
        pid.Kp=0.001
        pid.Ki=1
        pid.Kd=0
        pid.setpoint=0
        pid.output_limits = (10, 300) 
        #configuracion de MQTT
        c = MQTTClient("sensor"+str(id_sensor),server=url,user=user,password=pword,keepalive=30)
        c.set_callback(sub_cb)
        #c.connect()
        for i in range(0,5):
            try:
                c.connect()
                i=5
                reset=0
            except:
                #print("fallo en conexion MQTT")
                reset=1
        if reset==0:
        #configuracion timers        
            if scan_state=='on':
                tim.init(period=scan_rate,callback=Scan_callback)
            if scan_state=='off':
                tim.deinit()
            tim2.init(period=100,callback=Sub_timer2_cb)
            
            #suscribirse a los topic de atributos y comandos RPC
            c.subscribe(RPC_commands)   
            c.subscribe(attributes)
            #publicar configuracion actual
            c.publish(attributes,ujson.dumps(ATTR))

            if light_state=='on':
                pin_EN.on()
            if light_state=='off':
                pin_EN.off()
        else:
            reset=1
            tim.init(period=watchdog,callback=Reset_callback)
            abrirCONF()
    else:
        reset=1
        tim.init(period=watchdog,callback=Reset_callback)
        abrirCONF()
else:
    abrirCONF()
 
#final del codigo
