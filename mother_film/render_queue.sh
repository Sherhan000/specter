#!/usr/bin/env bash
# Очередь рендера: берёт шоты из render_queue.txt по порядку, рендерит (резюмируемо), кодирует clips/SXX.mp4
# и сразу коммитит и пушит готовый клип. Запуск: setsid nohup ./render_queue.sh > /home/user/render/queue.log 2>&1 &
cd "$(dirname "$0")"
Q=render_queue.txt; touch $Q
BR=$(git rev-parse --abbrev-ref HEAD)
while true; do
  next=""
  for s in $(cat $Q); do [ -s clips/$s.mp4 ] && [ ! -f /home/user/render/$s.redo ] || { next=$s; break; }; done
  if [ -z "$next" ]; then sleep 20; continue; fi
  rm -f /home/user/render/$next.redo
  echo "=== $(date +%H:%M:%S) start $next"
  if nice -n 10 python3 blender/render.py $next 2>&1 | grep --line-buffered -E "^\[|Error|Traceback|error"; then :; fi
  if [ -s clips/$next.mp4 ]; then
    for i in 1 2 3 4 5; do
      git add clips/$next.mp4 && git commit -qm "Рендер шота $next

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QzsQUsexmE5szY5rxQDFfp" -- clips/$next.mp4 && break; sleep 5; done
    for i in 2 4 8 16 32; do git push -u origin $BR 2>&1 | tail -1 && break; sleep $i; done
    echo "=== $(date +%H:%M:%S) done $next (pushed)"
  else
    echo "=== $(date +%H:%M:%S) FAILED $next"; sleep 60
  fi
done
