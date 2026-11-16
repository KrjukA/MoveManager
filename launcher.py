"""Запуск собранного приложения KRJUK Move Manager: сервер в фоне, браузер и маленькое окно «работает · Open · Quit».
Второй запуск не поднимает второй сервер — просто открывает браузер с уже работающим."""
import os
import socket
import threading
import webbrowser

import app


def port_busy(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


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
    tk.Label(root, text="Move Manager is running", font=("Helvetica", 14, "bold")).pack(padx=24, pady=(10, 2))
    tk.Label(root, text=f"build {app.BUILD} · {url}", fg="#777").pack(padx=24)
    tk.Label(root, text="Keep this window open while you use the manager.", fg="#777").pack(padx=24, pady=(6, 0))
    row = tk.Frame(root); row.pack(pady=16)
    tk.Button(row, text="Open in browser", width=16, command=lambda: webbrowser.open(url)).pack(side="left", padx=6)
    def quit_():
        quit_cb(); root.destroy()
    tk.Button(row, text="Quit", width=10, command=quit_).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", quit_)
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
