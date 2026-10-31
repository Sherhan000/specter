class_name QR
extends RefCounted
## A small QR code encoder (byte mode, error correction level L, versions 1–40, ISO/IEC 18004).
## Based on the reference algorithm (Project Nayuki's QR Code generator). QR.image("text") -> Image.

const ECC_L := 1   ## format bits of level L
## error-correction codewords per block and number of blocks for level L, index = version
const ECC_PER_BLOCK := [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
const BLOCKS := [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25]
const MAX_BYTES := 2953    ## what version 40-L holds in byte mode

var size := 0
var version := 0
var _dark: PackedByteArray
var _func: PackedByteArray


## Most bytes a QR code can hold (longer text gives an empty image).
static func fits(text: String) -> bool:
	return text.to_utf8_buffer().size() <= MAX_BYTES


## The QR code of the text as a black-on-white image: `scale` pixels per module, a 4-module quiet zone.
static func image(text: String, scale := 4) -> Image:
	var q := QR.new()
	if not q.encode(text.to_utf8_buffer()):
		return null
	var n := (q.size + 8) * scale
	var img := Image.create(n, n, false, Image.FORMAT_L8)
	img.fill(Color.WHITE)
	for y in q.size:
		for x in q.size:
			if q.dark(x, y):
				img.fill_rect(Rect2i((x + 4) * scale, (y + 4) * scale, scale, scale), Color.BLACK)
	return img


func dark(x: int, y: int) -> bool:
	return _dark[y * size + x] == 1


func encode(data: PackedByteArray) -> bool:
	version = 0
	for v in range(1, 41):
		var cap := _data_codewords(v) * 8
		var need := 4 + (8 if v <= 9 else 16) + data.size() * 8
		if need <= cap:
			version = v
			break
	if version == 0:
		return false
	# ---- bit stream: byte mode, count, data, terminator, padding
	var bits: Array[int] = []
	_append(bits, 4, 4)
	_append(bits, data.size(), 8 if version <= 9 else 16)
	for b in data:
		_append(bits, b, 8)
	var cap_bits := _data_codewords(version) * 8
	_append(bits, 0, mini(4, cap_bits - bits.size()))
	_append(bits, 0, (8 - bits.size() % 8) % 8)
	var words := PackedByteArray()
	for i in range(0, bits.size(), 8):
		var w := 0
		for j in 8:
			w = (w << 1) | bits[i + j]
		words.append(w)
	var pad := 0xEC
	while words.size() < _data_codewords(version):
		words.append(pad)
		pad = 0x11 if pad == 0xEC else 0xEC
	var all := _add_ecc(words)
	# ---- modules
	size = version * 4 + 17
	_dark = PackedByteArray()
	_dark.resize(size * size)
	_func = PackedByteArray()
	_func.resize(size * size)
	_draw_function_patterns()
	_draw_codewords(all)
	var best := 0
	var best_pen := 1 << 30
	for m in 8:
		_apply_mask(m)
		_draw_format(m)
		var pen := _penalty()
		if pen < best_pen:
			best_pen = pen
			best = m
		_apply_mask(m)
	_apply_mask(best)
	_draw_format(best)
	return true


static func _append(bits: Array[int], v: int, n: int) -> void:
	for i in range(n - 1, -1, -1):
		bits.append((v >> i) & 1)


static func _raw_modules(v: int) -> int:
	var r := (16 * v + 128) * v + 64
	if v >= 2:
		var na := v / 7 + 2
		r -= (25 * na - 10) * na - 55
		if v >= 7:
			r -= 36
	return r


static func _data_codewords(v: int) -> int:
	return _raw_modules(v) / 8 - ECC_PER_BLOCK[v] * BLOCKS[v]


# ---------------------------------------------------------------- Reed-Solomon
static func _mul(x: int, y: int) -> int:
	var z := 0
	for i in range(7, -1, -1):
		z = ((z << 1) ^ ((z >> 7) * 0x11D)) & 0xFF
		z ^= ((y >> i) & 1) * x
	return z


static func _divisor(n: int) -> PackedByteArray:
	var r := PackedByteArray()
	r.resize(n)
	r[n - 1] = 1
	var root := 1
	for i in n:
		for j in n:
			r[j] = _mul(r[j], root)
			if j + 1 < n:
				r[j] ^= r[j + 1]
		root = _mul(root, 0x02)
	return r


static func _remainder(data: PackedByteArray, div: PackedByteArray) -> PackedByteArray:
	var r := PackedByteArray()
	r.resize(div.size())
	for b in data:
		var factor := b ^ r[0]
		r.remove_at(0)
		r.append(0)
		for i in div.size():
			r[i] ^= _mul(div[i], factor)
	return r


func _add_ecc(data: PackedByteArray) -> PackedByteArray:
	var nb: int = BLOCKS[version]
	var ecc_len: int = ECC_PER_BLOCK[version]
	var raw := _raw_modules(version) / 8
	var n_short := nb - raw % nb
	var short_len := raw / nb
	var div := _divisor(ecc_len)
	var blocks: Array[PackedByteArray] = []
	var k := 0
	for i in nb:
		var n := short_len - ecc_len + (0 if i < n_short else 1)
		var dat := data.slice(k, k + n)
		k += n
		var ecc := _remainder(dat, div)
		if i < n_short:
			dat.append(0)
		dat.append_array(ecc)
		blocks.append(dat)
	var out := PackedByteArray()
	for i in blocks[0].size():
		for j in blocks.size():
			if i != short_len - ecc_len or j >= n_short:
				out.append(blocks[j][i])
	return out


# ---------------------------------------------------------------- drawing
func _put(x: int, y: int, d: bool, is_func := true) -> void:
	_dark[y * size + x] = 1 if d else 0
	if is_func:
		_func[y * size + x] = 1


func _draw_function_patterns() -> void:
	for i in size:
		_put(6, i, i % 2 == 0)
		_put(i, 6, i % 2 == 0)
	for c in [Vector2i(3, 3), Vector2i(size - 4, 3), Vector2i(3, size - 4)]:
		for dy in range(-4, 5):
			for dx in range(-4, 5):
				var xx: int = c.x + dx
				var yy: int = c.y + dy
				if xx >= 0 and xx < size and yy >= 0 and yy < size:
					var dist := maxi(absi(dx), absi(dy))
					_put(xx, yy, dist != 2 and dist != 4)
	var pos := _align_positions()
	var na := pos.size()
	for i in na:
		for j in na:
			if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
				continue
			for dy in range(-2, 3):
				for dx in range(-2, 3):
					_put(pos[i] + dx, pos[j] + dy, maxi(absi(dx), absi(dy)) != 1)
	_draw_format(0)
	if version >= 7:
		var rem := version
		for i in 12:
			rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
		var bits := (version << 12) | rem
		for i in 18:
			var d := ((bits >> i) & 1) == 1
			var a := size - 11 + i % 3
			var b := i / 3
			_put(a, b, d)
			_put(b, a, d)


func _align_positions() -> Array[int]:
	var out: Array[int] = []
	if version == 1:
		return out
	var na := version / 7 + 2
	var step := (version * 8 + na * 3 + 5) / (na * 4 - 4) * 2
	out.append(6)
	for i in na - 1:
		out.insert(1, size - 7 - i * step)
	return out


func _draw_format(mask: int) -> void:
	var data := (ECC_L << 3) | mask
	var rem := data
	for i in 10:
		rem = (rem << 1) ^ ((rem >> 9) * 0x537)
	var bits := ((data << 10) | rem) ^ 0x5412
	var bit := func(i: int) -> bool: return ((bits >> i) & 1) == 1
	for i in 6:
		_put(8, i, bit.call(i))
	_put(8, 7, bit.call(6))
	_put(8, 8, bit.call(7))
	_put(7, 8, bit.call(8))
	for i in range(9, 15):
		_put(14 - i, 8, bit.call(i))
	for i in 8:
		_put(size - 1 - i, 8, bit.call(i))
	for i in range(8, 15):
		_put(8, size - 15 + i, bit.call(i))
	_put(8, size - 8, true)


func _draw_codewords(data: PackedByteArray) -> void:
	var i := 0
	var right := size - 1
	while right >= 1:
		if right == 6:
			right = 5
		for vert in size:
			for j in 2:
				var x := right - j
				var upward := ((right + 1) & 2) == 0
				var y := size - 1 - vert if upward else vert
				if _func[y * size + x] == 0 and i < data.size() * 8:
					_dark[y * size + x] = (data[i >> 3] >> (7 - (i & 7))) & 1
					i += 1
		right -= 2


func _apply_mask(m: int) -> void:
	for y in size:
		for x in size:
			if _func[y * size + x] == 1:
				continue
			var inv := false
			match m:
				0: inv = (x + y) % 2 == 0
				1: inv = y % 2 == 0
				2: inv = x % 3 == 0
				3: inv = (x + y) % 3 == 0
				4: inv = (x / 3 + y / 2) % 2 == 0
				5: inv = x * y % 2 + x * y % 3 == 0
				6: inv = (x * y % 2 + x * y % 3) % 2 == 0
				7: inv = ((x + y) % 2 + x * y % 3) % 2 == 0
			if inv:
				_dark[y * size + x] ^= 1


## Simplified penalty (runs, 2x2 blocks, dark balance) to pick a readable mask.
func _penalty() -> int:
	var p := 0
	for y in size:
		var run := 1
		for x in range(1, size):
			if _dark[y * size + x] == _dark[y * size + x - 1]:
				run += 1
				if run == 5:
					p += 3
				elif run > 5:
					p += 1
			else:
				run = 1
	for x in size:
		var run := 1
		for y in range(1, size):
			if _dark[y * size + x] == _dark[(y - 1) * size + x]:
				run += 1
				if run == 5:
					p += 3
				elif run > 5:
					p += 1
			else:
				run = 1
	var dark_n := 0
	for y in size:
		for x in size:
			var c := _dark[y * size + x]
			dark_n += c
			if x + 1 < size and y + 1 < size and c == _dark[y * size + x + 1] and c == _dark[(y + 1) * size + x] and c == _dark[(y + 1) * size + x + 1]:
				p += 3
	var k := absi(dark_n * 20 - size * size * 10) / (size * size)
	return p + k * 10
