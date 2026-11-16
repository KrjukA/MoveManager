#!/bin/bash
# Останавливает поддельный Move и программу, запущенные run_env.sh (по номерам процессов, без pkill по имени).
for f in /tmp/mm-harness-app.pid /tmp/mm-harness-mock.pid; do
  [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null; rm -f "$f"
done
sleep 0.3
exit 0
