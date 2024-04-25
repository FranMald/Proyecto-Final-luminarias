extends Node

onready var customer_input := $VBoxContainer/LineEdit3
onready var username_input := $VBoxContainer/LineEdit
onready var password_input := $VBoxContainer/LineEdit2

onready var provision_request := $ProvisionRequest
onready var login_request := $LoginRequest
onready var http_request := $HTTPRequest
onready var customer_request := $CustomerRequest
onready var profile_request := $ProfileRequest

onready var loading := $Loading

onready var G = get_node("/root/Global")

func _ready():
	if G.token != "":
		$Config.disabled=false
		$Telemetria.disabled=false
	pass

func _on_Telemetria_pressed():
	get_tree().change_scene_to(load('res://Control.tscn'))

func _on_Config_pressed():
	get_tree().change_scene_to(load('res://Config.tscn'))

func _on_Button_pressed():
	var query = JSON.print({"username" : username_input.text, "password" : password_input.text})
	print(query)
	var header := ["Content-Type: application/json", "Accept: application/json"]
	login_request.request("https://demo.thingsboard.io/api/auth/login", header, true, HTTPClient.METHOD_POST, query)
	loading.text="Solictando Token..."

func _on_LoginRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		print(json.result)
		G.token = "Bearer " + json.result["token"]
		request_keys(G.token)
	if response_code == 401:
		loading.text="Fallo de inicio de sesion"
		$Config.disabled=true
		$Telemetria.disabled=true
		G.token=""
		G.provisionDeviceKey = ""
		G.provisionDeviceSecret = ""

func _on_Button2_pressed():
	username_input.text="maldonado.accari.f@gmail.com"
	password_input.text="ContraseniaThings"

func _on_ProfileRequest_request_completed(result, response_code, headers, body):
	var __my_file := File.new()
	var __my_text := str("This is line one.")
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		#print(json.result)
		__my_file.open("res://Test.txt", __my_file.WRITE)
		assert(__my_file.is_open())
		__my_file.store_string(body.get_string_from_utf8())
		__my_file.close()
		G.provisionDeviceKey=json.result.provisionDeviceKey
		G.provisionDeviceSecret=json.result.profileData.provisionConfiguration.provisionDeviceSecret
		$Config.disabled=false
		$Telemetria.disabled=false

func request_keys(token):
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	profile_request.request("https://demo.thingsboard.io/api/deviceProfile/04819920-bd8e-11eb-a311-cf80d7127bfd", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solictando Provision Keys ..."

