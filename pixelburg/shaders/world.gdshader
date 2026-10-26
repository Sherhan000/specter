// Shared world shader: time-of-day tint, seasons (autumn leaves, snow cover), wet look,
// distance haze near the horizon, plus a gentle sway for trees.
shader_type canvas_item;

uniform vec3 tint : source_color = vec3(1.0);
uniform float sway = 0.0;
uniform float snow = 0.0;
uniform float autumn = 0.0;
uniform float wet = 0.0;
uniform vec3 haze : source_color = vec3(0.7, 0.8, 0.9);
uniform float horizon_y = 11360.0;

varying float hz;

void vertex() {
	// things far up the valley fade into the same haze as the ground under them
	float k = 1.0 - smoothstep(horizon_y, horizon_y + 800.0, MODEL_MATRIX[3].y);
	hz = k * k * 0.6;
	if (sway > 0.0 && UV.y < 0.5) {
		float phase = MODEL_MATRIX[3].x * 0.031 + MODEL_MATRIX[3].y * 0.023;
		VERTEX.x += sin(TIME * 1.5 + phase) * sway;
	}
}

void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	float green = c.g - max(c.r, c.b);
	float leafy = smoothstep(0.02, 0.12, green);
	if (autumn > 0.0) {
		float k = fract(sin(dot(floor(FRAGCOORD.xy / 6.0), vec2(12.9898, 78.233))) * 43758.5453);
		vec3 warm = mix(vec3(c.g * 1.25, c.g * 0.72, c.b * 0.35), vec3(c.g * 1.2, c.g * 0.95, c.b * 0.3), k);
		c.rgb = mix(c.rgb, warm, autumn * leafy);
	}
	if (snow > 0.0) {
		float lum = dot(c.rgb, vec3(0.3, 0.59, 0.11));
		vec3 white = vec3(0.86, 0.9, 0.97) + lum * 0.12;
		c.rgb = mix(c.rgb, white, snow * leafy * 0.92);
	}
	if (wet > 0.0) {
		c.rgb = mix(c.rgb, c.rgb * vec3(0.86, 0.9, 1.0), wet);
	}
	COLOR = vec4(mix(c.rgb * tint, haze, hz), c.a);
}
