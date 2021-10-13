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
  for AP in aps_near[0:5]:
    APS.append(AP[0].decode('utf-8'))
    list_aps=list_aps + '<option value="' + AP[0].decode('utf-8') +'">'+ AP[0].decode('utf-8') + '</option>'
    i=i+1
  f = open('Home.html')
  html=f.read()
  f.close()
  html=html.replace("@REDES@",list_aps)
  f = open('Config.txt')
  ATTR=ujson.loads(f.read())
  f.close()
  ATTR_txt=ujson.dumps(ATTR)
  #html=html.replace("@wifi_ssid@",ATTR.get('wifi_ssid'))
  #html=html.replace("@wifi_pword@",ATTR.get('wifi_pword'))
  #html=html.replace("@mqtt_url@",ATTR.get('mqtt_url'))
  #html=html.replace("@mqtt_pword@",ATTR.get('mqtt_pword'))
  #html=html.replace("@mqtt_user@",ATTR.get('mqtt_user'))
  #html=html.replace("@id@",ATTR.get('id'))

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

#rutina que se ejecuta cuando se detecta un nuevo mensaje en un topic suscripto
def sub_cb(topic_cb, msg):
    global tim,tim2, PWM,light_state,scan_state,scan_rate,AVG,muestras,SUM,ATTR,topic_last
    tim2.deinit()
    print(topic_cb)
    topic_last=topic_cb
    print(msg)
    ATTR=ujson.loads(msg)
    print(ATTR)
    #respuesta a  la consuta de PWM desde le servidor
    if ATTR.get('method')=='getPWM':
	topic_last=str(topic_last)[2:-1]
        topic_last=topic_last.replace("request","response")
        c.publish(topic_last,str(PWM))
        print(str(PWM))
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
    #ejecucion del comando de seteo de PWM
    if ATTR.get('method')=='setPWM':
        PWM=int(ATTR.get('params'))
        ctrl_PWM.duty(PWM)
        print(PWM)
    #ejecucion del comando de SCAN ON/OFF   
    if ATTR.get('method')=='setScanStat':                        
        if ATTR.get('params')==True:
            print("Scan ON")
            tim.deinit()
            tim.init(period=scan_rate,callback=Scan_callback)
            scan_state='on'
        if ATTR.get('params')==False:
            print("Scan OFF")
            tim.deinit()
            scan_state='off'
    #ejecucion del comando de LIGHT ON/OFF         
    if ATTR.get('method')=='setLightStat':                        
        if ATTR.get('params')==True:
            print("Light ON")
            pin_EN.on()
            light_state='on' 
        if ATTR.get('params')==False:
            print("Light OFF")
            pin_EN.off()
            light_state='off'  
    #funcion provisoria que detienen el escaneo totalmente        
    if ATTR.get('STOP')!=None: 
        tim.deinit()
        tim2.deinit()
        STOP=1
        print ("STOP")
        
    #modificacion de tiempo de escaneo
    if ATTR.get('Scan Rate')!=None:                        
        scan_rate=int(ATTR.get('Scan Rate'))
        if scan_state=='on':
            #tim.deinit()
            tim2.deinit()
            tim.init(period=scan_rate,callback=Scan_callback)        
        print(scan_rate)
    #modificacion de muestras para promedio    
    if ATTR.get('Muestras_AVG')!=None:    
    	#recupera el valor enviado                    
        AVG=int(ATTR.get('Muestras_AVG'))
        print(AVG)
        #inicializa el valor de SUM
        SUM=[0,0,0,0,0,0]
        #se promedia todo el contenido del buffer de muestras actuales y se ingresa ese valor al primer elemento del nuevo buffer, borrando las anteriores
        for muestra in muestras:
            for i in range(0,5):
                SUM[i]=float(SUM[i])+float(muestra[i])
        for i in range(0,5):
            SUM[i]=SUM[i]/len(muestras)               
        muestras=[SUM]
        print(muestras)
        print(AVG)
    #otra manera para modificar el PWM    
    if ATTR.get('PWM')!=None:                         
        PWM=int(ATTR.get('PWM'))
        ctrl_PWM.duty(PWM)
        print(PWM)
    #se modifica el archivo con los nuevos parametros    
    f = open('Config.txt', 'r')
    config_old=ujson.loads(f.read())
    print(config_old)
    config_old["PWM"]=str(PWM)
    config_old["Muestras_AVG"]=str(AVG)
    config_old["Scan Rate"]=str(scan_rate) 
    config_old["Scan status"]=str(scan_state) 
    config_old["Light status"]=str(light_state) 
    config_str=ujson.dumps(config_old)
    f.close()
    f = open('Config.txt', 'w')
    f.write(config_str)
    f.close()
    #se publica los atriubutos mas recientes
    c.publish(attributes,config_str)
    if STOP==0:
        tim2.init(period=100,callback=Sub_timer2_cb)
    
def Sub_timer2_cb(timer):
    global d,c,values,Pin_STS,tags,x,muestras
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
    
    #se agrega la medicion actual al buffer
    muestras.append([values[1],values[2],values[3],values[4],values[5],values[6]])
    #si el largo del buffer supera el numero de muestras establecido se elimina el primer elemento
    if len(muestras) > AVG:
        muestras=muestras[1:]  
    
    #se verifica si se recibio algun mensaje por los topics
    try:
        c.check_msg()
    except:
        print("Error en MQTT")

    if STOP==0:
        tim2.init(period=100,callback=Sub_timer2_cb)

# calback para el escaneo de los sensores
def Scan_callback(timer):                    
    global d,c,values,Pin_STS,tags,x,muestras
    tim2.deinit()                                
    values[0]=utime.time()
    SUM=[0,0,0,0,0,0]
    #print(muestras)
    #calculo del promedio de todas las muestras del buffer
    for muestra in muestras:
        for i in range(0,6):
            #print(SUM)
            SUM[i]=SUM[i]+muestra[i]
    for i in range(0,6):
        SUM[i]=SUM[i]/len(muestras)
    print(SUM)
    
    values[1]=SUM[0]
    values[2]=SUM[1]
    values[3]=SUM[2]
    values[4]=SUM[3]
    values[5]=SUM[4]
    values[6]=SUM[5]
    values[7]=len(muestras)
    #parseo json
    for i in range(0,len(tags)):
        dict[tags[i]] = values[i]
        OUT=ujson.dumps(dict)
    #publica en topic
    muestras=[]    
    try:
        print(OUT)
        c.publish(topic_tm, OUT)
    except:
        #print ('fallo de publish')
        c.connect()
    if STOP==0:
        tim2.init(period=100,callback=Sub_timer2_cb)

#--------------- aqui comienza el programa----------------------
pin_EN= machine.Pin(13,machine.Pin.OUT)
pin_EN.off()
pin_BOARD= machine.Pin(2,machine.Pin.OUT)
pin_BOARD.on()

dict = {}
dict2 = {}
tags=['timestamp','TEMP','HUM','V','I','LUM1','LUM2','MUESTRAS']
values=[0,0,0,0,0,0,0,0]
muestras=[[0,0,0,0,0,0]]
STOP=0

topic_tm="v1/devices/me/telemetry"
attributes="v1/devices/me/attributes"
RPC_commands="v1/devices/me/rpc/request/+"

#carga de parametros de configuracion desde archivo
f = open('Config.txt')
ATTR=ujson.loads(f.read())
ATTR_txt=ujson.dumps(ATTR)
PWM=int(ATTR.get('PWM'))
AVG=int(ATTR.get('Muestras_AVG'))
scan_rate=int(ATTR.get('Scan Rate'))
scan_state=ATTR.get('Scan status')
light_state=ATTR.get('Light status')
user=ATTR.get('mqtt_user')
pword=ATTR.get('mqtt_pword')
url=ATTR.get('mqtt_url')
wifi_ssid=ATTR.get('wifi_ssid')
wifi_pword=ATTR.get('wifi_pword')
id_sensor=ATTR.get('id')
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

    #configuracion de MQTT
    c = MQTTClient("sensor"+str(id_sensor),server=url,user=user,password=pword,keepalive=30)
    c.set_callback(sub_cb)
    c.connect()
    #for i in range(0,5):
    #    try:
    #        c.connect()
    #        i=5
    #    except:
    #        print("fallo en conexion MQTT")

    #loop principal

    #configuracion timers        
    tim = machine.Timer(1)
    tim2 = machine.Timer(2)   
    if scan_state=='on':
        tim.init(period=scan_rate,callback=Scan_callback)
        print("SCAN ON") 
    if scan_state=='off':
        tim.deinit()
        print("SCAN OFF") 
    tim2.init(period=100,callback=Sub_timer2_cb)
    print("timers OK")  
    
    #suscribirse a los topic de atributos y comandos RPC
    print("Suscribirse a TOPIC")     
    c.subscribe(RPC_commands)   
    c.subscribe(attributes)
    #publicar configuracion actual
    c.publish(attributes,ATTR_txt)
    print(attributes) 
    
    if light_state=='on':
        pin_EN.on()
    if light_state=='off':
        pin_EN.off()
        
print("memoria libre ANTES: "+str(esp.freemem()))
print("Abrir socket")
#se abre socket para acceso a la pagina embebida
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(1)

while True: 
    global APS   
    utime.sleep_ms(1)
    #se espera aqui a que se ingrese a la web
    conn, addr = s.accept()
    print("memoria libre: "+str(esp.freemem()))
    form_data=[[0,0],[0,0],[0,0]]
    print('Got a connection from %s' % str(addr))
    request = str(conn.recv(1024))
    request=request.split()
    print(request)
    request=request[1].split("?")
    print(request[0])
    if request[0]=='/':
    	#se responde el request del home con el formulario de configuracion
        print("HOME")
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        conn.close()
    elif request[0]=='/Submit':
    	#parsear la configuracion que ingresa desde el request
        parametros=request[1]
        parametros=parametros.replace('=','":"')
        parametros=parametros.replace('&','","')
        parametros='{"'+parametros+'"}'
        config_new=ujson.loads(parametros)
        #se carga la configuracion anterior desde el archivo
        f = open('Config.txt')
        config_old=ujson.loads(f.read())
        f.close()
        #se actualizan los parametros
        config_old["wifi_ssid"]=config_new["wifi_ssid"].replace('+',' ')
        config_old["wifi_pword"]=config_new["wifi_pword"]
        config_old["id"]=config_new["id"]
        config_old["mqtt_user"]=config_new["mqtt_user"]
        config_old["mqtt_pword"]=config_new["mqtt_pword"]
        config_old["mqtt_url"]=config_new["mqtt_url"]
        config_str=ujson.dumps(config_old)
        #print(config_str)
        #se escriben en el archivo
        f = open('Config.txt', 'w')
        f.write(config_str)
        f.close() 
        #se responde con una pagina de confirmacion
        response = web_page_2() 
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        utime.sleep_ms(1000)
        conn.close()        
    elif request[0]=='/Reset':
    	#se resetea el dispositivo
        print ("--------------------reset----------------------")
        machine.reset()
    #print('Content = %s' % request)
    #se vacia la memoria
    response=""
    request=""
    parametros=[]
    print("memoria libre despues: "+str(esp.freemem()))
#final del codigo 