// Sky above the horizon: a gradient from the horizon colour to the zenith, stars at night.
shader_type canvas_item;

uniform vec3 zenith : source_color = vec3(0.36, 0.58, 0.84);
uniform vec3 horizon_col : source_color = vec3(0.78, 0.87, 0.94);
uniform float horizon_y = 11360.0;
uniform float height = 3000.0;
uniform float stars = 0.0;

varying vec2 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
}

void fragment() {
	float t = clamp((horizon_y - wpos.y) / height, 0.0, 1.0);
	vec3 c = mix(horizon_col, zenith, pow(t, 0.7));
	if (stars > 0.0) {
		vec2 cell = floor(wpos / 9.0);
		float h = hash(cell);
		float tw = 0.6 + 0.4 * sin(TIME * 2.0 + h * 40.0);
		c += vec3(step(0.996, h) * tw * stars * smoothstep(0.1, 0.5, t));
	}
	COLOR = vec4(c, 1.0);
}
