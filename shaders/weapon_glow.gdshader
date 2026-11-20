shader_type canvas_item;
// Solid pulsing halo drawn behind a weapon: gold for legendary, magenta for rare.
uniform vec4 glow_color : source_color = vec4(1.0, 0.82, 0.25, 1.0);
uniform float strength = 0.0;

void fragment() {
	float a = texture(TEXTURE, UV).a;
	float pulse = 0.6 + 0.4 * sin(TIME * 3.0);
	COLOR = vec4(glow_color.rgb, a * strength * pulse * COLOR.a);
}
