#!/usr/bin/env python3
"""Монтаж версии 2: русский закадровый голос, переходы, подписи времени, финал с телефоном,
титры-советы и THE END.

    python3 build_v2.py [out.mp4] [--draft]

Раскадровка задана по времени и не сдвигается от переходов: наплыв берёт по полкадра-«ручке» с обеих
сторон склейки (стоп-кадр крайнего кадра). Если клипа ещё нет, вместо него ставится чёрная карточка с
подписью, чтобы ролик можно было смотреть по мере готовности сцен.
"""
import os, sys, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
W, H, FPS = 1920, 1080, 24
BAR = (H - round(W / 2.39)) // 2            # каше 2.39:1
DRAFT = '--draft' in sys.argv
OUT = next((a for a in sys.argv[1:] if not a.startswith('--')), 'final_1080.mp4')
SERIF = 'fonts/CormorantGaramond.ttf'
ITALIC = 'fonts/CormorantGaramond-Italic.ttf'
INK = (236, 226, 208)

# id, начало, длительность, переход НА этот шот (тип, длительность), подпись-заглушка
SHOTS = [
    ('S01',   0.0,  9.0, None,              'Глина становится человеком'),
    ('S02',   9.0,  4.0, ('flash', 0.16),   'Молния. Первый крик'),
    ('S03',  13.0, 11.5, ('dip', 0.6),      '3:07 ночи. Мать качает ребёнка'),
    ('S04',  24.5,  6.0, ('warm', 0.8),     'Ему три года. Он падает'),
    ('S05',  30.5, 11.5, ('dissolve', 0.8), 'Годы идут. Она стареет и несёт его'),
    ('S05B', 42.0, 12.0, ('dissolve', 1.4), 'Он уехал. Она ждёт звонка в 3:07 ночи'),
    ('S06A', 54.0,  7.5, ('dip', 1.0),      'Он вернулся и опускается к её ногам'),
    ('S06',  61.5,  5.0, ('cut', 0),        'Её ноги. Золотой свет'),
    ('S07',  66.5,  7.0, ('flash', 0.12),   'Небо плачет'),
    ('S08',  73.5,  1.0, ('cut', 0),        'Тишина'),
    ('S09',  74.5, 12.0, ('dissolve', 1.0), 'Рассвет. Она открывает глаза и улыбается'),
    ('S09B', 86.5,  5.0, ('dissolve', 0.7), 'Он поднимает голову. Её рука у него на голове'),
]
T_TITLE, T_CRED, T_END, T_TOTAL = 91.5, 105.0, 136.5, 140.5
START = {s[0]: s[1] for s in SHOTS}

# подписи времени: шот, текст, появление и исчезновение (секунды от начала шота)
CAPTIONS = [
    ('S03',  'ТЕБЕ ПОЛГОДА',         1.0, 4.6),
    ('S04',  'ТЕБЕ ТРИ ГОДА',        0.5, 3.6),
    ('S05',  'ВЕСНА',                2.0, 3.0),
    ('S05',  'ЛЕТО',                 3.15, 4.15),
    ('S05',  'ОСЕНЬ',                4.3, 5.0),
    ('S05',  'ЗИМА',                 5.15, 7.0),
    ('S05B', 'ТРИДЦАТЬ ЛЕТ СПУСТЯ',  1.0, 5.0),
]

CREDITS = [
    ('h', 'ЧТО ХОТЕЛ СКАЗАТЬ ЭТОТ ФИЛЬМ'),
    ('p', 'Мать отдаёт тебе годы, сон и здоровье —'),
    ('p', 'и никогда не выставляет счёт.'),
    ('p', 'А мы вспоминаем об этом,'),
    ('p', 'когда звонить уже некому.'),
    ('gap', ''),
    ('h', 'ПОКА ОНА РЯДОМ'),
    ('p', 'Позвони сегодня. Не «на неделе».'),
    ('p', 'Спроси, как она, — и дослушай ответ.'),
    ('p', 'Приезжай без повода.'),
    ('p', 'Не повышай на неё голос.'),
    ('p', 'Говори «спасибо» вслух.'),
    ('p', 'Попроси прощения первым.'),
    ('p', 'Помогай раньше, чем она попросит.'),
    ('p', 'Обними её. Просто так.'),
    ('gap', ''),
    ('h', 'ПОЧЕМУ'),
    ('p', 'Потому что она не спала ради тебя.'),
    ('p', 'Потому что ей было больно вместо тебя.'),
    ('p', 'Потому что она ждёт — каждый день.'),
    ('p', 'И потому что время идёт только в одну сторону.'),
    ('gap', ''),
    ('q', '«Рай — под ногами матерей»'),
]

# звук: файл, старт, громкость, обрезка (0 = весь), fade-in, fade-out, шина
R = 'audio/raw/'
def at(shot, dt=0.0):
    return START[shot] + dt
LAYERS = [
    (R + 'score_v2.mp3',      0.0,            0.95, 0,   0.02, 2.5, 'music'),
    (R + 'sfx_clay.mp3',      0.0,            0.40, 5,   1.5,  1.5, 'amb'),
    (R + 'sfx_thunder.mp3',   at('S02'),      1.30, 5,   0.01, 1.5, 'hit'),
    (R + 'sfx_firstcry.mp3',  at('S02', 0.6), 0.95, 3.4, 0.05, 1.4, 'amb'),
    (R + 'sfx_teething.mp3',  at('S03', 0.2), 0.45, 7,   0.4,  2.0, 'amb'),
    (R + 'sfx_clock.mp3',     at('S03'),      0.22, 8,   0.5,  1.5, 'amb'),
    (R + 'sfx_fall.mp3',      at('S04', 1.78), 0.60, 4.0, 0.02, 0.8, 'fall'),
    (R + 'sfx_aging.mp3',     at('S05'),      0.55, 6,   0.4,  1.5, 'amb'),
    (R + 'sfx_wind.mp3',      at('S05', 4.6), 0.55, 8,   1.2,  2.0, 'amb'),
    (R + 'sfx_clock.mp3',     at('S05B'),     0.50, 8,   1.0,  1.0, 'amb'),
    (R + 'sfx_clock.mp3',     at('S05B', 7),  0.50, 5.6, 1.0,  1.2, 'amb'),
    (R + 'sfx_rain.mp3',      at('S06'),      1.00, 12,  0.8,  0.05, 'amb'),
    (R + 'sfx_quake.mp3',     at('S06', 1.0), 0.90, 6,   0.5,  1.0, 'amb'),
    (R + 'sfx_thunder.mp3',   at('S07', 1.4), 1.40, 5.5, 0.01, 0.05, 'hit'),
    (R + 'sfx_morning.mp3',   at('S09'),      0.32, 9,   1.5,  2.0, 'amb'),
    (R + 'sfx_morning.mp3',   at('S09', 8),   0.30, 9,   2.0,  2.5, 'amb'),
    (R + 'sfx_ring.mp3',      T_TITLE + 0.6,  0.60, 1.5, 0.01, 0.3, 'room'),
    (R + 'sfx_ring.mp3',      T_TITLE + 3.0,  0.60, 1.5, 0.01, 0.3, 'room'),
    (R + 'sfx_pickup.mp3',    T_TITLE + 4.7,  3.50, 0,   0.01, 0.2, 'room'),
    (R + 'vo_ru/01_clay.mp3',    at('S01', 1.2),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/02_cry.mp3',     at('S02', 1.6),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/03_night.mp3',   at('S03', 2.3),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/04_fall.mp3',    at('S04', 0.45), 1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/05_years.mp3',   at('S05', 0.7),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/06_left.mp3',    at('S05B', 0.9), 1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/07_return.mp3',  at('S06A', 0.8), 1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/08_heaven.mp3',  at('S06', 1.5),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/09_sky.mp3',     at('S07', 3.7),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/10_forgive.mp3', at('S09', 1.5),  1.0, 0, 0.01, 0.05, 'vo'),
    (R + 'vo_ru/11_hello.mp3',   T_TITLE + 5.6,   1.0, 0, 0.01, 0.05, 'vo'),
]
MUTE = (at('S08'), at('S09'))               # тишина перед рассветом: музыка и шумы выключены


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit('ffmpeg failed:\n' + ' '.join(cmd)[:3000] + '\n' + r.stderr[-3000:])


def dur(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                capture_output=True, text=True).stdout)


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
    return f


def spaced(draw, xy, text, f, fill, tracking=0.0, anchor_center=False):
    """Текст с разрядкой (доля кегля). Возвращает ширину."""
    widths = [draw.textlength(ch, font=f) for ch in text]
    tr = tracking * f.size
    total = sum(widths) + tr * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    if draw is not None and fill is not None:
        for ch, w in zip(text, widths):
            draw.text((x, y), ch, font=f, fill=fill)
            x += w + tr
    return total


def caption_png(text, path):
    """Подпись времени: капитель с разрядкой внизу слева, с мягкой тенью."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f = font(SERIF, 46, 'Medium')
    x, y = 150, H - BAR - 112
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    spaced(ds, (x, y + 2), text, f, (0, 0, 0, 230), 0.22)
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    im = Image.alpha_composite(im, sh); im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    d.line([(x, y - 16), (x + 56, y - 16)], fill=INK + (210,), width=2)
    spaced(d, (x, y), text, f, INK + (245,), 0.22)
    im.save(path)


def text_png(lines, path, size=(W, H)):
    """lines: [(текст, шрифт, кегль, начертание, разрядка, y, цвет)] по центру."""
    im = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for text, fp, sz, wt, tr, y, col in lines:
        spaced(d, (size[0] / 2, y), text, font(fp, sz, wt), col, tr, anchor_center=True)
    im.save(path)


def credits_png(path):
    rows = []; y = 0
    for kind, text in CREDITS:
        if kind == 'h':
            y += 46; rows.append((text, SERIF, 34, 'SemiBold', 0.26, y, (196, 168, 128, 255))); y += 92
        elif kind == 'p':
            rows.append((text, SERIF, 52, 'Regular', 0.01, y, INK + (255,))); y += 78
        elif kind == 'q':
            y += 30; rows.append((text, ITALIC, 54, 'Italic', 0.01, y, INK + (255,))); y += 90
        else:
            y += 70
    text_png(rows, path, (W, y + 10))
    return y + 10


def build_video(tmp):
    segs = []
    for i, (sid, t0, d, tr, cap) in enumerate(SHOTS):
        nxt = SHOTS[i + 1][3] if i + 1 < len(SHOTS) else None
        hin = tr[1] / 2 if tr and tr[0] == 'dissolve' else 0.0
        hout = nxt[1] / 2 if nxt and nxt[0] == 'dissolve' else 0.0
        clip = f'clips/{sid}.mp4'
        ins = []; fc = []
        if os.path.exists(clip) and os.path.getsize(clip) > 0:
            cd = dur(clip); k = d / cd
            ins += ['-i', clip]
            v = f'[0:v]setpts={k:.6f}*PTS,fps={FPS},scale={W}:-2:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1'
            note = '' if abs(k - 1) < 0.01 else f' (клип {cd:.1f} с растянут до {d:.1f} с)'
        else:
            png = f'{tmp}/ph_{sid}.png'
            text_png([('сцена в работе', ITALIC, 30, 'Italic', 0.02, H / 2 - 60, (120, 120, 120, 255)),
                      (cap, ITALIC, 44, 'Italic', 0.01, H / 2 - 10, (170, 170, 170, 255))], png)
            ins += ['-loop', '1', '-framerate', str(FPS), '-t', f'{d}', '-i', png]
            v = f'color=c=0x08080a:s={W}x{H}:r={FPS}:d={d}[bg];[bg][0:v]overlay=shortest=1,setsar=1'
            note = ' (ЗАГЛУШКА: клипа нет)'
        v += f',trim=0:{d},setpts=PTS-STARTPTS'
        # переход на этот шот и с него (в пределах собственной длительности)
        if tr and tr[0] in ('dip', 'warm', 'flash'):
            col = {'dip': 'black', 'warm': '0xffe6c0', 'flash': 'white'}[tr[0]]
            fd = tr[1] if tr[0] == 'flash' else tr[1] / 2
            v += f',fade=t=in:st=0:d={fd}:color={col}'
        if nxt and nxt[0] in ('dip', 'warm'):
            col = {'dip': 'black', 'warm': '0xffe6c0'}[nxt[0]]
            v += f',fade=t=out:st={d - nxt[1] / 2}:d={nxt[1] / 2}:color={col}'
        if i == len(SHOTS) - 1:
            v += f',fade=t=out:st={d - 1.6}:d=1.6:color=black'
        if hin or hout:
            v += f',tpad=start_mode=clone:start_duration={hin}:stop_mode=clone:stop_duration={hout}'
        fc.append(v + '[v0]'); last = 'v0'; n = 1
        for csid, text, a, b in CAPTIONS:
            if csid != sid:
                continue
            png = f'{tmp}/cap_{sid}_{n}.png'; caption_png(text, png)
            ins += ['-loop', '1', '-framerate', str(FPS), '-t', f'{d + hin + hout}', '-i', png]
            a += hin; b += hin
            fc.append(f'[{n}:v]format=rgba,fade=t=in:st={a}:d=0.5:alpha=1,fade=t=out:st={b}:d=0.6:alpha=1[c{n}];'
                      f'[{last}][c{n}]overlay=enable=\'between(t,{a},{b + 0.6})\'[v{n}]')
            last = f'v{n}'; n += 1
        seg = f'{tmp}/seg_{sid}.mp4'
        run(['ffmpeg', '-y', '-v', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', f'[{last}]', '-r', str(FPS),
             '-t', f'{d + hin + hout}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', seg])
        segs.append((seg, d + hin + hout, tr))
        print(f'  {sid}: {t0:6.1f}–{t0 + d:6.1f}{note}', flush=True)

    # --- титр, титры-советы, THE END
    tt = T_CRED - T_TITLE
    p1, p2 = f'{tmp}/t1.png', f'{tmp}/t2.png'
    f_ = font(SERIF, 84, 'Regular'); dd = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    w1 = dd.textlength('Позвони маме. ', font=f_); w2 = dd.textlength('Сегодня.', font=f_); x0 = (W - w1 - w2) / 2
    for png, txt, x in ((p1, 'Позвони маме.', x0), (p2, 'Сегодня.', x0 + w1)):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(im).text((x, H / 2 - 60), txt, font=f_, fill=INK + (255,)); im.save(png)
    a1, a2, b = 9.0, 10.3, tt - 1.0
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r={FPS}:d={tt}',
         '-loop', '1', '-framerate', str(FPS), '-t', f'{tt}', '-i', p1, '-loop', '1', '-framerate', str(FPS), '-t', f'{tt}', '-i', p2,
         '-filter_complex',
         f'[1:v]format=rgba,fade=t=in:st={a1}:d=1.0:alpha=1,fade=t=out:st={b}:d=0.9:alpha=1[a];'
         f'[2:v]format=rgba,fade=t=in:st={a2}:d=1.0:alpha=1,fade=t=out:st={b}:d=0.9:alpha=1[b];'
         f'[0:v][a]overlay[x];[x][b]overlay,format=yuv420p[v]', '-map', '[v]', '-t', f'{tt}',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', f'{tmp}/title.mp4'])
    tc = T_END - T_CRED
    ch = credits_png(f'{tmp}/credits.png')
    speed = (ch + H * 0.86) / tc
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r={FPS}:d={tc}',
         '-loop', '1', '-framerate', str(FPS), '-t', f'{tc}', '-i', f'{tmp}/credits.png', '-filter_complex',
         f'[0:v][1:v]overlay=x=0:y=\'{H * 0.93:.0f}-t*{speed:.3f}\',format=yuv420p[v]', '-map', '[v]', '-t', f'{tc}',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', f'{tmp}/credits.mp4'])
    te = T_TOTAL - T_END
    text_png([('THE END', SERIF, 96, 'Regular', 0.30, H / 2 - 62, INK + (255,))], f'{tmp}/end.png')
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r={FPS}:d={te}',
         '-loop', '1', '-framerate', str(FPS), '-t', f'{te}', '-i', f'{tmp}/end.png', '-filter_complex',
         f'[1:v]format=rgba,fade=t=in:st=0.3:d=1.0:alpha=1,fade=t=out:st={te - 1.2}:d=1.0:alpha=1[a];[0:v][a]overlay,format=yuv420p[v]',
         '-map', '[v]', '-t', f'{te}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', f'{tmp}/end.mp4'])
    for name, d in (('title', tt), ('credits', tc), ('end', te)):
        segs.append((f'{tmp}/{name}.mp4', d, ('cut', 0)))
    print(f'  титр {T_TITLE}–{T_CRED}, титры {T_CRED}–{T_END} ({speed:.0f} px/с), THE END {T_END}–{T_TOTAL}', flush=True)

    # --- склейка: наплывы через xfade, остальное встык
    ins = []; fc = []
    for seg, _, _ in segs:
        ins += ['-i', seg]
    for i in range(len(segs)):                     # одна временная база (1/24) для xfade и concat
        fc.append(f'[{i}:v]fps={FPS},setpts=PTS-STARTPTS[s{i}]')
    acc = 's0'; acc_d = segs[0][1]
    for i in range(1, len(segs)):
        _, d, tr = segs[i]
        if tr and tr[0] == 'dissolve':
            fc.append(f'[{acc}][s{i}]xfade=transition=fade:duration={tr[1]}:offset={acc_d - tr[1]:.4f}[x{i}]'); acc_d += d - tr[1]
        else:
            fc.append(f'[{acc}][s{i}]concat=n=2:v=1:a=0,fps={FPS}[x{i}]'); acc_d += d
        acc = f'x{i}'
    # грейд: чуть тепла, виньетка и каше только на картинке, зерно на всём
    grade = (f"[{acc}]eq=contrast=1.03:saturation=1.0,colorbalance=rs=0.015:bs=-0.015:rh=0.01:bh=-0.01,"
             f"vignette=PI/8:enable='lt(t,{T_TITLE})',"
             f"drawbox=x=0:y=0:w=iw:h={BAR}:color=black:t=fill,drawbox=x=0:y=ih-{BAR}:w=iw:h={BAR}:color=black:t=fill,"
             f"noise=alls=5:allf=t:enable='lt(t,{T_TITLE})',noise=alls=2:allf=t:enable='gte(t,{T_TITLE})',format=yuv420p[vout]")
    fc.append(grade)
    cut = f'{tmp}/cut.mp4'
    enc = ['-c:v', 'libx264', '-preset', 'veryfast' if DRAFT else 'slow', '-crf', '21' if DRAFT else '18', '-tune', 'grain',
           '-maxrate', '6500k', '-bufsize', '13M', '-pix_fmt', 'yuv420p']
    run(['ffmpeg', '-y', '-v', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[vout]', '-t', f'{T_TOTAL}'] + enc + [cut])
    return cut, acc_d


def build_audio(tmp):
    ins = []; fc = []; bus = {'music': [], 'amb': [], 'hit': [], 'vo': [], 'fall': [], 'room': []}
    for i, (f, s, vol, trim, fi, fo, b) in enumerate(LAYERS):
        if not os.path.exists(f):
            sys.exit('нет звукового файла ' + f)
        ins += ['-i', f]
        d = trim or dur(f)
        ms = int(round(s * 1000))
        fc.append(f'[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{d},afade=t=in:d={fi},'
                  f'afade=t=out:st={max(0, d - fo)}:d={fo},volume={vol},adelay={ms}|{ms}[a{i}]')
        bus[b].append(f'[a{i}]')
    def mix(names, out, extra=''):
        fc.append(''.join(names) + f'amix=inputs={len(names)}:normalize=0:duration=longest,apad=whole_dur={T_TOTAL},atrim=0:{T_TOTAL}{extra}[{out}]')
    a, b = MUTE                                   # быстрый, но не щёлкающий уход в тишину и мягкий возврат
    gate = f",volume='min(1,max(0,({a}-t)/0.10)+max(0,(t-{b})/0.35))':eval=frame"
    # голос: срез низа, лёгкая компрессия, теплота
    # голос: срез низа, лёгкая компрессия, теплота и едва слышная «комната», чтобы он сел в музыку
    mix(bus['vo'], 'vo0', ',highpass=f=75,equalizer=f=220:t=q:w=1.0:g=1.5,equalizer=f=3200:t=q:w=1.2:g=2.0,'
                          'acompressor=threshold=0.09:ratio=3:attack=12:release=180:makeup=1.8,'
                          'aecho=0.9:0.9:31|57|93:0.10|0.07|0.04')
    fc.append('[vo0]asplit=4[vo][sc1][sc2][sc3]')
    mix(bus['music'], 'mus0', gate)
    mix(bus['fall'], 'fall', ',equalizer=f=3200:t=q:w=1.0:g=-5')          # резкий детский плач смягчён
    mix(bus['room'], 'room', ',aecho=0.8:0.8:43|81|127:0.22|0.14|0.08')    # телефон звучит в комнате
    fc.append("[%s]%samix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%s,atrim=0:%s%s[amb0]"
              % (']['.join(x.strip('[]') for x in bus['amb'] + ['fall']), '', len(bus['amb']) + 1, T_TOTAL, T_TOTAL, gate))
    mix(bus['hit'], 'hit0', gate)
    # музыка, шумы и удары уходят под голос
    fc.append('[mus0][sc1]sidechaincompress=threshold=0.02:ratio=8:attack=90:release=650:makeup=1[mus]')
    fc.append('[amb0][sc2]sidechaincompress=threshold=0.02:ratio=12:attack=60:release=550:makeup=1[amb]')
    fc.append('[hit0][sc3]sidechaincompress=threshold=0.03:ratio=5:attack=60:release=500:makeup=1[hit]')
    fc.append(f'[mus][amb][hit][room][vo]amix=inputs=5:normalize=0:duration=longest,volume=1.0,alimiter=limit=0.89,'
              f'loudnorm=I=-15:TP=-1.5:LRA=13,atrim=0:{T_TOTAL},afade=t=out:st={T_TOTAL - 1.5}:d=1.5[out]')
    wav = f'{tmp}/mix.wav'
    run(['ffmpeg', '-y', '-v', 'error'] + ins + ['-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-c:a', 'pcm_s24le', wav])
    return wav


def main():
    tmp = tempfile.mkdtemp(prefix='mf_')
    try:
        print('видео:'); cut, d = build_video(tmp)
        print(f'звук: {len(LAYERS)} дорожек'); wav = build_audio(tmp)
        run(['ffmpeg', '-y', '-v', 'error', '-i', cut, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
             '-c:a', 'aac', '-b:a', '256k', '-t', f'{T_TOTAL}', '-movflags', '+faststart', OUT])
        run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '256k', 'audio/master_mix_v2.m4a'])
        print(f'OK: {OUT}  {dur(OUT):.2f} с, {os.path.getsize(OUT) / 1e6:.1f} МБ (картинка {d:.2f} с)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
