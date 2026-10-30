// The whole valley floor in one pass: grass, forest floor, fields and lakes blended softly
// from a low-resolution terrain map, and every road drawn from its tile data: lanes,
// parking, sidewalks with curbs, crosswalks, highway and country roads, dirt tracks.
shader_type canvas_item;

uniform sampler2D terrain_tex : filter_linear, repeat_disable;
uniform sampler2D road_tex : filter_nearest, repeat_disable;
uniform sampler2D info_tex : filter_nearest, repeat_disable;
// ground textures in one array: phones allow only a few texture units per shader
uniform sampler2DArray ground_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;

uniform float map_size = 240.0;
uniform float horizon = 142.0;
uniform vec2 land0 = vec2(80.0);
uniform float land_size = 80.0;
uniform float plot = 10.0;
uniform vec3 tint : source_color = vec3(1.0);
uniform vec3 haze : source_color = vec3(0.62, 0.74, 0.86);
uniform float snow = 0.0;
uniform float autumn = 0.0;
uniform float wet = 0.0;
uniform float overlay = 0.0;

varying vec2 wpos;

const vec3 PAINT = vec3(0.93, 0.93, 0.9);
const vec3 CURB = vec3(0.78, 0.76, 0.72);

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float sd_box(vec2 p, vec2 c, vec2 h) {
	vec2 d = abs(p - c) - h;
	return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float smin(float a, float b, float k) {
	float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
	return mix(b, a, h) - k * h * (1.0 - h);
}

// local frame of an arm: along runs from the tile centre (0.5) to the edge (1.0);
// cross < 0.5 is the lane of traffic coming in towards the centre
vec2 arm_frame(vec2 f, int k) {
	if (k == 0) return vec2(1.0 - f.y, f.x);        // north (-y)
	if (k == 1) return vec2(f.x, f.y);              // east (+x)
	if (k == 2) return vec2(f.y, 1.0 - f.x);        // south (+y)
	return vec2(1.0 - f.x, 1.0 - f.y);              // west (-x)
}

// Distance field of the carriageway (negative inside) for any arm layout.
// half = half width of the travelled way. Also returns coordinates for markings:
// m.x = along the road, m.y = across (0.5 = centre line), m.z = 1 straight, 2 curve.
float carriage(vec2 f, int arms, float half, out vec3 m) {
	int n = (arms & 1) + ((arms >> 1) & 1) + ((arms >> 2) & 1) + ((arms >> 3) & 1);
	m = vec3(0.0);
	if (arms == 10) { m = vec3(f.x, f.y, 1.0); return abs(f.y - 0.5) - half; }
	if (arms == 5) { m = vec3(f.y, 1.0 - f.x, 1.0); return abs(f.x - 0.5) - half; }
	if (n == 2) {
		// a bend: a ring around the inner corner
		vec2 p = vec2(((arms & 2) != 0) ? 1.0 : 0.0, ((arms & 4) != 0) ? 1.0 : 0.0);
		float r = length(f - p);
		// along = arc length on the centre line
		m = vec3(atan(abs(f.y - p.y), abs(f.x - p.x)) * 0.5, r, 2.0);
		return abs(r - 0.5) - half;
	}
	float d = (n == 1) ? length(f - 0.5) - (half + 0.12) : sd_box(f, vec2(0.5), vec2(half));
	if (n == 0) return d;
	for (int k = 0; k < 4; k++) {
		if ((arms & (1 << k)) == 0) continue;
		vec2 a = arm_frame(f, k);
		float da = sd_box(a, vec2(0.75, 0.5), vec2(0.27, half));
		d = smin(d, da, 0.1);
	}
	return d;
}

vec3 tex_g(float layer, vec2 g, float scale) {
	return texture(ground_tex, vec3(g * scale, layer)).rgb;
}

// ------------------------------------------------------------------ terrain
vec3 terrain(vec2 g, out float water_mask) {
	vec4 nz = texture(noise_tex, g / 24.0);
	vec4 nz2 = texture(noise_tex, g / 5.0 + 0.31);
	vec2 wob = (nz.rg - 0.5) * 1.6 + (nz2.rg - 0.5) * 0.5;
	vec4 w = texture(terrain_tex, (g + wob) / map_size);
	// grass, broken up with a second sample at another scale so it never tiles visibly
	vec3 gr = mix(tex_g(0.0, g, 0.5), tex_g(0.0, g + 0.37, 0.19), smoothstep(0.35, 0.65, nz.b));
	gr *= 0.9 + nz.r * 0.2;
	// big soft patches: deeper green hollows, paler sunny slopes
	float macro = texture(noise_tex, g / 60.0 + 0.5).r;
	gr = mix(gr, gr * vec3(0.82, 0.9, 0.95), smoothstep(0.55, 0.75, macro) * 0.6);
	gr = mix(gr, gr * vec3(1.08, 1.04, 0.82), smoothstep(0.45, 0.25, macro) * 0.6);
	gr = mix(gr, vec3(dot(gr, vec3(0.33))), 0.12);
	vec3 dry = gr * vec3(1.12, 1.0, 0.62) + vec3(0.06, 0.04, 0.0);
	gr = mix(gr, dry, w.a * 0.7);
	gr = mix(gr, gr * vec3(1.25, 0.95, 0.5) + vec3(0.08, 0.04, 0.0), autumn * 0.75);
	// forest floor
	vec3 fo = tex_g(1.0, g, 0.5);
	fo = mix(fo, fo * vec3(1.5, 0.9, 0.5), autumn * 0.6);
	float wf = smoothstep(0.42, 0.62, w.r + (nz2.b - 0.5) * 0.25);
	vec3 c = mix(gr, fo, wf);
	// fields: blocks with rows running one way or the other
	float wfi = smoothstep(0.45, 0.6, w.g + (nz2.a - 0.5) * 0.2);
	if (wfi > 0.0) {
		vec2 blk = floor(g / 7.0);
		float h = hash(blk);
		float rows_axis = step(0.5, fract(h * 7.3));
		float row = fract((rows_axis > 0.5 ? g.x : g.y) * 9.0);
		float prof = smoothstep(0.15, 0.45, row) * (1.0 - smoothstep(0.55, 0.85, row));
		vec3 soil = tex_g(2.0, g, 0.5);
		vec3 crop = h < 0.3 ? vec3(0.78, 0.66, 0.3) : h < 0.6 ? vec3(0.42, 0.6, 0.24) : h < 0.8 ? vec3(0.55, 0.62, 0.22) : soil * 1.12;
		crop *= 0.85 + nz2.b * 0.3;
		vec3 fc = mix(soil, crop, prof * 0.9);
		// thin tracks between the blocks
		vec2 bf = fract(g / 7.0);
		float track = 1.0 - smoothstep(0.0, 0.025, min(min(bf.x, 1.0 - bf.x), min(bf.y, 1.0 - bf.y)));
		fc = mix(fc, gr * 0.85, track);
		c = mix(c, fc, wfi);
	}
	// lakes with a sandy shore
	water_mask = smoothstep(0.5, 0.56, w.b);
	float shore = smoothstep(0.3, 0.45, w.b) * (1.0 - water_mask);
	c = mix(c, tex_g(3.0, g, 0.5) * vec3(1.15, 1.1, 0.95), shore);
	if (water_mask > 0.0) {
		float depth = smoothstep(0.55, 1.0, w.b);
		vec3 wc = mix(vec3(0.3, 0.55, 0.62), vec3(0.16, 0.36, 0.5), depth);
		float rip = texture(noise_tex, g / 3.0 + vec2(TIME * 0.02, TIME * 0.013)).b;
		float rip2 = texture(noise_tex, g / 2.0 - vec2(TIME * 0.017, -TIME * 0.01)).b;
		wc += smoothstep(0.62, 0.7, (rip + rip2) * 0.5) * 0.12;
		c = mix(c, wc, water_mask);
	}
	return c;
}

// ------------------------------------------------------------------ roads
// red brick paving in running bond, about 0.8 x 0.4 m
vec3 bricks(vec2 g) {
	vec2 b = g * vec2(20.0, 40.0);
	float row = floor(b.y);
	b.x += mod(row, 2.0) * 0.5;
	vec2 cell = floor(b);
	vec2 fr = fract(b);
	float h = hash(cell + vec2(row * 3.1, 7.0));
	vec3 c = mix(vec3(0.62, 0.3, 0.22), vec3(0.74, 0.42, 0.3), h);
	c = mix(c, vec3(0.55, 0.36, 0.3), step(0.86, hash(cell + 1.7)) * 0.6);
	float joint = 1.0 - smoothstep(0.0, 0.08, min(min(fr.x, 1.0 - fr.x) * 0.5, min(fr.y, 1.0 - fr.y)));
	return mix(c, vec3(0.7, 0.66, 0.6), joint * 0.7);
}

// returns colour + coverage. type: 1 dirt, 2 asphalt, 3 stone, 4 highway, 5 country, 6 town street, 7 boulevard,
// 8 avenue (wide, four lanes), 9 brick street, 10 street with bus lanes, 11 street with bike lanes
vec4 road(vec2 g, vec2 f, ivec4 d, vec3 ground) {
	int type = d.r;
	int arms = d.g & 15;
	bool park = (d.g & 16) != 0;
	bool cut0 = (d.g & 32) != 0;
	bool cut1 = (d.g & 64) != 0;
	int xw = d.b & 15;
	bool midx = (d.b & 32) != 0;
	vec4 nz = texture(noise_tex, g / 6.0);

	if (type == 1) {
		// dirt road: two worn wheel tracks per lane, soft grassy edges
		vec3 m;
		float dc = carriage(f, arms, 0.24, m);
		float edge = dc + (nz.g - 0.5) * 0.08 + (texture(noise_tex, g / 1.5).b - 0.5) * 0.05;
		float a = 1.0 - smoothstep(-0.06, 0.02, edge);
		vec3 c = tex_g(3.0, g, 0.5);
		if (m.z > 0.0) {
			float off = abs(m.y - 0.5);
			float ruts = max(1.0 - smoothstep(0.012, 0.03, abs(off - 0.06)), 1.0 - smoothstep(0.012, 0.03, abs(off - 0.17)));
			c *= 1.0 - ruts * 0.16;
			c = mix(c, ground * 0.9, (1.0 - smoothstep(0.0, 0.02, off)) * 0.3);
		}
		c = mix(c, ground, (1.0 - a) * 0.5);
		return vec4(c, a);
	}

	if (type == 4) {
		// highway along x: four lanes, central barrier, rails; a gap where the spur joins
		float cr = f.y - 0.5;
		float ac = abs(cr);
		vec3 c = tex_g(4.0, g, 0.5) * 0.96;
		float spur = ((arms & 1) != 0 && f.x > 0.25 && f.x < 0.75) ? 1.0 : 0.0;
		float spur_s = ((arms & 4) != 0 && f.x > 0.25 && f.x < 0.75) ? 1.0 : 0.0;
		bool open_n = cr < 0.0 && spur > 0.5;
		bool open_s = cr > 0.0 && spur_s > 0.5;
		bool open_side = open_n || open_s;
		if (ac > 0.47 && !open_side) {
			c = mix(ground, tex_g(3.0, g, 0.5) * 0.9, 0.7);
			float rail = 1.0 - smoothstep(0.004, 0.008, abs(ac - 0.485));
			c = mix(c, vec3(0.72, 0.74, 0.76), rail);
			c = mix(c, c * 0.6, (1.0 - smoothstep(0.0, 0.012, ac - 0.49)) * step(0.49, ac) * 0.6);
			return vec4(c, 1.0);
		}
		float tw = 1.0 - smoothstep(0.08, 0.2, abs(fract(f.y * 4.0) - 0.5));
		c *= 1.0 - tw * 0.05;
		bool gap = (spur > 0.5 || spur_s > 0.5) && f.x > 0.3 && f.x < 0.7;
		if (ac < 0.016 && !gap) {
			float side = smoothstep(-0.016, 0.016, cr);
			c = mix(vec3(0.82, 0.82, 0.8), vec3(0.6, 0.6, 0.6), side);
			return vec4(c, 1.0);
		}
		float edge_l = 1.0 - smoothstep(0.003, 0.006, abs(ac - 0.455));
		if (open_side) edge_l = 0.0;
		float dash = step(fract(f.x * 2.0), 0.45) * (1.0 - smoothstep(0.003, 0.006, abs(ac - 0.235)));
		float yel = (1.0 - smoothstep(0.003, 0.006, abs(ac - 0.026))) * (gap ? 0.0 : 1.0);
		c = mix(c, PAINT, max(edge_l, dash));
		c = mix(c, vec3(0.92, 0.75, 0.25), yel);
		return vec4(c, 1.0);
	}

	vec3 m;
	float half = type == 8 ? 0.3 : ((type == 10 || type == 11) ? 0.25 : 0.21);
	float dc = carriage(f, arms, half, m);
	vec3 asph = tex_g(4.0, g, 0.5);

	if (type == 5) {
		// country road: two lanes, edge lines, gravel shoulders, no sidewalks
		float sh = dc - 0.06 + (nz.b - 0.5) * 0.03;
		if (dc > 0.0) {
			if (sh > 0.0) return vec4(0.0);
			vec3 gv = mix(tex_g(3.0, g, 0.5) * vec3(1.05, 1.02, 0.95), ground, 0.3);
			return vec4(gv, 1.0 - smoothstep(-0.02, 0.0, sh));
		}
		vec3 c = asph;
		float edge_l = 1.0 - smoothstep(0.003, 0.006, abs(dc + 0.012));
		c = mix(c, PAINT, edge_l);
		if (m.z > 0.0 && (arms == 10 || arms == 5 || m.z > 1.5)) {
			float off = abs(m.y - 0.5);
			float cl = (1.0 - smoothstep(0.003, 0.006, off)) * step(fract(m.x * 3.0), 0.5);
			c = mix(c, PAINT, cl);
		}
		return vec4(c, 1.0);
	}

	// city streets (asphalt, cobblestone, town): carriageway + parking + sidewalks with curbs
	bool cobble = type == 3 || type == 9;
	float dpark = 1.0;
	if (park && (arms == 10 || arms == 5)) {
		float along = m.x;
		float ac = abs(m.y - 0.5);
		float s0 = cut0 ? 0.1 : -1.0;
		float s1 = cut1 ? 0.9 : 2.0;
		float rr = 0.05;
		float bx = sd_box(vec2(along, ac), vec2((s0 + s1) * 0.5, 0.0), vec2((s1 - s0) * 0.5 - rr, 0.35 - rr)) - rr;
		if (midx) {
			bx = max(bx, -(abs(along - 0.5) - 0.13));
		}
		dpark = bx;
	}
	float droad = min(dc, dpark);
	vec3 surf = type == 9 ? bricks(g) : (cobble ? tex_g(6.0, g, 3.0) : asph);
	if (type == 8) surf *= 0.9;
	vec3 pav = tex_g(5.0, g, 0.5);
	// sidewalk slabs, one metre
	vec2 sl = fract(g * 16.0);
	float joint = 1.0 - smoothstep(0.0, 0.06, min(min(sl.x, 1.0 - sl.x), min(sl.y, 1.0 - sl.y)));
	pav *= 1.0 - joint * 0.12;
	pav *= 0.95 + hash(floor(g * 16.0)) * 0.08;
	if (type == 6) pav = mix(pav, pav * vec3(0.95, 0.93, 0.9), 0.5);
	vec3 c;
	if (droad > 0.0) {
		c = pav;
		// curb stone right next to the street
		float curb = 1.0 - smoothstep(0.006, 0.012, droad);
		c = mix(c, CURB, curb);
	} else {
		c = surf;
		// gutter shadow under the curb
		c *= 1.0 - (1.0 - smoothstep(0.0, 0.016, -droad)) * 0.35;
		if (dc > 0.0) {
			// parking lane: stall marks every 5.3 m
			c *= 0.97;
			float st = fract(m.x * 3.0);
			float mark = (1.0 - smoothstep(0.008, 0.016, min(st, 1.0 - st))) * (cobble ? 0.0 : 1.0);
			c = mix(c, PAINT, mark * 0.85);
		} else if (type == 7 && m.z > 0.0 && (arms == 10 || arms == 5 || m.z > 1.5)) {
			// boulevard: a green median with low curbs and small round shrubs instead of the centre line
			float off = abs(m.y - 0.5);
			float tw = 1.0 - smoothstep(0.02, 0.05, abs(off - 0.125));
			c *= 1.0 - tw * 0.06;
			float lane = (1.0 - smoothstep(0.003, 0.006, abs(off - 0.2))) * step(fract(m.x * 3.0), 0.5);
			c = mix(c, PAINT, lane * 0.5);
			if (off < 0.05) {
				vec3 gm = tex_g(0.0, g, 0.5) * 1.05;
				float sp = fract(m.x * 2.0) - 0.5;
				float bush = 1.0 - smoothstep(0.025, 0.035, length(vec2(sp * 0.5, off)));
				gm = mix(gm, gm * vec3(0.6, 0.8, 0.55), bush);
				gm = mix(gm, CURB, 1.0 - smoothstep(0.004, 0.009, 0.05 - off));
				c = gm;
			}
		} else if (type == 11 && m.z > 0.0 && (arms == 10 || arms == 5 || m.z > 1.5)) {
			// bike lanes along both curbs: green surface behind a dashed white line, a bicycle mark every tile
			float off = abs(m.y - 0.5);
			if (off > 0.14) c = mix(c, vec3(0.3, 0.58, 0.36), 0.8);
			float dl = (1.0 - smoothstep(0.003, 0.007, abs(off - 0.14))) * step(fract(m.x * 6.0), 0.6);
			c = mix(c, PAINT, dl);
			float cl = (1.0 - smoothstep(0.003, 0.006, off)) * step(fract(m.x * 3.0), 0.55);
			c = mix(c, PAINT, cl);
			vec2 bk = vec2(fract(m.x) - 0.5, off - 0.195);
			float wheel = max(1.0 - smoothstep(0.003, 0.006, abs(length(bk - vec2(-0.025, 0.0)) - 0.016)),
				1.0 - smoothstep(0.003, 0.006, abs(length(bk - vec2(0.025, 0.0)) - 0.016)));
			float bar = (1.0 - smoothstep(0.002, 0.005, abs(bk.y + 0.004))) * step(abs(bk.x), 0.025);
			c = mix(c, PAINT, max(wheel, bar) * 0.85);
		} else if ((type == 8 || type == 10) && m.z > 0.0 && (arms == 10 || arms == 5 || m.z > 1.5)) {
			float off = abs(m.y - 0.5);
			if (type == 8) {
				// avenue: double yellow centre line, dashed lines between the two lanes each way
				float tw = 1.0 - smoothstep(0.02, 0.05, abs(off - 0.08)) + 1.0 - smoothstep(0.02, 0.05, abs(off - 0.22));
				c *= 1.0 - tw * 0.05;
				float yel = 1.0 - smoothstep(0.003, 0.006, abs(off - 0.012));
				c = mix(c, vec3(0.92, 0.75, 0.25), yel);
				float dash = (1.0 - smoothstep(0.003, 0.006, abs(off - 0.15))) * step(fract(m.x * 3.0), 0.5);
				c = mix(c, PAINT, dash * 0.9);
			} else {
				// bus lanes along both curbs: red surface behind a solid white line, a dashed centre line
				if (off > 0.13) c = mix(c, vec3(0.62, 0.24, 0.2), 0.75);
				float sol = 1.0 - smoothstep(0.003, 0.007, abs(off - 0.13));
				c = mix(c, PAINT, sol);
				float cl = (1.0 - smoothstep(0.003, 0.006, off)) * step(fract(m.x * 3.0), 0.55);
				c = mix(c, PAINT, cl);
				// a pale diamond on the bus lane every tile
				vec2 dm = vec2(fract(m.x) - 0.5, off - 0.19);
				float dia = 1.0 - smoothstep(0.0, 0.006, abs(abs(dm.x) * 0.35 + abs(dm.y)) - 0.03);
				c = mix(c, PAINT, dia * 0.7);
			}
		} else if (!cobble) {
			// wear in the wheel tracks, centre line
			if (m.z > 0.0 && (arms == 10 || arms == 5 || m.z > 1.5)) {
				float off = abs(m.y - 0.5);
				float tw = 1.0 - smoothstep(0.02, 0.05, abs(off - 0.105));
				c *= 1.0 - tw * 0.06;
				float cl = (1.0 - smoothstep(0.003, 0.006, off)) * step(fract(m.x * 3.0), 0.55);
				c = mix(c, PAINT, cl);
			}
		}
		// crosswalks and stop lines
		for (int k = 0; k < 4; k++) {
			if ((xw & (1 << k)) == 0) continue;
			vec2 a = arm_frame(f, k);
			if (a.x > 0.73 && a.x < 0.88 && abs(a.y - 0.5) < half) {
				float z = step(fract(a.y * 16.0), 0.5);
				c = mix(c, PAINT, z * 0.92);
			}
			if (!cobble && a.x > 0.905 && a.x < 0.925 && a.y > 0.5 - half && a.y < 0.5) {
				c = mix(c, PAINT, 0.9);
			}
		}
		if (midx) {
			float al = m.x;
			if (abs(al - 0.5) < 0.075 && abs(m.y - 0.5) < half) {
				float z = step(fract(m.y * 16.0), 0.5);
				c = mix(c, PAINT, z * 0.92);
			}
		}
	}
	return vec4(c, 1.0);
}

// ------------------------------------------------------------------ water dug by the player
// The road texture's alpha carries it: 129 river, 130 sea, 131 ocean (255 = road without water).
int water_at(ivec2 p) {
	int a = int(texelFetch(road_tex, p, 0).a * 255.0 + 0.5);
	return (a > 128 && a < 140) ? a - 128 : 0;
}

// Distance to the nearest dry tile around: the shore follows it, so neighbouring water tiles merge
// into one shape and the banks come out rounded.
vec3 player_water(vec2 g, ivec2 t, int kind, vec3 ground, out float field) {
	float dmin = 10.0;
	for (int dy = -1; dy <= 1; dy++) {
		for (int dx = -1; dx <= 1; dx++) {
			ivec2 n = t + ivec2(dx, dy);
			if ((dx != 0 || dy != 0) && water_at(n) == 0) {
				vec2 q = max(abs(g - (vec2(n) + 0.5)) - 0.5, vec2(0.0));
				dmin = min(dmin, length(q));
			}
		}
	}
	field = dmin;
	vec4 nz = texture(noise_tex, g / 2.5);
	float fw = dmin + (nz.r - 0.5) * 0.1 + (texture(noise_tex, g / 7.0 + 0.4).g - 0.5) * 0.14;
	vec3 sand = tex_g(3.0, g, 0.5) * vec3(1.15, 1.1, 0.95);
	vec3 c = mix(ground, sand, smoothstep(0.0, 0.05, fw));
	float wm = smoothstep(0.13, 0.17, fw);
	if (wm > 0.0) {
		float deep = smoothstep(0.2, 0.9, dmin);
		vec3 shallow = kind == 1 ? vec3(0.34, 0.6, 0.62) : kind == 2 ? vec3(0.22, 0.52, 0.66) : vec3(0.16, 0.42, 0.62);
		vec3 deepc = kind == 1 ? vec3(0.2, 0.44, 0.52) : kind == 2 ? vec3(0.1, 0.3, 0.5) : vec3(0.04, 0.16, 0.36);
		vec3 wc = mix(shallow, deepc, deep);
		float sp = kind == 1 ? 0.06 : 0.025;
		float rip = texture(noise_tex, g / 3.0 + vec2(TIME * sp, TIME * sp * 0.6)).b;
		float rip2 = texture(noise_tex, g / 2.0 - vec2(TIME * sp * 0.8, -TIME * sp * 0.5)).b;
		wc += smoothstep(0.62, 0.7, (rip + rip2) * 0.5) * (kind == 3 ? 0.16 : 0.12);
		if (kind >= 2) {
			// surf: foam lines running along the shore
			float band = smoothstep(0.15, 0.18, fw) * (1.0 - smoothstep(0.22, 0.4, fw));
			float wave = step(0.55, fract(fw * 12.0 - TIME * 0.35 + nz.g * 0.6));
			wc = mix(wc, vec3(0.92, 0.96, 0.98), band * wave * (kind == 3 ? 0.85 : 0.5));
		}
		c = mix(c, wc, wm);
	}
	return c;
}

void fragment() {
	vec2 g = vec2((wpos.x / 160.0 + wpos.y / 80.0) * 0.5, (wpos.y / 80.0 - wpos.x / 160.0) * 0.5);
	float sum = g.x + g.y;
	if (sum < horizon - 0.5) {
		discard;
	}
	float wm;
	vec3 c = terrain(g, wm);
	vec3 ground = c;
	ivec2 t = ivec2(floor(g));
	vec2 f = g - floor(g);
	bool on_map = t.x >= 0 && t.y >= 0 && t.x < int(map_size) && t.y < int(map_size);
	if (on_map) {
		ivec4 d = ivec4(texelFetch(road_tex, t, 0) * 255.0 + 0.5);
		int wk = (d.a > 128 && d.a < 140) ? d.a - 128 : 0;
		float wfield = 0.0;
		if (wk > 0) {
			c = player_water(g, t, wk, ground, wfield);
		}
		if (d.r > 0) {
			vec4 r = road(g, f, d, ground);
			if (wk > 0) {
				// a bridge: the deck with railings, water and its shadow on both sides
				vec3 mb;
				float db = carriage(f, d.g & 15, 0.33, mb);
				float deck = 1.0 - smoothstep(-0.004, 0.004, db);
				c = mix(c, c * 0.55, (1.0 - deck) * (1.0 - smoothstep(0.0, 0.08, db)) * 0.7);
				r.a *= deck;
				c = mix(c, r.rgb, r.a);
				float rail = (1.0 - smoothstep(0.004, 0.01, abs(db + 0.012))) * step(0.5, fract((f.x + f.y) * 14.0) + 0.4);
				c = mix(c, vec3(0.86, 0.86, 0.9), rail * 0.9);
			} else {
				c = mix(c, r.rgb, r.a);
			}
		}
	}
	// seasons and weather
	float green = c.g - max(c.r, c.b);
	if (snow > 0.0) {
		float lum = dot(c, vec3(0.3, 0.59, 0.11));
		float cover = snow * (0.75 + 0.25 * smoothstep(0.0, 0.08, green));
		c = mix(c, vec3(0.88, 0.91, 0.97) * (0.92 + lum * 0.15), cover * 0.9);
	}
	if (wet > 0.0) {
		float sheen = texture(noise_tex, g / 4.0).g;
		c = mix(c, c * vec3(0.78, 0.82, 0.9) + sheen * 0.05, wet);
	}
	// building mode: zones, owned land, plot borders
	if (overlay > 0.0 && on_map) {
		ivec4 info = ivec4(texelFetch(info_tex, t, 0) * 255.0 + 0.5);
		if (info.r > 0) {
			vec3 zc = info.r == 1 ? vec3(0.45, 0.7, 1.0) : info.r == 2 ? vec3(1.0, 0.85, 0.3) : info.r == 3 ? vec3(0.75, 0.6, 0.5) : vec3(0.5, 1.0, 0.5);
			float own = float(info.g > 0);
			c = mix(c, c * zc * 1.15, 0.35 * overlay * own);
			c = mix(c, c * 0.55, (1.0 - own) * 0.5 * overlay);
			vec2 pl = (g - land0) / plot;
			vec2 pf = fract(pl);
			float pd = min(min(pf.x, 1.0 - pf.x), min(pf.y, 1.0 - pf.y)) * plot;
			float line = 1.0 - smoothstep(0.03, 0.07, pd);
			c = mix(c, vec3(1.0), line * 0.6 * overlay);
		}
	}
	// distance haze towards the horizon
	float hz = 1.0 - smoothstep(horizon, horizon + 10.0, sum);
	c = mix(c * tint, haze, hz * hz * 0.6);
	float a = smoothstep(horizon - 0.5, horizon + 0.8, sum);
	COLOR = vec4(c, a);
}
