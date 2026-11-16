#!/bin/bash
# Все проверки интерфейса, каждая на свежем окружении. Нужен Playwright: pip install playwright && playwright install chromium
# Запуск: bash tests/harness/run_ui_checks.sh [shot_cmd shot_ui50 ...]   — без аргументов прогоняет все tests/ui/shot_*.py
HERE="$(cd "$(dirname "$0")" && pwd)"; UI="$(cd "$HERE/../ui" && pwd)"
LIST="$*"; [ -z "$LIST" ] && LIST=$(cd "$UI" && ls shot_*.py shot3.py 2>/dev/null | sed 's/\.py$//' | sort -u)
fail=0
for f in $LIST; do
  bash "$HERE/run_style_env.sh" > /tmp/env_$f.log 2>&1
  (cd "$UI" && timeout 300 python3 "$f.py" > /tmp/$f.log 2>&1); rc=$?
  n=$(grep -c FAIL /tmp/$f.log); echo "$f exit=$rc fails=$n"
  [ $rc -ne 0 ] && fail=1
done
bash "$HERE/stop_env.sh"
exit $fail
