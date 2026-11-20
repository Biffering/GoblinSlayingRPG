extends Node
func _ready() -> void:
	_run.call_deferred()
func wait(s: float) -> void:
	await get_tree().create_timer(s).timeout
func shot(n: String) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("/tmp/shx/%s.png" % n)
func _run() -> void:
	await wait(0.3)
	Main.inst.goto_title()
	await wait(2.5)
	await shot("title")
	print("T29 DONE")
	get_tree().quit()
