// Cast shadows of buildings: fade at night and under clouds.
shader_type canvas_item;

uniform float strength = 1.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	COLOR = vec4(c.rgb, c.a * strength * COLOR.a);
}
