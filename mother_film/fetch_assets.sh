#!/usr/bin/env bash
# Скачивает бесплатные исходники (CC0), нужные для 3D-версии: базовая модель, риг и морф-таргеты MakeHuman.
set -euo pipefail
D=${1:-/home/user/assets}
mkdir -p "$D"; cd "$D"
if [ ! -d mhrepo ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/makehumancommunity/makehuman mhrepo
  (cd mhrepo && git sparse-checkout set makehuman/data/targets makehuman/data/3dobjs makehuman/data/rigs makehuman/data/eyes)
fi
echo "MH_DATA=$D/mhrepo/makehuman/data"
