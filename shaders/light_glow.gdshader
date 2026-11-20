shader_type canvas_item;
render_mode blend_add;
// The warm (or cold) color each light throws on its surroundings.
uniform int count = 0;
uniform vec4 lights[48];     // x, y, radius, strength
uniform vec4 colors[48];     // rgb, glow amount
uniform vec2 screen = vec2(480.0, 270.0);

void fragment() {
	vec2 p = UV * screen;
	vec3 acc = vec3(0.0);
	for (int i = 0; i < count; i++) {
		float d = distance(p, lights[i].xy) / max(1.0, lights[i].z);
		float f = clamp(1.0 - d, 0.0, 1.0);
		acc += colors[i].rgb * f * f * f * colors[i].a * lights[i].w;
	}
	COLOR = vec4(acc, 1.0);
}
