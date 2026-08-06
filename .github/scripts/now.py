#!/usr/bin/env python3
"""Refresh the live systems block of README.md (now playing/reading/exploring, weather, markets)."""
import datetime
import json
import os
import re
import time
import urllib.request

START, END = "<!-- NOW:START -->", "<!-- NOW:END -->"
README = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "README.md"))
NOW_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "now.json"))
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.goldprice.org/",
}

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


def pct_str(value):
    arrow = "\u25b2" if value >= 0 else "\u25bc"
    return f"{arrow} {abs(value):.2f}%"


def weather_line():
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=-9.4438&longitude=147.1803"
               "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto")
        cur = json.loads(fetch(url))["current"]
        desc = WMO.get(cur["weather_code"], "unknown")
        return (f"**weather · Port Moresby** — {round(cur['temperature_2m'])}°C · {desc} · "
                f"{cur['relative_humidity_2m']}% RH · wind {round(cur['wind_speed_10m'])} km/h")
    except Exception:
        return None


def markets_line():
    try:
        btc = json.loads(fetch(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        ))["bitcoin"]
        gold = json.loads(fetch("https://data-asg.goldprice.org/dbXRates/USD"))["items"][0]
        return (f"**markets** — XAUUSD ${gold['xauPrice']:,.2f} ({pct_str(gold['pcXau'])}) · "
                f"BTCUSD ${btc['usd']:,.0f} ({pct_str(btc['usd_24h_change'])})")
    except Exception:
        return None


def spotify_lines(cfg):
    if not cfg.get("enabled") or not cfg.get("uid"):
        return []
    url = ("https://spotify-github-profile.kittinanx.com/api/view?uid={uid}"
           "&cover_image=true&theme=default&show_offline=false&background_color=121212"
           "&interchange=true&bar_color=00ffcc&bar_color_cover=false").format(uid=cfg["uid"])
    return [f"**now playing**", "", f"[![spotify]({url})](https://open.spotify.com/user/{cfg['uid']})"]


def reading_line(cfg):
    title = cfg.get("title", "").replace("[", "\\[").replace("]", "\\]")
    author = cfg.get("author", "").replace("[", "\\[").replace("]", "\\]")
    source = f" · via {cfg['source']}" if cfg.get("source") else ""
    return f"**now reading** — *{title}* by {author}{source}"


def exploring_line(items):
    if not items:
        return "**now exploring** — *idle*"
    parts = " · ".join(f"`{p}`" for p in items)
    return f"**now exploring** — {parts}"


def old_line(current, key):
    for line in current.splitlines():
        if line.startswith(f"**{key}**"):
            return line
    return None


def build_block(cfg, current):
    tz = datetime.timezone(datetime.timedelta(hours=10))
    now = datetime.datetime.now(tz)
    ts = now.strftime("%d %b %Y · %H:%M") + " GMT+10"
    weather = weather_line() or old_line(current, "weather")
    markets = markets_line() or old_line(current, "markets")
    if weather is None:
        weather = "**weather · Port Moresby** — link down"
    if markets is None:
        markets = "**markets** — link down"
    lines = ["### \u258d live systems", "", f"_last sync: {ts}_", "",
             *spotify_lines(cfg.get("spotify", {})), "",
             reading_line(cfg.get("reading", {})), "",
             exploring_line(cfg.get("exploring", [])), "",
             weather, "", markets, "",
             "<!-- x feed: coming soon (rss.app bridge) -->"]
    return "\n".join(lines)


def main():
    with open(NOW_JSON, encoding="utf-8") as f:
        cfg = json.load(f)
    with open(README, encoding="utf-8") as f:
        text = f.read()
    a = text.index(START)
    b = text.index(END)
    current = text[a + len(START):b]
    block = build_block(cfg, current)
    if re.sub(r"_last sync:.*GMT\+10_", "", current).strip() == re.sub(r"_last sync:.*GMT\+10_", "", block).strip():
        print("no changes")
        return
    new_text = text[: a + len(START)] + "\n\n" + block + "\n\n" + text[b:]
    with open(README, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("README refreshed")


if __name__ == "__main__":
    main()
