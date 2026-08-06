#!/usr/bin/env python3
"""Render the self-hosted profile cards into assets/: contribution pulse, language
bars, and the market tape drawn from the prices now.py collects.

The cards are committed to the repo, so the README never depends on a third-party
renderer being up. A failed refresh leaves the previous card in place.
"""
import argparse
import datetime
import html
import json
import os
import re
import urllib.error
import urllib.request

USER = "n30dyn4m1c"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(ROOT, "assets")
STAMP = "<!-- generated:"

BASE, CYAN, MAGENTA = "#0D0221", "#00FFCC", "#FF00CC"
TEXT, MUTED, GRID = "#C9D1D9", "#8B949E", "#1B0940"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
# level 0-4 heat, dark violet through to magenta
HEAT = ["#160A33", "#1F3D63", "#177C8E", "#00C6A8", "#00FFCC"]
LANG_COLORS = ["#00FFCC", "#FF00CC", "#00C6A8", "#C31FD1", "#177C8E", "#7B1FA2"]

API = "https://api.github.com"
UA = {
    "User-Agent": "n30dyn4m1c-profile-cards",
    "Accept": "application/vnd.github+json",
}


def token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def fetch(url, data=None, accept=None):
    headers = dict(UA)
    if accept:
        headers["Accept"] = accept
    if token() and url.startswith(API):  # never leak the token to the html fallback
        headers["Authorization"] = f"Bearer {token()}"
    body = json.dumps(data).encode() if data is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


# ---------------------------------------------------------------- data sources

GRAPHQL = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def calendar_via_graphql():
    payload = json.loads(fetch(f"{API}/graphql", {"query": GRAPHQL, "variables": {"login": USER}}))
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "graphql error"))
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return weeks, cal["totalContributions"]


def calendar_via_html():
    """Fallback: the public contribution graph, parsed for dates and per-day counts."""
    page = fetch(f"https://github.com/users/{USER}/contributions", accept="text/html")
    counts = {}
    for tip_for, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', page, re.S):
        m = re.search(r"([\d,]+|No)\s+contribution", text)
        if m:
            counts[tip_for] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
    days = []
    for cell in re.findall(r"<td[^>]*class=\"[^\"]*ContributionCalendar-day[^\"]*\"[^>]*>", page):
        date = re.search(r'data-date="([\d-]+)"', cell)
        if not date:
            continue
        cid = re.search(r'id="([^"]+)"', cell)
        level = re.search(r'data-level="(\d+)"', cell)
        count = counts.get(cid.group(1) if cid else "", None)
        if count is None:  # no tooltip parsed — approximate from the heat level
            count = int(level.group(1)) if level else 0
        days.append((date.group(1), count))
    if not days:
        raise RuntimeError("no contribution cells found")
    days.sort()
    weeks, week = [], []
    start = datetime.date.fromisoformat(days[0][0])
    pad = (start.weekday() + 1) % 7  # calendar columns start on Sunday
    week = [None] * pad
    for date, count in days:
        week.append((date, count))
        if len(week) == 7:
            weeks.append([d for d in week if d])
            week = []
    if week:
        weeks.append([d for d in week if d])
    return weeks, sum(c for _, c in days)


def calendar():
    if token():
        try:
            return calendar_via_graphql()
        except Exception as e:
            print(f"graphql calendar unavailable ({e}), falling back to html")
    return calendar_via_html()


def languages(limit=6, repo_cap=40):
    repos, page = [], 1
    while page <= 3:
        batch = json.loads(fetch(f"{API}/users/{USER}/repos?per_page=100&page={page}&type=owner"))
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    active = [r for r in repos if not r.get("fork") and not r.get("archived")]
    active.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    # Each repo contributes one unit, split by its own language mix. Summing raw
    # bytes instead would let a single vendored dependency own the whole card.
    weights = {}
    for repo in active[:repo_cap]:
        try:
            sizes = json.loads(fetch(repo["languages_url"]))
        except Exception:
            continue
        total = sum(sizes.values())
        for lang, size in sizes.items():
            weights[lang] = weights.get(lang, 0) + size / total
    if not weights:
        raise RuntimeError("no language bytes returned")
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    grand = sum(weights.values())
    stars = sum(r.get("stargazers_count", 0) for r in active)
    return [(name, w / grand * 100) for name, w in ranked], stars, len(active)


def profile():
    return json.loads(fetch(f"{API}/users/{USER}"))


# -------------------------------------------------------------------- rendering

def streaks(weeks):
    days = [d for week in weeks for d in week]
    days.sort()
    today = datetime.date.today()
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    current = 0
    for date, count in reversed(days):
        if datetime.date.fromisoformat(date) > today:
            continue
        if count:
            current += 1
        elif current or datetime.date.fromisoformat(date) != today:
            break
    best = max((c for _, c in days), default=0)
    return current, longest, best


def level(count):
    if count <= 0:
        return 0
    if count < 3:
        return 1
    if count < 6:
        return 2
    if count < 10:
        return 3
    return 4


def text_el(x, y, body, size=12, fill=TEXT, anchor="start", weight="400"):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(body)}</text>')


def frame(width, height, body, css):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">\n'
            f"{STAMP}{stamp} -->\n"
            f"<style>\n{css}\n</style>\n"
            f'<rect width="{width}" height="{height}" rx="10" fill="{BASE}" />\n'
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
            f'fill="none" stroke="{GRID}" />\n'
            f"{body}\n</svg>\n")


def pulse_card(weeks, total):
    cell, gap, pad = 12, 2, 20
    step = cell + gap
    cols = len(weeks)
    width = pad * 2 + cols * step - gap
    top = 56
    height = top + 7 * step - gap + 46
    current, longest, best = streaks(weeks)

    squares = []
    for col, week in enumerate(weeks):
        for day in week:
            date, count = day
            row = (datetime.date.fromisoformat(date).weekday() + 1) % 7
            x, y = pad + col * step, top + row * step
            squares.append(
                f'<rect class="c w{col}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{HEAT[level(count)]}"><title>{date} · {count}</title></rect>')

    legend_end = width - pad - 34
    legend_start = legend_end - (len(HEAT) * step - gap)
    labels = [
        text_el(pad, 30, "contributions", 13, CYAN),
        text_el(width - pad, 30,
                f"total {total} · streak {current} · best day {best} · longest {longest}",
                12, TEXT, anchor="end"),
        text_el(pad, height - 16, f"{weeks[0][0][0]} → {weeks[-1][-1][0]}", 11, MUTED),
        text_el(legend_start - 8, height - 16, "less", 11, MUTED, anchor="end"),
        text_el(width - pad, height - 16, "more", 11, MUTED, anchor="end"),
    ]
    legend = "".join(
        f'<rect x="{legend_start + i * step}" y="{height - 26}" width="{cell}" '
        f'height="{cell}" rx="2" fill="{shade}" />'
        for i, shade in enumerate(HEAT))

    # one delay class per column: the negative offsets turn a single keyframe into
    # a wave that travels left to right across the grid.
    delays = "\n".join(f".w{c}{{animation-delay:-{6 - (c * 0.09) % 6:.2f}s}}" for c in range(cols))
    css = ("@keyframes pulse{0%,88%{opacity:.72}94%{opacity:1}100%{opacity:.72}}\n"
           ".c{opacity:.72;animation:pulse 6s ease-in-out infinite}\n"
           "@media(prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}\n" + delays)
    return frame(width, height, "".join(squares) + "".join(labels) + legend, css)


def langs_card(ranked, stars, repo_count, followers):
    pad, row_h, bar_h = 20, 26, 10
    width = 780
    top = 56
    height = top + len(ranked) * row_h + 40
    bar_x = pad + 132
    bar_w = width - bar_x - pad - 62

    rows = []
    for i, (name, pct) in enumerate(ranked):
        y = top + i * row_h
        color = LANG_COLORS[i % len(LANG_COLORS)]
        filled = max(2, round(bar_w * pct / 100))
        rows.append(
            text_el(pad, y + bar_h, name, 12, TEXT)
            + f'<rect x="{bar_x}" y="{y + 2}" width="{bar_w}" height="{bar_h}" rx="5" fill="{GRID}" />'
            + f'<rect class="b b{i}" x="{bar_x}" y="{y + 2}" width="{filled}" height="{bar_h}" '
              f'rx="5" fill="{color}" style="--w:{filled}px" />'
            + text_el(width - pad, y + bar_h, f"{pct:.1f}%", 12, MUTED, anchor="end"))

    header = text_el(pad, 30, "languages", 13, MAGENTA)
    footer = text_el(pad, height - 16,
                     f"repos {repo_count} · stars {stars} · followers {followers}", 12, TEXT)
    delays = "\n".join(f".b{i}{{animation-delay:{i * 0.12:.2f}s}}" for i in range(len(ranked)))
    css = ("@keyframes grow{from{width:0}to{width:var(--w)}}\n"
           ".b{animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}\n"
           "@media(prefers-reduced-motion:reduce){.b{animation:none}}\n" + delays)
    return frame(width, height, header + "".join(rows) + footer, css)


def spark(points, x0, y0, w, h, color, index):
    """A sparkline that draws itself in, with a breathing dot left at the head."""
    lo, hi = min(points), max(points)
    span = (hi - lo) or 1.0
    step = w / (len(points) - 1)
    xy = [(x0 + i * step, y0 + h - (v - lo) / span * h) for i, v in enumerate(points)]
    length = sum(((xy[i + 1][0] - xy[i][0]) ** 2 + (xy[i + 1][1] - xy[i][1]) ** 2) ** 0.5
                 for i in range(len(xy) - 1))
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    hx, hy = xy[-1]
    return (f'<polyline class="l l{index}" points="{path}" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="--len:{length:.0f}" />'
            f'<circle class="ring r{index}" cx="{hx:.1f}" cy="{hy:.1f}" r="5.5" fill="none" '
            f'stroke="{color}" stroke-width="1.5" />'
            f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="2.5" fill="{color}" />')


def tape_card(history):
    if len(history) < 2:
        raise RuntimeError("not enough samples yet")
    width, height = 780, 168
    pad, gap = 20, 24
    panel = (width - pad * 2 - gap) / 2
    spark_y, spark_h = 74, 58

    series = [("XAUUSD", [row[1] for row in history], CYAN),
              ("BTCUSD", [row[2] for row in history], MAGENTA)]
    body = [text_el(pad, 30, "tape", 13, CYAN)]
    for i, (name, values, color) in enumerate(series):
        x0 = pad + i * (panel + gap)
        change = (values[-1] - values[0]) / values[0] * 100 if values[0] else 0.0
        arrow = "▲" if change >= 0 else "▼"
        body += [
            text_el(x0, 56, name, 12, TEXT),
            text_el(x0 + panel, 56, f"{values[-1]:,.2f}  {arrow} {abs(change):.2f}%", 12,
                    CYAN if change >= 0 else MAGENTA, anchor="end"),
            f'<line x1="{x0}" y1="{spark_y + spark_h + 8}" x2="{x0 + panel}" '
            f'y2="{spark_y + spark_h + 8}" stroke="{GRID}" stroke-width="1" />',
            spark(values, x0, spark_y, panel - 8, spark_h, color, i),
        ]

    hours = (datetime.datetime.strptime(history[-1][0], "%Y-%m-%dT%H:%MZ")
             - datetime.datetime.strptime(history[0][0], "%Y-%m-%dT%H:%MZ")).total_seconds() / 3600
    window = f"{hours:.0f}h" if hours < 48 else f"{hours / 24:.1f}d"
    body.append(text_el(pad, height - 16,
                        f"window {window} · {len(history)} samples · % over window",
                        11, MUTED))

    css = ("@keyframes draw{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}\n"
           "@keyframes blip{0%,100%{opacity:.15}50%{opacity:.9}}\n"
           ".l{stroke-dasharray:var(--len);stroke-dashoffset:var(--len);"
           "animation:draw 1.8s ease-out forwards}\n"
           ".ring{opacity:.15;animation:blip 2.4s ease-in-out infinite 1.8s}\n"
           ".l1{animation-delay:.25s}.r1{animation-delay:2.05s}\n"
           "@media(prefers-reduced-motion:reduce){.l{stroke-dasharray:none;stroke-dashoffset:0;"
           "animation:none}.ring{animation:none;opacity:.6}}")
    return frame(width, height, "".join(body), css)


# ------------------------------------------------------------------ entry point

def is_fresh(path, max_age_hours):
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(400)
    except OSError:
        return False
    m = re.search(rf"{re.escape(STAMP)}([0-9T:\-]+Z)", head)
    if not m:
        return False
    made = datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)
    age = datetime.datetime.now(datetime.timezone.utc) - made
    return age < datetime.timedelta(hours=max_age_hours)


def write(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.relpath(path, ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-hours", type=float, default=20.0,
                    help="skip the refresh while the existing cards are younger than this")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--fixture", help="render from a JSON fixture instead of the GitHub API")
    args = ap.parse_args()

    pulse_path = os.path.join(ASSETS, "pulse.svg")
    langs_path = os.path.join(ASSETS, "langs.svg")
    tape_path = os.path.join(ASSETS, "tape.svg")

    if args.fixture:
        data = json.load(open(args.fixture, encoding="utf-8"))
        weeks = [[(d[0], d[1]) for d in week] for week in data["weeks"]]
        write(pulse_path, pulse_card(weeks, data["total"]))
        write(langs_path, langs_card([tuple(x) for x in data["languages"]],
                                     data["stars"], data["repos"], data["followers"]))
        if data.get("history"):
            write(tape_path, tape_card(data["history"]))
        return

    # The tape reads prices now.py already collected, so it refreshes every run
    # rather than on the daily cadence the API-backed cards use.
    try:
        with open(os.path.join(ROOT, "data", "history.json"), encoding="utf-8") as f:
            write(tape_path, tape_card(json.load(f)))
    except Exception as e:
        print(f"tape kept (refresh failed: {e})")

    if not args.force and is_fresh(pulse_path, args.max_age_hours) and is_fresh(langs_path, args.max_age_hours):
        print("cards are fresh")
        return

    try:
        weeks, total = calendar()
        write(pulse_path, pulse_card(weeks, total))
    except Exception as e:
        print(f"contribution pulse kept (refresh failed: {e})")

    try:
        me = profile()
        ranked, stars, repo_count = languages()
        write(langs_path, langs_card(ranked, stars, repo_count, me.get("followers", 0)))
    except Exception as e:
        print(f"language card kept (refresh failed: {e})")


if __name__ == "__main__":
    main()
