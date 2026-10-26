// Light that only shows at night (lamp heads, glow, light pools): one uniform for all of them.
shader_type canvas_item;
render_mode blend_add;

uniform float night = 0.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	COLOR = vec4(c.rgb, c.a * night);
}
