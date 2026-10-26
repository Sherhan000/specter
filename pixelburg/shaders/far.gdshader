// Backdrop strips beyond the horizon: the farther the layer, the more it melts into the haze
// of the hour; the lower parts sink into valley mist.
shader_type canvas_item;

uniform vec3 tint : source_color = vec3(1.0);
uniform vec3 haze : source_color = vec3(0.7, 0.8, 0.9);
uniform float amount = 0.3;
uniform float mist = 0.3;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float m = clamp((UV.y - 0.4) / 0.6, 0.0, 1.0);
	float h = clamp(amount + mist * m * m, 0.0, 1.0);
	COLOR = vec4(mix(c.rgb * tint, haze, h), c.a);
}
