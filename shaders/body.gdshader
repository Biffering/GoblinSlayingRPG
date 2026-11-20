shader_type canvas_item;
// Character body: white hit-flash, golden shimmer while a boost elixir is active, and fading.
uniform float flash = 0.0;
uniform float glow = 0.0;
uniform vec4 glow_color : source_color = vec4(1.0, 0.85, 0.4, 1.0);
uniform float fade = 1.0;
uniform float tint_amount = 0.0;
uniform vec4 tint : source_color = vec4(1.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	// a bright band of gold that sweeps up the body
	float sweep = fract(UV.y * 3.0 - TIME * 0.9);
	float g = glow * (0.12 + 0.1 * sin(TIME * 3.2) + 0.25 * smoothstep(0.85, 1.0, sweep));
	c.rgb = c.rgb + glow_color.rgb * g;
	c.rgb = mix(c.rgb, tint.rgb, tint_amount);
	c.rgb = mix(c.rgb, vec3(1.0), flash);
	c.a *= fade;
	COLOR = c;
}
