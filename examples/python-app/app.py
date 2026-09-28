"""Example app for FM ActionLink.

Receives the plugin's events on http://127.0.0.1:8767/fm-events and shows web pages over
the game in borderless windows (pywebview):

  window.open / window.pin / window.close  -> a window next to the button
  panel.show / panel.hide                   -> a window glued over the embedded panel
  button.click ("sendToApp")                -> a normal window, brought to the front

Replace the pages in WINDOWS, PANELS and APP_PAGE with your own. Requires: pip install pywebview
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

# Physical pixels, like the game. Must run before any window exists.
ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

import webview  # noqa: E402

PORT = 8767
BASE = f"http://127.0.0.1:{PORT}"
PAGES = Path(__file__).resolve().parent / "pages"

# buttonId -> page and window size (physical pixels)
WINDOWS = {
    "quick-preview": {"page": "/pages/preview.html", "size": (380, 250)},
    "model-3d": {"page": "/pages/model3d.html", "size": (560, 380)},
}
# panelId -> page
PANELS = {
    "embedded-3d": "/pages/model3d.html?embedded=1",
}
APP_PAGE = "/pages/player.html"
GAP = 6

user32 = ctypes.windll.user32
user32.FindWindowW.restype = wt.HWND
user32.GetForegroundWindow.restype = wt.HWND
user32.MonitorFromPoint.restype = wt.HMONITOR
HWND_TOPMOST = wt.HWND(-1)
SWP_NOACTIVATE = 0x10
SW_HIDE, SW_SHOWNOACTIVATE = 0, 4

lock = threading.Lock()
overlays = {}  # key -> {"window", "hwnd", "title", "rect", "visible"}
game_pid = None


def log(message):
    print(f"[app] {message}", flush=True)


def page_url(page, event):
    player = event.get("playerId")
    joiner = "&" if "?" in page else "?"
    return f"{BASE}{page}{joiner}playerId={quote(str(player or ''))}&mode={quote(event.get('mode') or '')}"


def work_area(x, y):
    class MonitorInfo(ctypes.Structure):
        _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]
    info = MonitorInfo(cbSize=ctypes.sizeof(MonitorInfo))
    user32.GetMonitorInfoW(user32.MonitorFromPoint(wt.POINT(x, y), 2), ctypes.byref(info))
    r = info.rcWork
    return r.left, r.top, r.right, r.bottom


def next_to(anchor, size):
    """Below the button, or above it when there is no room; kept inside the monitor."""
    w, h = size
    left, top, right, bottom = work_area(anchor["x"], anchor["y"])
    x = min(max(anchor["x"], left), right - w)
    y = anchor["y"] + anchor["height"] + GAP
    if y + h > bottom:
        y = max(anchor["y"] - GAP - h, top)
    return x, y, w, h


def place(key):
    """Moves the overlay to its rect, in physical pixels (pywebview's own x/y are logical)."""
    o = overlays.get(key)
    if o and o["hwnd"] and o["rect"]:
        x, y, w, h = o["rect"]
        user32.SetWindowPos(o["hwnd"], HWND_TOPMOST, x, y, w, h, SWP_NOACTIVATE)


def show_overlay(key, url, rect):
    """Creates the borderless window the first time, then only moves it (the page stays loaded)."""
    with lock:
        o = overlays.get(key)
        if o and o["window"] == "creating":
            o.update(rect=rect, visible=True, close_when_ready=False)
            return
        if o and o["window"] is not None:
            same_page = o["url"] == url
            o.update(rect=rect, visible=True, url=url)
            if not o["hwnd"]:
                o["hwnd"] = user32.FindWindowW(None, o["title"])
            place(key)
            if not same_page:
                o["window"].load_url(url)
            return
        title = f"FM26 overlay {key}"
        overlays[key] = {"window": "creating", "hwnd": None, "title": title, "rect": rect, "visible": True, "url": url}
    x, y, w, h = rect
    window = webview.create_window(title, url, x=x, y=y, width=w, height=h, frameless=True, easy_drag=False,
                                   on_top=True, resizable=False, focus=False, background_color="#10151C")

    def shown():
        with lock:
            overlays[key]["hwnd"] = user32.FindWindowW(None, title)
            place(key)
    window.events.shown += shown
    with lock:
        overlays[key]["window"] = window
        closed_meanwhile = overlays[key].get("close_when_ready")
    if closed_meanwhile:
        hide_overlay(key, destroy=True)


def hide_overlay(key, destroy=False):
    with lock:
        o = overlays.get(key)
        if not o:
            return
        o["visible"] = False
        if o["window"] == "creating":
            # the mouse left before the window finished opening
            o["close_when_ready"] = destroy
            return
        if destroy:
            window = o["window"]
            overlays.pop(key)
    if destroy:
        try:
            window.destroy()
        except Exception:
            pass


def watch_foreground():
    """Overlays show only while the game (or this app) is in front: otherwise an always-on-top
    window would float over every other program."""
    own_pid = os.getpid()
    while True:
        time.sleep(0.12)
        owner = wt.DWORD()
        user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(owner))
        in_front = owner.value in (game_pid, own_pid)
        with lock:
            items = [(o["hwnd"], o["visible"]) for o in overlays.values() if o["hwnd"]]
        for hwnd, wanted in items:
            show = wanted and in_front
            if show != bool(user32.IsWindowVisible(hwnd)):
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE if show else SW_HIDE)


def open_app_window(event):
    """What a "sendToApp" button would do in a real app: show that player, in front."""
    url = page_url(APP_PAGE, event)
    window = webview.create_window("Example app", url, width=720, height=480)
    window.events.shown += lambda: window.restore()


def handle(event):
    global game_pid
    game_pid = event.get("gamePid") or game_pid
    kind = event.get("event")
    if kind == "button.click":
        open_app_window(event)
    elif kind == "window.open":
        spec = WINDOWS.get(event.get("buttonId"))
        if spec:
            key = "window:" + event["buttonId"]
            show_overlay(key, page_url(spec["page"], event), next_to(event["anchor"], spec["size"]))
    elif kind == "window.close":
        hide_overlay("window:" + event.get("buttonId", ""), destroy=True)
    elif kind == "panel.show":
        page = PANELS.get(event.get("panelId"))
        if page:
            r = event["rect"]
            show_overlay("panel:" + event["panelId"], page_url(page, event), (r["x"], r["y"], r["width"], r["height"]))
    elif kind == "panel.hide":
        hide_overlay("panel:" + event.get("panelId", ""))
    # "window.pin" needs nothing here: the window stays until "window.close"


class Server(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/fm-events":
            self.send_response(404); self.end_headers(); return
        try:
            event = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except (ValueError, json.JSONDecodeError):
            self.send_response(400); self.end_headers(); return
        if event.get("event") not in ("panel.show",):  # panel.show repeats every 2 s
            log(json.dumps(event))
        # answer at once: the plugin sends the next event only after this one
        self.send_response(204); self.end_headers()
        threading.Thread(target=handle, args=(event,), daemon=True).start()

    def do_GET(self):
        path = self.path.split("?")[0]
        file = (PAGES / path.removeprefix("/pages/")).resolve()
        if not path.startswith("/pages/") or PAGES not in file.parents or not file.is_file():
            self.send_response(404); self.end_headers(); return
        body = file.read_bytes()
        kinds = {".html": "text/html; charset=utf-8", ".glb": "model/gltf-binary", ".png": "image/png"}
        self.send_response(200)
        self.send_header("Content-Type", kinds.get(file.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve():
    log(f"listening on {BASE}/fm-events")
    threading.Thread(target=watch_foreground, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Server).serve_forever()


if __name__ == "__main__":
    # pywebview needs one window to start its loop; this one stays hidden
    webview.create_window("FM26 example app (hidden)", html="<html></html>", hidden=True)
    webview.start(func=lambda: threading.Thread(target=serve, daemon=True).start())
