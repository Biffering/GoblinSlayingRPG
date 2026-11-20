shader_type canvas_item;
// Darkness over the map, with soft holes where lights shine, and a vignette for depth.
uniform vec4 ambient = vec4(0.0, 0.0, 0.03, 0.0);   // rgb: shade color, a: how dark
uniform float vignette = 0.35;
uniform int count = 0;
uniform vec4 lights[48];     // x, y, radius (screen px), strength
uniform vec2 screen = vec2(480.0, 270.0);

void fragment() {
	vec2 p = UV * screen;
	float lit = 0.0;
	for (int i = 0; i < count; i++) {
		float d = distance(p, lights[i].xy) / max(1.0, lights[i].z);
		float f = clamp(1.0 - d, 0.0, 1.0);
		lit += f * f * (3.0 - 2.0 * f) * lights[i].w;
	}
	lit = clamp(lit, 0.0, 1.0);
	vec2 c = UV - 0.5;
	float vig = smoothstep(0.32, 0.78, length(c * vec2(1.0, 0.82))) * vignette;
	float dark = clamp(ambient.a * (1.0 - lit) + vig * (1.0 - lit * 0.6), 0.0, 0.96);
	// a faint dither keeps the gradient from banding at low resolution
	float n = fract(sin(dot(floor(p), vec2(12.9898, 78.233))) * 43758.5453);
	dark = clamp(dark + (n - 0.5) * 0.018, 0.0, 0.97);
	COLOR = vec4(ambient.rgb, dark);
}
