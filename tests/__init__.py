"""Настройка окружения тестов.

Тесты подменяют SSH и выполняют команды для Move (BusyBox: GNU-подобные find/stat/tar) прямо на этом компьютере.
На Mac свои BSD-версии этих утилит, поэтому, если через Homebrew установлены coreutils, findutils и gnu-tar,
их GNU-версии ставятся первыми в PATH. Временная папка — по настоящему пути (на Mac /var — ссылка на /private/var).
Поставить один раз:  brew install coreutils findutils gnu-tar
"""
import os
import sys
import tempfile

if sys.platform == "darwin":
    gnubins = [f"{p}/libexec/gnubin" for p in ("/opt/homebrew/opt/gnu-tar", "/opt/homebrew/opt/coreutils",
                                                "/opt/homebrew/opt/findutils", "/usr/local/opt/gnu-tar",
                                                "/usr/local/opt/coreutils", "/usr/local/opt/findutils")]
    have = [d for d in gnubins if os.path.isdir(d)]
    path = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join(have + [p for p in path if p not in have])
    real_tmp = os.path.realpath(tempfile.gettempdir())
    os.environ["TMPDIR"] = real_tmp
    tempfile.tempdir = real_tmp
