tool
extends ColorRect

onready var gauge_rect := get_parent()

func _process(delta):
	material.set_shader_param("starting_angle", get_parent().material.get_shader_param("starting_angle"))
	material.set_shader_param("ending_angle", get_parent().material.get_shader_param("ending_angle"))
	material.set_shader_param("value", get_parent().material.get_shader_param("value"))
