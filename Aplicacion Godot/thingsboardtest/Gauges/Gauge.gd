tool
class_name MeanGauge
extends Control

export (float) var value : float setget set_value
export (float) var min_value := 0.0 setget set_min_value
export (float) var max_value := 1.0 setget set_max_value
export (float) var start_angle := 45.0 setget set_start_angle 
export (float) var end_angle := 315.0 setget set_end_angle 
export (Color) var foreground_color := Color.red setget set_f_color
export (Color) var background_color := Color.black setget set_b_color
export (Color) var needle_color := Color("#667fff") setget set_n_color
export (Color) var foreground_tick_color := Color.white setget set_foreground_tick_color
export (Color) var background_tick_color := Color.white setget set_background_tick_color
export (String) var unit := "" setget set_unit
export (String) var variable_name := "" setget set_var_name
export (float) var smooth := 1.0
export (int) var prim_ticks_amount := 5 setget set_prim_ticks_amount
export (int) var sec_ticks_amount := 25 setget set_sec_ticks_amount
export (float) var prim_ticks_width := 0.01 setget set_prim_ticks_width
export (float) var sec_ticks_width := 0.03 setget set_sec_ticks_width
export (int) var decimal_digits := 2 setget set_decimal_digits

var data := {}

onready var gauge_font := theme.default_font
onready var color_rect := $HBoxContainer/ColorRect
onready var label := $HBoxContainer/ColorRect/Label
onready var unit_label := $HBoxContainer/ColorRect/Label/Unit
onready var rect_material = color_rect.material
onready var tick_material = $HBoxContainer/ColorRect/GaugeTicks.material
onready var gauge_tick = $HBoxContainer/ColorRect/GaugeTicks
onready var needle := $HBoxContainer/ColorRect/NeedleRect
onready var name_label := $HBoxContainer/Name
onready var tween := $Tween

func _ready():
	set_min_value(min_value)
	set_max_value(max_value)
	set_f_color(foreground_color)
	set_b_color(background_color)
	set_unit(unit)
	set_var_name(variable_name)
	set_value(value)
	set_n_color(needle_color)
	set_decimal_digits(decimal_digits)
	set_prim_ticks_amount(prim_ticks_amount)
	set_sec_ticks_amount(sec_ticks_amount)
	_on_ColorRect_resized()
	
func set_settings(data : Dictionary):
	for key in data:
		if key == "foreground_color":
			self.foreground_color = Color(data[key])
		else:
			set(key, data[key])
		
func get_settings() -> Dictionary:
	var data := {
		"min_value" : min_value,
		"max_value" : max_value,
		"foreground_color" : foreground_color.to_html(),
		"variable_name" : variable_name,
		"unit" : unit
	}
	return data
	
func set_unit(u : String):
	unit = u
	if is_instance_valid(unit_label):
		unit_label.text = u
		
func set_var_name(n : String):
	variable_name = n
	if is_instance_valid(name_label):
		name_label.text = n

func set_n_color(c : Color):
	needle_color = c
	if is_instance_valid(needle):
		needle.material.set_shader_param("color", c)

func set_f_color(c : Color):
	foreground_color = c
	if is_instance_valid(rect_material):
		rect_material.set_shader_param("foreground_color", c)
		
func set_b_color(c : Color):
	background_color = c
	if is_instance_valid(rect_material):
		rect_material.set_shader_param("background_color", c)
		
func set_min_value(v : float):
	min_value = v
	if is_instance_valid(color_rect):
		color_rect.set_labels(prim_ticks_amount)

func set_max_value(v : float):
	max_value = v
	if is_instance_valid(color_rect):
		color_rect.set_labels(prim_ticks_amount)


func set_value(v):
	var prev_value := value
	if v is String:
		value = float(v)
	else:
		value = v
	value = clamp(value, min_value, max_value)
	if is_instance_valid(rect_material):
		var format := "%."+str(decimal_digits)+"f"
		if v is String and not v.is_valid_float():
			label.text = v
		else:
			label.text = format % stepify(value, 1.0/pow(10, decimal_digits))
		
		tween.stop_all()
		tween.interpolate_method(self, "_update_value", prev_value, value, smooth)
		tween.start()
		
func _update_value(v : float):
	var normalized_value = (v - min_value)/(max_value - min_value)
	rect_material.set_shader_param("value", normalized_value)
	var angle = start_angle * (1.0-normalized_value) + end_angle * normalized_value
	needle.rect_rotation = angle

func set_start_angle(a:float):
	start_angle = a
	if is_instance_valid(rect_material):
		rect_material.set_shader_param("starting_angle", a)
	
func set_end_angle(a:float):
	end_angle = a
	if is_instance_valid(rect_material):
		rect_material.set_shader_param("ending_angle", a)

func set_prim_ticks_amount(t : int):
	prim_ticks_amount = t
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("prim_ticks_amount", t)
		color_rect.set_labels(t)
		color_rect.tick_amount = t
		
func set_sec_ticks_amount(t : int):
	sec_ticks_amount = t
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("sec_ticks_amount", t)

func set_prim_ticks_width(w : float):
	prim_ticks_width = w
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("tick_width", w)
		
func set_sec_ticks_width(w : float):
	sec_ticks_width = w
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("sec_tick_width", w)
		
func set_foreground_tick_color(c : Color):
	foreground_tick_color = c
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("tick_fg_color", c)
		
func set_background_tick_color(c : Color):
	background_tick_color = c
	if is_instance_valid(tick_material):
		tick_material.set_shader_param("tick_bg_color", c)

func set_decimal_digits(d:int):
	decimal_digits = d
	if is_instance_valid(color_rect):
		set_value(value)
		color_rect.set_labels(prim_ticks_amount)


func _on_ColorRect_resized():
	if is_instance_valid(color_rect):
		var dim = color_rect.rect_size.x
		var font_size = 8 * (256-dim)/128 + 14 * (dim - 128)/128
		gauge_font.size = int(font_size)
