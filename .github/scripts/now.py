#!/usr/bin/env python3
"""Refresh the live systems block of README.md (now playing/reading/exploring, weather, markets)."""
import datetime
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

START, END = "<!-- NOW:START -->", "<!-- NOW:END -->"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
README = os.path.join(ROOT, "README.md")
NOW_JSON = os.path.join(ROOT, "now.json")
HISTORY = os.path.join(ROOT, "data", "history.json")
MAX_POINTS = 336  # one week of half-hourly samples
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.goldprice.org/",
}

CYAN, MAGENTA, BASE = "00FFCC", "FF00CC", "0D0221"

WMO = {
    0: "clear sky", 1: "partly cloudy", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle", 56: "drizzle", 57: "drizzle",
    61: "rain", 63: "rain", 65: "rain", 66: "rain", 67: "rain",
    71: "snow", 73: "snow", 75: "snow", 77: "snow grains",
    80: "showers", 81: "showers", 82: "showers",
    85: "snow showers", 86: "snow showers",
    95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm",
}


def fetch(url, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def shield(text):
    """Escape a segment for a shields.io badge path."""
    return urllib.parse.quote(text.replace("-", "--").replace("_", "__"), safe="")


def row(rid, label, value):
    """One live-systems table row, tagged so a failed refresh can reuse the last good copy."""
    return (f"<!--row:{rid}-->\n<tr>\n"
            f'<td width="130"><code>{label}</code></td>\n'
            f"<td>{value}</td>\n"
            f"</tr>")


def old_row(current, rid):
    m = re.search(rf"<!--row:{rid}-->\n<tr>.*?</tr>", current, re.S)
    return m.group(0) if m else None


def weather_row():
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=-9.4438&longitude=147.1803"
               "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto")
        cur = json.loads(fetch(url))["current"]
        desc = WMO.get(cur["weather_code"], "unknown")
        value = (f"{round(cur['temperature_2m'])}&deg;C &middot; {desc} &middot; "
                 f"{cur['relative_humidity_2m']}% RH &middot; wind {round(cur['wind_speed_10m'])} km/h")
        return row("weather", "port moresby", value)
    except Exception:
        return None


def market_badge(symbol, price, pct):
    """Neon pill per instrument — cyan when the tape is up, magenta when it bleeds."""
    up = pct >= 0
    arrow = "▲" if up else "▼"
    message = f"{price} {arrow} {abs(pct):.2f}%"
    src = (f"https://img.shields.io/badge/{shield(symbol)}-{shield(message)}-"
           f"{CYAN if up else MAGENTA}?style=flat-square&labelColor={BASE}")
    return f'<img alt="{html.escape(symbol)} {html.escape(message)}" src="{html.escape(src)}" />'


def append_history(xau, btc):
    """Keep a rolling week of prices for the sparkline card. Never fatal."""
    try:
        with open(HISTORY, encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = []
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    if hist and hist[-1][0] == ts:
        return
    hist.append([ts, round(xau, 2), round(btc, 2)])
    try:
        os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(hist[-MAX_POINTS:], f, separators=(",", ":"))
    except OSError as e:
        print(f"history not written: {e}")


def markets_row():
    try:
        btc = json.loads(fetch(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        ))["bitcoin"]
        gold = json.loads(fetch("https://data-asg.goldprice.org/dbXRates/USD"))["items"][0]
        append_history(gold["xauPrice"], btc["usd"])
        value = "&nbsp;".join([
            market_badge("XAUUSD", f"${gold['xauPrice']:,.2f}", gold["pcXau"]),
            market_badge("BTCUSD", f"${btc['usd']:,.0f}", btc["usd_24h_change"]),
        ])
        return row("markets", "markets", value)
    except Exception:
        return None


def reading_row(cfg):
    title = html.escape(cfg.get("title", ""))
    author = html.escape(cfg.get("author", ""))
    source = f" &middot; {html.escape(cfg['source'])}" if cfg.get("source") else ""
    return row("reading", "reading", f"{title} &mdash; {author}{source}")


def exploring_row(items):
    if not items:
        return row("exploring", "exploring", "idle")
    chips = " &middot; ".join(html.escape(str(p)) for p in items)
    return row("exploring", "exploring", chips)


def build_block(cfg, current):
    tz = datetime.timezone(datetime.timedelta(hours=10))
    ts = datetime.datetime.now(tz).strftime("%d %b %Y &middot; %H:%M") + " GMT+10"
    rows = [
        reading_row(cfg.get("reading", {})),
        exploring_row(cfg.get("exploring", [])),
        weather_row() or old_row(current, "weather") or row("weather", "port moresby", "link down"),
        markets_row() or old_row(current, "markets") or row("markets", "markets", "link down"),
    ]
    parts = ["<table>", "\n".join(rows), "</table>", "",
              f"<sub>last sync &middot; {ts}</sub>"]
    return "\n".join(parts)


def strip_sync(text):
    return re.sub(r"<sub>last sync.*?GMT\+10</sub>", "", text)


def main():
    with open(NOW_JSON, encoding="utf-8") as f:
        cfg = json.load(f)
    with open(README, encoding="utf-8") as f:
        text = f.read()
    a = text.index(START)
    b = text.index(END)
    current = text[a + len(START):b]
    block = build_block(cfg, current)
    if strip_sync(current).strip() == strip_sync(block).strip():
        print("no changes")
        return
    new_text = text[: a + len(START)] + "\n\n" + block + "\n\n" + text[b:]
    with open(README, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("README refreshed")


if __name__ == "__main__":
    main()
