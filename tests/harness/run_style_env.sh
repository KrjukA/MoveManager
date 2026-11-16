#!/bin/bash
# То же, что run_env.sh, плюс четыре проекта в группах Live/Archive на «компьютере».
HERE="$(cd "$(dirname "$0")" && pwd)"
bash "$HERE/run_env.sh"
B=http://127.0.0.1:8765
B2="/tmp/mmlib/BGDN LV Set 78/BGDN LV Set 78.ablbundle"
for k in 1 2 3 4; do curl -s -X POST --data-binary @"$B2" "$B/api/library-import?name=Demo%20$k.ablbundle&group=$([ $k -le 2 ] && echo Live || echo Archive)" >/dev/null; done
