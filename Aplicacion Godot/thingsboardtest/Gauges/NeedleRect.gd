tool
extends ColorRect



func _on_ColorRect_resized():
	rect_size = get_parent().rect_size
	rect_pivot_offset = rect_size / 2.0
