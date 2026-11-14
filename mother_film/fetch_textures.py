#!/usr/bin/env python3
"""Скачивает CC0-текстуры Poly Haven (2k) для глиняных материалов. Использование: fetch_textures.py [папка]"""
import json, os, sys, urllib.request
D = sys.argv[1] if len(sys.argv) > 1 else '/home/user/assets/tex'
NAMES = ['clay_plaster', 'mud_cracked_dry_03', 'brown_mud_02', 'rock_face_03', 'clay_floor_001', 'cliff_side']
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor', 'Rough': 'rough', 'Displacement': 'disp'}
os.makedirs(D, exist_ok=True)
hdr = {'User-Agent': 'Mozilla/5.0'}
for n in NAMES:
    info = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.polyhaven.com/files/{n}', headers=hdr)))
    for k, short in MAPS.items():
        if k not in info:
            print('no', k, 'for', n, list(info)[:12]); continue
        r = info[k]['2k']
        fmt = 'jpg' if 'jpg' in r else 'png'
        out = f'{D}/{n}_{short}.{fmt}'
        if not os.path.exists(out):
            with urllib.request.urlopen(urllib.request.Request(r[fmt]['url'], headers=hdr)) as s, open(out, 'wb') as f:
                f.write(s.read())
        print(out, os.path.getsize(out))
