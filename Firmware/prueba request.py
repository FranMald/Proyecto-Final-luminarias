from wifi import do_connect
import ujson

do_connect("DAVITELWIFI34778","Ja5Achoh")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(1)

while True: 
    global APS   
    #se espera aqui a que se ingrese a la web
    conn, addr = s.accept()
    #print("memoria libre: "+str(esp.freemem()))
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
    #
    
    