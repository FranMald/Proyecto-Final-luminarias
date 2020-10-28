import pymysql
import ssl
import sys
import json
import paho.mqtt.client as mqtt

#conn = pymysql.connect(host="localhost", user="root", passwd="aa153486", database="ilum")
conn = pymysql.connect(host="68.183.146.169", user="root", passwd="aa153486", database="ilum")
cursor = conn.cursor()

def on_connect(client, userdata, flags, rc):
	print('connected (%s)' % client._client_id)
	client.subscribe(topic='s/#')

def on_message(client, userdata, message):
    print('------------------------------')
    print(message.payload)
    Nsens=message.topic[2]								#obtiene el numero del sensor
    if message.topic=='s/'+str(Nsens)+'/MEASURE':		#verifica si recibe un mensaje en el topic de medicion
        print(message.topic)
        dic = json.loads(message.payload)
        sql = "INSERT INTO Valores VALUES ('{}','{}','{}','{}','{}','{}','{}','{}');"
        query = sql.format(Nsens, dic['timestamp'], dic['TEMP'], dic['HUM'], dic['V'], dic['I'], dic['LUM'], dic['STS'])
        print(query)
        cursor.execute(query)
        conn.commit()
    if message.topic=='s/'+str(Nsens)+'/ACTUAL':			#verifica si recibe un mensaje en el topic de configuracion
        print(message.topic)
        dic = json.loads(message.payload)
        sql = "INSERT INTO Configuracion VALUES ('{}','{}','{}','{}','{}','{}');"
        query = sql.format(Nsens,dic['timestamp'],dic['SCAN'],dic['RATE'],dic['AVG'],dic['PWM'])
        print(query)
        cursor.execute(query)
        conn.commit()
    #if message.topic=='s/'+str(Nsens)+'/COORD': #para la tabla de configuraciones del sensor 
    #   print(message.topic)
	#   dic = json.loads(message.payload)
    # 
    #   config=[(Nsens,dic['id'],dic['nombre'],dic['cooredenadas'])]
    #   cursor.executemany('INSERT INTO configuraciones VALUES (?,?,?)',sensores)
    #conn.commit()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
#client.connect("localhost", 1883, 60)
client.connect("68.183.146.169", 1883, 60)

client.loop_forever()

