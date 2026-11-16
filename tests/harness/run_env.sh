#!/bin/bash
# Поднимает программу против поддельного Move для проверок интерфейса (tests/ui/shot_*.py).
#   поддельный HTTP API Move — mock_move.py на :8799, программа — копия репозитория в /tmp/mm на :8765,
#   «девайс» — /tmp/fakesets, /tmp/fakeul (библиотека), /tmp/fakeschwung; «компьютер» — /root/mmpc.
# Нужен Linux (GNU find/stat, как BusyBox на Move) и запуск от root (проверки ждут папку /root/mmpc).
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
bash "$HERE/stop_env.sh"
rm -rf /tmp/fakesets /tmp/mm /tmp/mmlib /tmp/fakeschwung /tmp/fakeul; mkdir /tmp/fakesets /tmp/fakeschwung
bash "$HERE/seed_userlib.sh"
mkdir /tmp/mm && (cd "$REPO" && tar --exclude=.git --exclude=cache --exclude=backups --exclude=config.json --exclude='move_ssh_key*' --exclude=known_hosts -cf - .) | tar -xf - -C /tmp/mm
echo '{"move_url":"http://127.0.0.1:8799","library":"/tmp/mmlib","audio_format":"mp3"}' > /tmp/mm/config.json
(python3 "$HERE/mock_move.py" > /tmp/mock.log 2>&1 & echo $! > /tmp/mm-harness-mock.pid)
(cd /tmp/mm && PATH="$HERE/fakebin:$PATH" MOVE_SSH_CMD="$HERE/fake_ssh.sh" MOVE_SETS_DIR=/tmp/fakesets MOVE_SCHWUNG_DIR=/tmp/fakeschwung \
   MOVE_USERLIB_DIR=/tmp/fakeul MOVE_MANAGER_NO_BROWSER=1 python3 /tmp/mm/app.py > /tmp/mm.log 2>&1 & echo $! > /tmp/mm-harness-app.pid)
sleep 1.5
B=http://127.0.0.1:8765
curl -s -X POST $B/api/auth/code -H 'Content-Type: application/json' -d '{"code":"123456"}' >/dev/null
curl -s -X POST $B/api/ssh/setup >/dev/null; sleep 1
ID=$(curl -s $B/api/move/sets | python3 -c "import json,sys; print([s for s in json.load(sys.stdin)['sets'] if s['name'].startswith('BGDN')][0]['id'])")
curl -s -X POST $B/api/move/sets/$ID/pull -H 'Content-Type: application/json' -d '{"audio":false}' >/dev/null; sleep 1
