extends Node2D
## Ending credits: the six Hearths relit, then a scroll of thanks. Press Z to finish when it ends.

signal finished

var t := 0.0
var lines := [
	"The fire in Cinderreach burns orange again.", "In Maretide, the tide goes out, and comes back, the way tides should.",
	"The winds of Skyreach are loud and free.", "In Gravenhold, the rock is just rock.",
	"In Luminael, people are finished for today.", "And in the Hollow, everyone is here.", "",
	"King Goblin's hoard is scattered back to the six worlds.", "And the Kindler has a new name.", "",
	"GOBLIN SLAYER", "", "", "Thank you for playing.", "", "The Witness and the Unmaker still wait,",
	"for those who can't leave well enough alone.", "", "Press Z to continue your journey."]
const ELS := ["fire", "water", "wind", "stone", "spirit", "void"]


func _ready() -> void:
	# the true ending: King Goblin AND both omnipotents defeated
	if GS.flag("beat_aeon") and GS.flag("beat_nihil"):
		var at := lines.find("GOBLIN SLAYER")
		lines.insert(at, "")
		lines.insert(at, "The Witness and the Unmaker kneel beside you. No one is left to fear.")
		lines.insert(at, "TRUE ENDING")
		var w := lines.find("The Witness and the Unmaker still wait,")
		if w >= 0:
			lines[w] = "Every Hearth, every shadow, every crown: set right."
			lines[w + 1] = "A legend, finished."
	lines.append("")
	lines.append("New Game+ unlocked: start again from the title screen with your whole party." if GS.ng == 0 else
		"New Game+ %d unlocked: the goblins grow bolder every time." % (GS.ng + 1))
	Audio.music("ending", 1.5)


func _process(delta: float) -> void:
	t += delta
	queue_redraw()
	if t > 6.0 + lines.size() * 1.4 and Inp.ok():
		finished.emit()
		set_process(false)


func _draw() -> void:
	draw_rect(Rect2(0, 0, 480, 270), Color(0.03, 0.02, 0.07))
	for i in 6:
		var p := Vector2(60 + i * 72, 40)
		var lit := clampf((t - i * 0.6) / 0.8, 0.0, 1.0)
		var col := DB.el_color(ELS[i])
		var pulse := 0.7 + 0.3 * sin(t * 1.2 + i)
		draw_circle(p, 14 * lit * pulse, Color(col.r, col.g, col.b, 0.25))
		draw_circle(p, 7 * lit, Color(col.r, col.g, col.b, 0.9))
	var y0 := 280.0 - (t - 4.0) * 22.0
	for i in lines.size():
		var y := y0 + i * 18
		if y < 70 or y > 270:
			continue
		var l: String = lines[i]
		if l == "GOBLIN SLAYER":
			Art.text_center(self, Vector2(240, y), l, Color(1, 0.9, 0.6), 16, Art.font_title, false)
		else:
			Art.text_center(self, Vector2(240, y), l)
	if t > 6.0 + lines.size() * 1.4:
		Art.text_center(self, Vector2(240, 150), "Press Z to continue your journey.", Art.YELLOW)
