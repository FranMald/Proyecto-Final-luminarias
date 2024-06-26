extends Control

onready var provision_request := $ProvisionRequest
onready var http_request := $HTTPRequest
onready var login_request := $LoginRequest
onready var customer_request := $CustomerRequest
onready var telemetry_request := $TelemetryRequest
onready var attributes_request := $AttributesRequest
onready var profile_request := $ProfileRequest

onready var customer_input := $VBoxContainer/LineEdit3
onready var username_input := $VBoxContainer/LineEdit
onready var password_input := $VBoxContainer/LineEdit2
onready var data_hum := $GridContainer/Data_hum
onready var data_temp := $GridContainer/Data_temp
onready var data_i := $GridContainer/Data_I
onready var data_v := $GridContainer/Data_V
onready var data_lum1 := $GridContainer/Data_LUM1
onready var data_lum2 := $GridContainer/Data_LUM2
onready var loading := $Loading

onready var SSID_input := $VBoxContainer2/LineEdit
onready var PWORD_input := $VBoxContainer2/LineEdit2
onready var URL_input := $VBoxContainer2/LineEdit3
onready var DEVTOKEN_input := $VBoxContainer2/LineEdit4
onready var NAME_input := $VBoxContainer2/LineEdit5
onready var DEVTOKEN_label := $VBoxContainer2/Label4
onready var Provision_check := $VBoxContainer2/CheckButton

onready var ESTADO:= $ESTADO

onready var temp_gauge := $MeanGauge
onready var v_gauge := $MeanGauge2
onready var lum1_gauge := $MeanGauge3
onready var hum_gauge := $MeanGauge4
onready var i_gauge := $MeanGauge5
onready var lum2_gauge := $MeanGauge6
var devices
onready var G = get_node("/root/Global")

func _ready():
	pass # Replace with function body.-
	
func _on_Back_pressed():
	#Global.goto_scene("res://inicio.tscn")
	get_tree().change_scene_to(load('res://inicio.tscn'))

func _on_ProfileRequest_request_completed(result, response_code, headers, body):
	var __my_file := File.new()
	var __my_text := str("This is line one.")
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		__my_file.open("res://Test.txt", __my_file.WRITE)
		assert(__my_file.is_open())
		__my_file.store_string(body.get_string_from_utf8())
		__my_file.close()
		print(json.result.provisionDeviceKey)
		print(json.result.profileData.provisionConfiguration.provisionDeviceSecret)
		
func _on_CustomRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		devices=json
		$ItemList.clear()
		for n in len(json.result.data):
			$ItemList.add_item(json.result.data[n].name)
		$Button4.disabled=false

func _on_HTTPRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		print(json.result.id)
		customer_request.request("https://demo.thingsboard.io/api/customer/"+ json.result.id.id +"/devices?pageSize=50&page=0", headers, true, HTTPClient.METHOD_GET)
		loading.text="Solictando Customer Devices..."
		
func _on_LoginRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		print(json.result)
		G.token = "Bearer " + json.result["token"]
		var custumer=customer_input.text
		request_customer(G.token,custumer)
		loading.text="Solictando Customer Info..."
		
func _on_TelemetryRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		print(json.result)
		temp_gauge.value = float(json.result.TEMP[0].value)
		v_gauge.value = float(json.result.V[0].value)
		lum1_gauge.value = float(json.result.LUM1[0].value)
		hum_gauge.value = float(json.result.HUM[0].value)
		i_gauge.value = float(json.result.I[0].value)
		lum2_gauge.value = float(json.result.LUM2[0].value)
		if $Timer/CheckButton.pressed:
			$Timer.one_shot=true
			$Timer.start(15)
			
func _on_AttributesRequest_request_completed(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		loading.text=""
		var json = JSON.parse(body.get_string_from_utf8())
		print(json.result)
		
func request_customer(token,custumer):
	var headers = ["Content-Type: application/json", "X-Authorization: " + token]
	http_request.request("https://demo.thingsboard.io:443/api/tenant/customers?customerTitle="+custumer, headers, true, HTTPClient.METHOD_GET)
	loading.text="Solictando Customer ID..."
	
func _on_Button_pressed():
	var query = JSON.print({"username" : username_input.text, "password" : password_input.text})
	print(query)
	var header := ["Content-Type: application/json", "Accept: application/json"]
	login_request.request("https://demo.thingsboard.io/api/auth/login", header, true, HTTPClient.METHOD_POST, query)
	loading.text="Solictando Token..."
	
func _on_Button2_pressed():
	username_input.text="maldonado.accari.f@gmail.com"
	password_input.text="ContraseniaThings"
	customer_input.text="TESIS"

func _on_ItemList_item_selected(index):
	print($ItemList.get_item_text(index))
	print(devices.result.data[index].id.id)
	var CurrentTime= 1000*OS.get_unix_time();
	var startTs=CurrentTime-1000000
	var endTs=CurrentTime
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	telemetry_request.request("https://demo.thingsboard.io/api/plugins/telemetry/DEVICE/"+devices.result.data[index].id.id+"/values/timeseries", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solicitando última telemetría..."
	
func _on_Button4_pressed():
	var index=$ItemList.get_selected_items()[0]
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	telemetry_request.request("https://demo.thingsboard.io/api/plugins/telemetry/DEVICE/"+devices.result.data[index].id.id+"/values/timeseries", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solicitando última telemetría..."

func _on_Timer_timeout():
	var index=$ItemList.get_selected_items()[0]
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	telemetry_request.request("https://demo.thingsboard.io/api/plugins/telemetry/DEVICE/"+devices.result.data[index].id.id+"/values/timeseries", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solicitando última telemetría..."

func _on_CheckButton_pressed():
	if $Timer/CheckButton.pressed:
		$Timer.one_shot=true
		$Timer.start(1)
	else:
		$Timer.stop()

func _on_Timer2_timeout():
	$Timer/ProgressBar.value=$Timer.time_left

func _on_Button5_pressed():
	var index=$ItemList.get_selected_items()[0]
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	attributes_request.request("https://demo.thingsboard.io/api/plugins/telemetry/DEVICE/"+devices.result.data[index].id.id+"/values/attributes", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solicitando Configuracion..."

func _on_Button3_pressed():
	var headers = ["Content-Type: application/json", "X-Authorization: " + G.token]
	profile_request.request("https://demo.thingsboard.io/api/deviceProfile/04819920-bd8e-11eb-a311-cf80d7127bfd", headers, true, HTTPClient.METHOD_GET)
	loading.text="Solicitando última telemetría..."

func _on_Button6_pressed():
	var custumer=customer_input.text
	request_customer(G.token,custumer)
	loading.text="Solictando Customer Info..."
