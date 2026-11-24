"""Запуск собранного приложения KRJUK Move Manager: сервер в фоне, браузер и маленькое окно «работает · Open · Quit».
Второй запуск не поднимает второй сервер — просто открывает браузер с уже работающим."""
import os
import socket
import subprocess
import sys
import threading
import webbrowser

import app


TEXTS = {
    "en": {"running": "Move Manager is running", "keep": "Keep this window open while you use the manager.",
           "open": "Open in browser", "quit": "Quit",
           "busy": "An operation is still running: {what}.\n\nIf you quit now, it will be interrupted. Quit anyway?"},
    "ru": {"running": "Move Manager работает", "keep": "Не закрывайте это окно, пока пользуетесь программой.",
           "open": "Открыть в браузере", "quit": "Выйти",
           "busy": "Ещё идёт операция: {what}.\n\nЕсли выйти сейчас, она прервётся. Выйти всё равно?"},
}


def _mac_langs():
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, timeout=3).stdout
        return [x.strip(' "(),\n') for x in out.decode("utf-8", "replace").split(",") if x.strip(' "(),\n')]
    except Exception:  # noqa: BLE001
        return []


def _win_lang():
    try:
        import ctypes
        return ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except Exception:  # noqa: BLE001
        return 0


def system_lang(env=None, platform=None, mac_langs=_mac_langs, win_lang=_win_lang):
    """Язык системы для окна запуска: «ru» или «en». Из Finder/Проводника переменной LANG обычно нет."""
    env = os.environ if env is None else env
    platform = platform or sys.platform
    if platform == "darwin":
        langs = mac_langs()
        if langs:
            return "ru" if langs[0].lower().startswith("ru") else "en"
    if platform.startswith("win"):
        return "ru" if (win_lang() & 0x3FF) == 0x19 else "en"
    val = env.get("LC_ALL") or env.get("LC_MESSAGES") or env.get("LANG") or ""
    return "ru" if val.lower().startswith("ru") else "en"


def port_busy(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def may_quit(ask, lang):
    """Можно ли выходить: операций нет — да; есть (копирование, перенос…) — спросить ask(заголовок, текст)."""
    busy = app.running_jobs()
    if not busy:
        return True
    tx = TEXTS[lang]
    return bool(ask(tx["quit"], tx["busy"].format(what=", ".join(dict.fromkeys(busy)))))


def _window(url, quit_cb):
    """Окно управления на tkinter. Без tkinter или без экрана — None, и программа работает без окна."""
    try:
        import tkinter as tk
        root = tk.Tk()
    except Exception:  # noqa: BLE001
        return None
    root.title(app.APP_NAME)
    root.resizable(False, False)
    try:                                           # значок окна и логотип; без картинок окно всё равно работает
        root.iconphoto(True, tk.PhotoImage(file=str(app.STATIC_DIR / "favicon.png")))
        logo = tk.PhotoImage(file=str(app.STATIC_DIR / "logo.png")).subsample(2)
        tk.Label(root, image=logo).pack(padx=24, pady=(18, 0))
        root._logo = logo                          # иначе картинку соберёт сборщик мусора
    except Exception:  # noqa: BLE001
        pass
    lang = system_lang()
    tx = TEXTS[lang]
    tk.Label(root, text=tx["running"], font=("Helvetica", 14, "bold")).pack(padx=24, pady=(10, 2))
    tk.Label(root, text=f"v{app.VERSION} · {url}", fg="#777").pack(padx=24)
    tk.Label(root, text=tx["keep"], fg="#777").pack(padx=24, pady=(6, 0))
    row = tk.Frame(root); row.pack(pady=16)
    tk.Button(row, text=tx["open"], width=18, command=lambda: webbrowser.open(url)).pack(side="left", padx=6)
    def quit_():
        from tkinter import messagebox
        if not may_quit(lambda t, m: messagebox.askyesno(t, m, icon="warning", parent=root), lang):
            return
        quit_cb(); root.destroy()
    tk.Button(row, text=tx["quit"], width=10, command=quit_).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", quit_)
    try:                                           # Mac: ⌘Q и «Завершить» в Dock — тоже через проверку
        root.createcommand("::tk::mac::Quit", quit_)
        # повторный двойной щелчок по приложению в Finder (или по значку в Dock): macOS не запускает вторую копию,
        # а шлёт работающей «открыть снова» — открываем браузер (сборка 63)
        root.createcommand("::tk::mac::ReopenApplication", lambda *a: webbrowser.open(url))
    except Exception:  # noqa: BLE001
        pass
    return root


def main(stop=None):
    url = f"http://127.0.0.1:{app.PORT}"
    if port_busy(app.PORT):                       # уже работает — открыть его
        webbrowser.open(url)
        return
    srv, url = app.make_server()
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    if not os.environ.get("MOVE_MANAGER_NO_BROWSER"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    win = None if os.environ.get("MOVE_MANAGER_NO_WINDOW") else _window(url, srv.shutdown)
    try:
        if win is not None:
            win.mainloop()
        else:
            print(f"{app.APP_NAME} (build {app.BUILD}) running: {url}\nStop with Ctrl+C")
            (stop or threading.Event()).wait()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()
