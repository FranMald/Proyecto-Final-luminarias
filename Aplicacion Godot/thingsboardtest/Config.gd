extends Node

onready var SSID_input := $VBoxContainer2/LineEdit
onready var PWORD_input := $VBoxContainer2/LineEdit2
onready var URL_input := $VBoxContainer2/LineEdit3
onready var DEVTOKEN_input := $VBoxContainer2/LineEdit4
onready var NAME_input := $VBoxContainer2/LineEdit5
onready var DEVTOKEN_label := $VBoxContainer2/Label4
onready var Provision_check := $VBoxContainer2/CheckButton
onready var ESTADO:= $ESTADO
onready var provision_request := $ProvisionRequest
# Declare member variables here. Examples:
# var a = 2
# var b = "text"


# Called when the node enters the scene tree for the first time.
func _ready():
	pass # Replace with function body.-

# Called every frame. 'delta' is the elapsed time since the previous frame.
#func _process(delta):
#	pass


func _on_Back_pressed():
	get_tree().change_scene_to(load('res://inicio.tscn'))

func _on_CheckButton_pressed():
	if Provision_check.pressed:
		DEVTOKEN_input.editable=false
		DEVTOKEN_input.text="provision"
		NAME_input.editable=true
		NAME_input.text=""
	else:
		DEVTOKEN_input.editable=true
		DEVTOKEN_input.text=""
		NAME_input.editable=false
		NAME_input.text=""


func _on_Load_Config_pressed():
	if not (SSID_input.text=="" or PWORD_input.text=="" or URL_input.text==""  or (DEVTOKEN_input.editable and DEVTOKEN_input.text=="")):
		print("SI")
		var headers = ["Configuracion"]
		var request_data = '{"wifi_ssid": "'+SSID_input.text+'","wifi_pword": "'+ PWORD_input.text +'","mqtt_url": "'+URL_input.text+'","mqtt_user": "'+DEVTOKEN_input.text+'","NAME": "'+NAME_input.text+'"}'
		print (request_data)
		#provision_request.request("http://192.168.0.17",headers,true,HTTPClient.METHOD_GET, request_data)
		ESTADO.text="Esperando Respuesta de Dispositivo"
		provision_request.request("http://192.168.4.1",headers,true,HTTPClient.METHOD_GET, request_data)
	else:
		print("Cargar Datos necesarios")
		
func _on_Reset_pressed():
	var headers = ["Configuracion"]
	var request_data = '{"command": "reset"}'
	ESTADO.text="Esperando Respuesta de Dispositivo"
	#provision_request.request("http://192.168.0.17",headers,true,HTTPClient.METHOD_GET, request_data)
	provision_request.request("http://192.168.4.1",headers,true,HTTPClient.METHOD_GET, request_data)

func _on_ProvisionRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		ESTADO.text="OK"
		print (headers)
		print (result)
		print (str(body))

