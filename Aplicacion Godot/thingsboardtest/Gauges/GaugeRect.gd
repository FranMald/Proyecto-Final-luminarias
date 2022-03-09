tool
extends ColorRect

onready var needle := $NeedleRect

var tick_amount := 0

func _ready():
	_on_ColorRect_resized()

func _on_ColorRect_resized():
	var min_dim := min(rect_size.x, rect_size.y)
	rect_size.y = min_dim
	rect_size.x = min_dim
	var y := 0.0
	rect_position = get_parent().rect_size/2 - rect_size/2
	if is_instance_valid(needle):
		var needle_length : float = needle.rect_size.y / 2.0
		
		var y1 := Vector2(0, needle_length).rotated(deg2rad(get_parent().get_parent().start_angle)).y

		var y2 := Vector2(0, needle_length).rotated(deg2rad(get_parent().get_parent().end_angle)).y
		
		y = max(y1, y2)
	
	set_labels(tick_amount)
#		get_parent().get_parent().rect_size = Vector2(rect_size.x, rect_size.y / 2.0 + y + rect_position.y)

func set_labels(amount : int):
	var radius : float = $GaugeTicks.material.get_shader_param("inner_radius")
	for label in $Labels.get_children():
		$Labels.remove_child(label)
	if amount == 0:
		return
	tick_amount = amount
	var max_value : float = get_parent().get_parent().max_value
	var min_value : float = get_parent().get_parent().min_value
	var start : float = get_parent().get_parent().start_angle
	var end : float = get_parent().get_parent().end_angle
	var delta_angle : float = (end - start) / (amount);
	var delta : float = (max_value - min_value) / (amount);
	
	
	
	for i in amount+1:
		var label := DynamicLabel.new()
		label.align = Label.ALIGN_CENTER
		label.valign = Label.VALIGN_CENTER
		$Labels.add_child(label)
		var value : float = i * delta + min_value
		var angle : float = i * delta_angle + start
		var position := rect_size.y*radius*Vector2(0, 1).rotated(deg2rad(angle))
		if position.x > 0:
			label.grow_horizontal = Control.GROW_DIRECTION_BEGIN
		elif position.x < 0:
			label.grow_horizontal = Control.GROW_DIRECTION_END
		else:
			label.grow_horizontal = Control.GROW_DIRECTION_BOTH
		
		if position.y < -0.5*radius*rect_size.y:
			label.grow_horizontal = Control.GROW_DIRECTION_BOTH
			
		label.text = str(stepify(value, 1.0/pow(10, get_parent().get_parent().decimal_digits)))

		label.rect_position = position


func _on_HBoxContainer_resized():
	var min_dim := min(get_parent().rect_size.x, get_parent().rect_size.y)
	rect_size.y = min_dim
	rect_size.x = min_dim
	rect_position = get_parent().rect_size/2 - rect_size/2
	var y := 0.0
	
	if is_instance_valid(needle):
		var needle_length : float = needle.rect_size.y / 2.0
		
		var y1 := Vector2(0, needle_length).rotated(deg2rad(get_parent().get_parent().start_angle)).y

		var y2 := Vector2(0, needle_length).rotated(deg2rad(get_parent().get_parent().end_angle)).y
		
		y = max(y1, y2)
	
	rect_position.y += y/4.0
	set_labels(tick_amount)
