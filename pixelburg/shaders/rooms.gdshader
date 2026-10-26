// Window light of homes at night. The texture holds four groups of rooms (one per channel);
// the sprite's modulate says which groups are lit, `night` fades everything with the daylight.
shader_type canvas_item;
render_mode blend_add;

uniform float night = 0.0;
uniform vec3 warm : source_color = vec3(1.0, 0.8, 0.5);

void fragment() {
	vec4 g = texture(TEXTURE, UV);
	float l = clamp(dot(g, COLOR), 0.0, 1.0);
	COLOR = vec4(warm * l * night, 1.0);
}
