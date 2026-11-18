#!/usr/bin/env bash
# Собирает мастер-звук 60 c из исходников в audio/raw. Использование: ./mix_audio.sh [brian|george|lily]
set -euo pipefail
cd "$(dirname "$0")"
VO=${1:-brian}
R=audio/raw
# layer: file start_sec volume [trim_sec] [fadein] [fadeout_len]
L() { echo "$1|$2|$3|${4:-0}|${5:-0.02}|${6:-0.3}"; }
LAYERS=(
 "$(L $R/music.mp3         0    0.85 43   0.02 0.4)"
 "$(L $R/sfx_clay.mp3      0    0.45 5    1.5  1.5)"
 "$(L $R/sfx_heartbeat.mp3 0    1.30 9    0.5  0.6)"
 "$(L $R/sfx_thunder.mp3   9.0  1.40 5    0.01 1.0)"
 "$(L $R/sfx_firstcry.mp3  9.35 1.10 3.8  0.05 0.8)"
 "$(L $R/sfx_teething.mp3  13.0 0.85 7    0.3  0.5)"
 "$(L $R/sfx_fall.mp3      20.0 0.95 4.6  0.05 0.6)"
 "$(L $R/sfx_aging.mp3     25.0 0.75 6    0.4  0.6)"
 "$(L $R/sfx_rain.mp3      31.0 1.00 12   0.6  0.05)"
 "$(L $R/sfx_quake.mp3     32.0 0.95 6    0.5  1.0)"
 "$(L $R/sfx_thunder.mp3   37.4 1.40 5.5  0.01 0.05)"
 "$(L $R/music_sunrise.mp3 44.0 0.70 16   0.8  2.0)"
 "$(L $R/sfx_morning.mp3   44.0 0.35 9    1.5  2.0)"
 "$(L $R/vo_$VO.mp3        44.8 1.70 0    0.02 0.3)"
 "$(L $R/sfx_drop.mp3      56.4 1.20 3    0.01 0.8)"
)
ins=(); fc=""; i=0
for l in "${LAYERS[@]}"; do IFS='|' read -r f s v t fi fo <<<"$l"
  ins+=(-i "$f")
  dur=$t; [ "$dur" = 0 ] && dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  st=$(python3 -c "print(max(0,$dur-$fo))")
  ms=$(python3 -c "print(int($s*1000))")
  fc+="[$i:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:$dur,afade=t=in:d=$fi,afade=t=out:st=$st:d=$fo,volume=$v,adelay=${ms}|${ms}[a$i];"
  i=$((i+1))
done
mix=""; for ((k=0;k<i;k++)); do mix+="[a$k]"; done
fc+="${mix}amix=inputs=$i:normalize=0:duration=longest,apad=whole_dur=60,atrim=0:60,alimiter=limit=0.89,loudnorm=I=-14:TP=-1.5:LRA=14[out]"
mkdir -p audio
ffmpeg -y -v error "${ins[@]}" -filter_complex "$fc" -map "[out]" -ar 48000 -c:a pcm_s24le audio/master_mix.wav
ffmpeg -y -v error -i audio/master_mix.wav -c:a aac -b:a 320k audio/master_mix.m4a
echo "OK: audio/master_mix.wav ($VO)"
