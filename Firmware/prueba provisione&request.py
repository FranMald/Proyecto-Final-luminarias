from wifi import do_connect
from simple import MQTTClient
import ujson
global TOKEN
import os

def response_cb(topic_cb, msg):
    global TOKEN
    response=ujson.loads(msg)
    if response.get('status')=="SUCCESS":
        TOKEN=response.get('credentialsValue')

try:
    f=open('conf_net.txt')
    print("configurado")
    f.close()
except:
           
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(1)

    while True: 
        global APS   
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
            
        if conf.get('SSID')!=None and conf.get('PWORD')!=None and conf.get('URL')!=None and conf.get('TOKEN')!=None:
            print("guardar")
            f = open('conf_net.txt','w')
            f.write(ujson.dumps(conf))
            f.close() 
            
        if conf.get('command')=="reset":
            print("RESET")
            f = open('conf_net.txt')
            net_conf=ujson.loads(f.read())
            f.close()
            if net_conf.get('TOKEN')=="provision":
                print('provision')
                do_connect(net_conf.get('SSID'),net_conf.get('PWORD'))
                c = MQTTClient("provision",server=net_conf.get('URL'),user="provision",password="",port=1883,keepalive=30)
                c.set_callback(response_cb)
                c.connect()
                c.subscribe("/provision/response")
                f=open('conf_provision.txt')
                PROVISION_REQUEST = ujson.loads(f.read())
                if net_conf.get('NAME')!="":
                    PROVISION_REQUEST['deviceName']=net_conf.get('NAME')
                c.publish("/provision/request",ujson.dumps(PROVISION_REQUEST))
                c.wait_msg()
                print(TOKEN)
                net_conf['TOKEN']=TOKEN
                f = open('conf_net.txt','w')
                f.write(ujson.dumps(net_conf))
                f.close() 
            machine.reset()
        
