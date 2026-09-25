#!/usr/bin/env python3
"""Render the profile hero into assets/hero-{dark,light}.svg.

A prompt types `whoami` over a synthwave horizon: a striped sun and a
perspective grid rolling toward the viewer. Everything moves with CSS keyframes,
so it animates inside GitHub's <img> proxy with no script. Glyphs sit on a fixed
monospace grid (explicit x per character), so the cursor lands where the text is
whatever font the viewer ends up with.

Static art: run by hand after a design change, not by the Actions.
"""
import html
import os

from theme import MONO, THEMES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H = 800, 180
HORIZON = 118
CW = 13.2            # monospace advance at font-size 22
X0, Y1, Y2 = 28, 50, 86

PROMPT = "n30dyn4m1c@pom:~$ "
COMMAND = "whoami"
IDENTITY = "neo malesa · technologist · developer · trader · writer"
WHERE = "port moresby, png  09°26′S 147°11′E"

TYPE_START, TYPE_STEP = 0.6, 0.14   # seconds


def xs(start, text, advance):
    return " ".join(f"{start + i * advance:.1f}" for i in range(len(text)))


def grid(t):
    """Horizontal rungs that accelerate toward the viewer, plus rays from the vanishing point."""
    depth = H - HORIZON
    rungs, n, period = [], 8, 4.0
    for i in range(n):
        rungs.append(f'<line class="rung" x1="0" x2="{W}" y1="{HORIZON}" y2="{HORIZON}" '
                     f'style="animation-delay:-{i * period / n:.2f}s" />')
    rays = []
    vx = W / 2
    for k in range(-14, 15):
        bx = vx + k * 70
        rays.append(f'<line x1="{vx}" y1="{HORIZON}" x2="{bx}" y2="{H + 40}" />')
    css = (f"@keyframes roll{{from{{transform:translateY(0);opacity:0}}"
           f"15%{{opacity:.55}}to{{transform:translateY({depth}px);opacity:1}}}}\n"
           f".rung{{animation:roll {period}s cubic-bezier(.55,0,1,.45) infinite}}\n")
    body = (f'<g clip-path="url(#floor)" stroke="{t["cyan"]}" stroke-width="1" '
            f'opacity="{0.55 if t["glow"] else 0.45}">'
            f'<g opacity=".6">{"".join(rays)}</g>{"".join(rungs)}</g>'
            f'<line x1="0" x2="{W}" y1="{HORIZON}" y2="{HORIZON}" stroke="{t["magenta"]}" '
            f'stroke-width="1.5" opacity=".9" />')
    return body, css


def sun(t):
    cx, r = W - 104, 58
    # stripes widen toward the horizon, the classic sliced sun
    cuts = []
    y, gap = HORIZON - 30, 2.0
    while y < HORIZON:
        cuts.append(f'<rect x="{cx - r}" y="{y:.1f}" width="{2 * r}" height="{gap:.1f}" fill="#000" />')
        y += gap + 5
        gap += 1.2
    mask = (f'<mask id="slice"><rect width="{W}" height="{H}" fill="#fff" />{"".join(cuts)}</mask>')
    body = (f'<g clip-path="url(#sky)" mask="url(#slice)">'
            f'<circle cx="{cx}" cy="{HORIZON}" r="{r}" fill="url(#sunfill)" /></g>')
    defs = (f'<linearGradient id="sunfill" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{t["magenta"]}" stop-opacity=".95" />'
            f'<stop offset="1" stop-color="{t["magenta"]}" stop-opacity=".25" /></linearGradient>'
            + mask)
    return body, defs


def prompt(t):
    typed_x = X0 + len(PROMPT) * CW
    chars, css = [], []
    for i, ch in enumerate(COMMAND):
        chars.append(f'<text class="k k{i}" x="{typed_x + i * CW:.1f}" y="{Y1}">{html.escape(ch)}</text>')
        css.append(f".k{i}{{animation-delay:{TYPE_START + i * TYPE_STEP:.2f}s}}")
    done = TYPE_START + len(COMMAND) * TYPE_STEP

    # cursor hops one cell per keystroke, then parks after the command and blinks
    stops = [f"0%{{transform:translate(0,0)}}"]
    total = done + 0.5
    for i in range(1, len(COMMAND) + 1):
        pct = (TYPE_START + (i - 1) * TYPE_STEP) / total * 100
        stops.append(f"{pct:.2f}%{{transform:translate({i * CW:.1f}px,0)}}")
    stops.append(f"100%{{transform:translate({len(COMMAND) * CW:.1f}px,0)}}")
    cursor_x = typed_x
    css += [
        "@keyframes type{to{opacity:1}}",
        ".k{opacity:0;animation:type 0s linear forwards}",
        f"@keyframes hop{{{''.join(stops)}}}",
        f".cur{{animation:hop {total:.2f}s steps(1,end) forwards,blink 1.1s steps(1,end) {total:.2f}s infinite}}",
        "@keyframes blink{50%{opacity:0}}",
        "@keyframes rise{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}",
        f".id{{opacity:0;animation:rise .6s ease-out {done + 0.25:.2f}s forwards}}",
        f".where{{opacity:0;animation:rise .6s ease-out {done + 0.6:.2f}s forwards}}",
    ]
    glow = ' filter="url(#glow)"' if t["glow"] else ""
    body = (f'<g font-family="{MONO}" font-size="22"{glow}>'
            f'<text x="{xs(X0, PROMPT, CW)}" y="{Y1}" fill="{t["cyan"]}">{html.escape(PROMPT)}</text>'
            f'<g fill="{t["text"]}">{"".join(chars)}</g>'
            f'<rect class="cur" x="{cursor_x:.1f}" y="{Y1 - 18}" width="{CW - 2:.0f}" height="22" '
            f'fill="{t["magenta"]}" opacity=".85" /></g>'
            f'<text class="id" x="{X0}" y="{Y2}" font-family="{MONO}" font-size="17" '
            f'fill="{t["text"]}">{html.escape(IDENTITY)}</text>'
            f'<text class="where" x="{X0}" y="{Y2 + 22}" font-family="{MONO}" font-size="13" '
            f'fill="{t["muted"]}">{html.escape(WHERE)}</text>')
    return body, "\n".join(css)


def hero(name):
    t = THEMES[name]
    g_body, g_css = grid(t)
    s_body, s_defs = sun(t)
    p_body, p_css = prompt(t)
    reduced = ("@media(prefers-reduced-motion:reduce){.rung,.cur{animation:none}"
               ".k,.id,.where{animation:none;opacity:1}"
               f".cur{{transform:translate({len(COMMAND) * CW:.1f}px,0)}}}}")
    defs = (f'<clipPath id="sky"><rect width="{W}" height="{HORIZON}" /></clipPath>'
            f'<clipPath id="floor"><rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" /></clipPath>'
            '<filter id="glow" x="-5%" y="-40%" width="110%" height="180%">'
            '<feGaussianBlur stdDeviation="2.2" result="b" />'
            '<feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>'
            + s_defs)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">\n'
            f'<title id="t">n30dyn4m1c@pom:~$ whoami — neo malesa, technologist, developer, '
            f'trader, writer, port moresby</title>\n'
            f"<defs>{defs}</defs>\n"
            f"<style>\n{g_css}{p_css}\n{reduced}\n</style>\n"
            f'<rect width="{W}" height="{H}" rx="10" fill="{t["bg"]}" />\n'
            f"{s_body}\n{g_body}\n{p_body}\n"
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" '
            f'stroke="{t["grid"]}" />\n</svg>\n')


def main():
    for name in THEMES:
        path = os.path.join(ROOT, "assets", f"hero-{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(hero(name))
        print(f"wrote assets/hero-{name}.svg ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
