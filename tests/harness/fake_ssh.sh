#!/bin/bash
# Поддельный ssh для проверок: команды «на Move» выполняются локально, getfattr/setfattr/dbus-send — заглушки из fakebin.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec env PATH="$HERE/fakebin:$PATH" sh -c "$1"
