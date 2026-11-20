shader_type canvas_item;
// Colors the precomputed aura ring (red channel = distance from the sprite) with up to three
// element colors that flow upward in bands, with a slow pulse and a pixel-style flicker.
// Vivid, mostly opaque near the body so the element colors read on any ground.
uniform vec4 col0 : source_color = vec4(1.0);
uniform vec4 col1 : source_color = vec4(1.0);
uniform vec4 col2 : source_color = vec4(1.0);
uniform int ncol = 1;
uniform float strength = 0.0;
uniform float radius = 1.0;
uniform float maxr = 4.0;
uniform float seed = 0.0;

void fragment() {
	vec4 t = texture(TEXTURE, UV);
	if (t.a < 0.5 || strength <= 0.001) {
		discard;
	}
	float d = max(1.0, floor(t.r * maxr + 0.5));
	if (d > radius + 0.01) {
		discard;
	}
	float pulse = 0.62 + 0.38 * sin(TIME * 1.25 + seed);          // slow breathing pulse
	float fall = 1.0 - (d - 1.0) / (radius + 1.0);
	vec2 cell = floor(UV / TEXTURE_PIXEL_SIZE);  // sprite pixels, independent of screen scale
	float n = fract(sin(dot(cell + vec2(floor(TIME * 5.0), seed), vec2(12.9898, 78.233))) * 43758.5453);
	// outer pixels flicker on and off like heat shimmer
	if (d > 1.0 && n < 0.18 * (d - 1.0)) {
		discard;
	}
	float a = strength * (0.35 + 0.65 * fall) * (0.55 + 0.45 * pulse) * (0.85 + 0.15 * n) * 1.25;
	a = floor(a * 6.0 + 0.5) / 6.0;
	int idx = 0;
	if (ncol > 1) {
		float band = floor((cell.y + cell.x * 0.5) / 3.0 + TIME * 2.2 + seed);
		idx = int(mod(band, float(ncol)));
	}
	vec4 c = col0;
	if (idx == 1) { c = col1; }
	if (idx == 2) { c = col2; }
	vec3 lit = mix(c.rgb, vec3(1.0), 0.25 * fall * pulse);  // hot core near the body
	COLOR = vec4(lit, clamp(a, 0.0, 0.95));
}
