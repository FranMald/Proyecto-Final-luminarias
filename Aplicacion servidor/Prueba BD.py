import sqlite3
import ssl
import sys
import json
import paho.mqtt.client

def on_connect(client, userdata, flags, rc):
	print('connected (%s)' % client._client_id)
	client.subscribe(topic='s/#')

def on_message(client, userdata, message):
	print('------------------------------')
	print(message.payload)
	Nsens=message.topic[2]								#obtiene el numero del sensor
	if message.topic=='s/'+str(Nsens)+'/MEASURE':		#verifica si recibe un mensaje en el topic de medicion
		print(message.topic)
		dict = json.loads(message.payload)
		conn = sqlite3.connect('tele_ilum')
		c = conn.cursor()
		valores=[(Nsens,dict['timestamp'],dict['TEMP'],dict['HUM'],dict['V'],dict['I'],dict['LUM'],dict['STS'])]
		c.executemany('INSERT INTO valores VALUES (?,?,?,?,?,?,?,?)', valores)	
	if message.topic=='s/'+str(Nsens)+'/ACTUAL':			#verifica si recibe un mensaje en el topic de configuracion
		print(message.topic)
		dict = json.loads(message.payload)
		conn = sqlite3.connect('tele_ilum')
		c = conn.cursor()
		config=[(Nsens,dict['timestamp'],dict['SCAN'],dict['RATE'],dict['AVG'],dict['PWM'])]
		c.executemany('INSERT INTO configuraciones VALUES (?,?,?,?,?,?)', config)	
	conn.commit()

def main():
	client = paho.mqtt.client.Client(client_id='Python3', clean_session=False)
	client.on_connect = on_connect
	client.on_message = on_message
	client.connect(host='68.183.146.169', port=1883)
	client.loop_forever()

if __name__ == '__main__':
	main()

try:
	while True:
		time.sleep(1)
		
except KeyboardInterrupt:
	print ("exiting")
	client.disconnect()
	client.loop_stop()
	f.close()	
