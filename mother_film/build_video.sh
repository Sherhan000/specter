#!/usr/bin/env bash
# Собирает финальный ролик 60 c: клипы из clips/S01.mp4 … S09.mp4 + мастер-звук.
# Нет клипа — ставится карточка-заглушка (так получается аниматик).
# Использование: ./build_video.sh [4k|1080] [имя_выхода.mp4]
set -euo pipefail
cd "$(dirname "$0")"
RES=${1:-4k}; OUT=${2:-final_${RES}.mp4}
if [ "$RES" = 4k ]; then W=3840; H=2160; MAXR=45M; else W=1920; H=1080; MAXR=14M; fi
FPS=24
FONT=$(fc-match -f '%{file}' 'Liberation Serif:style=Regular' 2>/dev/null || echo /usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf)
FONTI=$(fc-match -f '%{file}' 'Liberation Serif:style=Italic' 2>/dev/null || echo "$FONT")
# id | длительность | подпись заглушки
SHOTS=(
 "S01|9|1. Darkness. Clay becomes a human. Heartbeat like thunder."
 "S02|4|2. Lightning strikes. First cry shakes the mountains."
 "S03|7|3. 3 AM. Teething baby. Sleepless mother, red eyes, Ash-Sharh."
 "S04|5|4. The child falls. Her heart falls faster."
 "S05|6|5. She ages in seconds. White hair. Shaking hands. Still carrying him."
 "S06|5|6. The grown son looks down at his mother's feet. Golden light."
 "S07|7|7. The sky cries. Rain over the world. Mountains tremble. Lightning."
 "S08|1|8. Silence."
 "S09|12|9. Sunrise. Warm light on her face. She smiles."
)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
list=$TMP/list.txt; : > $list; n=0
for s in "${SHOTS[@]}"; do IFS='|' read -r id d cap <<<"$s"; n=$((n+1))
  seg=$TMP/$id.mp4
  if [ -s clips/$id.mp4 ]; then
    cd_=$(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/$id.mp4)
    # клипы отрендерены в 2.39:1 — вписываем по ширине, каше добавляется полями
    # клип короче шота -> плавно замедляем; длиннее -> обрезаем
    k=$(python3 -c "print(max(1.0, $d/$cd_))")
    ffmpeg -y -v error -i clips/$id.mp4 -an -vf "setpts=${k}*PTS,fps=$FPS,scale=$W:-2:flags=lanczos,pad=$W:$H:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p" -t $d -c:v libx264 -preset medium -crf 16 $seg
    echo "  $id: clip ($cd_ s -> $d s)"
  else
    printf '%s' "$cap" > $TMP/$id.txt
    ffmpeg -y -v error -f lavfi -i "color=c=0x0b0b0d:s=${W}x${H}:r=$FPS:d=$d" -vf "drawtext=fontfile=$FONTI:textfile=$TMP/$id.txt:fontcolor=0x8a8a8a:fontsize=$((H/30)):x=(w-tw)/2:y=(h-th)/2,format=yuv420p" -c:v libx264 -preset veryfast -crf 20 $seg
    echo "  $id: placeholder"
  fi
  echo "file '$seg'" >> $list
done
# S10: чёрный экран, капля, титр
ffmpeg -y -v error -f lavfi -i "color=c=black:s=${W}x${H}:r=$FPS:d=4" -vf "drawtext=fontfile=$FONT:text='Call your mother today.':fontcolor=white:fontsize=$((H/18)):x=(w-tw)/2:y=(h-th)/2:alpha='if(lt(t,0.9),0,if(lt(t,1.9),(t-0.9),1))',format=yuv420p" -c:v libx264 -preset medium -crf 16 $TMP/S10.mp4
echo "file '$TMP/S10.mp4'" >> $list
ffmpeg -y -v error -f concat -safe 0 -i $list -c copy $TMP/cut.mp4
# Грейд (лёгкий — свет и цвет уже заложены в 3D-рендере): чуть тепла, каше 2.39:1, зерно, виньетка,
# лёгкий подсвет кадра на молниях (9.0 и 37.4 c).
BAR=$(( (H - W*100/239) / 2 ))
VF="eq=contrast=1.03:saturation=1.0,colorbalance=rs=0.015:bs=-0.015:rh=0.01:bh=-0.01,"
VF+="eq=brightness=0.16:enable='between(t,9.00,9.10)+between(t,9.18,9.24)+between(t,37.40,37.48)+between(t,37.55,37.60)',"
VF+="vignette=PI/8,noise=alls=5:allf=t,"
VF+="drawbox=x=0:y=0:w=iw:h=$BAR:color=black:t=fill,drawbox=x=0:y=ih-$BAR:w=iw:h=$BAR:color=black:t=fill,format=yuv420p"
[ -f audio/master_mix.wav ] || ./mix_audio.sh  # wav не хранится в git, пересобирается из audio/raw
ffmpeg -y -v error -i $TMP/cut.mp4 -i audio/master_mix.wav -vf "$VF" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -tune grain -maxrate $MAXR -bufsize $MAXR -pix_fmt yuv420p -c:a aac -b:a 320k -t 60 -movflags +faststart "$OUT"
echo "OK: $OUT"
