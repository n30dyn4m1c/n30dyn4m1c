#!/usr/bin/env python3
"""Render the profile hero into assets/hero-{dark,light}.svg.

Both variants open with a prompt typing `whoami`.
  dark   synthwave: a sliced sun and a perspective grid rolling toward the viewer
  light  the N30 PNG banner and the bird of paradise, in PNG flag colours
The ASCII art lives verbatim in scripts/art/.

Everything moves with CSS keyframes, so it animates inside GitHub's <img> proxy
with no script. Glyphs sit on a fixed monospace grid (explicit x per character),
so the art and the cursor line up whatever font the viewer ends up with.

Static art: run by hand after a design change, not by the Actions.
"""
import html
import os

from theme import MONO, THEMES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art")
W = 800

PROMPT = "n30dyn4m1c@pom:~$ "
COMMAND = "whoami"
TYPE_START, TYPE_STEP = 0.6, 0.14   # seconds
TYPED = TYPE_START + len(COMMAND) * TYPE_STEP

GLOW = ('<filter id="glow" x="-5%" y="-40%" width="110%" height="180%">'
        '<feGaussianBlur stdDeviation="2.2" result="b" />'
        '<feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>')


def xs(start, text, advance):
    return " ".join(f"{start + i * advance:.1f}" for i in range(len(text)))


def art(name):
    with open(os.path.join(ART, name), encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def typed_prompt(t, x0, y, size, cw):
    """`user@host:~$ ` then `whoami` keyed in one glyph at a time, cursor hopping behind."""
    typed_x = x0 + len(PROMPT) * cw
    chars, css = [], []
    for i, ch in enumerate(COMMAND):
        chars.append(f'<text class="k k{i}" x="{typed_x + i * cw:.1f}" y="{y}">{html.escape(ch)}</text>')
        css.append(f".k{i}{{animation-delay:{TYPE_START + i * TYPE_STEP:.2f}s}}")

    # cursor hops one cell per keystroke, then parks after the command and blinks
    stops = ["0%{transform:translate(0,0)}"]
    total = TYPED + 0.5
    for i in range(1, len(COMMAND) + 1):
        pct = (TYPE_START + (i - 1) * TYPE_STEP) / total * 100
        stops.append(f"{pct:.2f}%{{transform:translate({i * cw:.1f}px,0)}}")
    stops.append(f"100%{{transform:translate({len(COMMAND) * cw:.1f}px,0)}}")
    css += [
        "@keyframes type{to{opacity:1}}",
        ".k{opacity:0;animation:type 0s linear forwards}",
        f"@keyframes hop{{{''.join(stops)}}}",
        f".cur{{animation:hop {total:.2f}s steps(1,end) forwards,blink 1.1s steps(1,end) {total:.2f}s infinite}}",
        "@keyframes blink{50%{opacity:0}}",
        "@keyframes rise{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}",
        "@media(prefers-reduced-motion:reduce){.k{animation:none;opacity:1}"
        f".cur{{animation:none;transform:translate({len(COMMAND) * cw:.1f}px,0)}}}}",
    ]
    glow = ' filter="url(#glow)"' if t["glow"] else ""
    body = (f'<g font-family="{MONO}" font-size="{size}"{glow}>'
            f'<text x="{xs(x0, PROMPT, cw)}" y="{y}" fill="{t["accent"]}">{html.escape(PROMPT)}</text>'
            f'<g fill="{t["text"]}">{"".join(chars)}</g>'
            f'<rect class="cur" x="{typed_x:.1f}" y="{y - size * 0.82:.1f}" width="{cw - 2:.0f}" '
            f'height="{size}" fill="{t["hot"]}" opacity=".85" /></g>')
    return body, "\n".join(css)


def reveal(cls, delay):
    """Fade-and-rise in after `delay` seconds; shown at once under reduced motion."""
    return (f".{cls}{{opacity:0;animation:rise .6s ease-out {delay:.2f}s forwards}}\n"
            f"@media(prefers-reduced-motion:reduce){{.{cls}{{animation:none;opacity:1}}}}")


def svg(t, height, title, defs, css, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
            f'viewBox="0 0 {W} {height}" role="img" aria-labelledby="t">\n'
            f'<title id="t">{html.escape(title)}</title>\n'
            f"<defs>{defs}</defs>\n"
            f"<style>\n{css}\n</style>\n"
            f'<rect width="{W}" height="{height}" rx="10" fill="{t["bg"]}" />\n'
            f"{body}\n"
            f'<rect x=".5" y=".5" width="{W - 1}" height="{height - 1}" rx="10" fill="none" '
            f'stroke="{t["grid"]}" />\n</svg>\n')


# ---------------------------------------------------------------- dark: synthwave

H_DARK, HORIZON = 180, 118


def grid(t):
    """Horizontal rungs that accelerate toward the viewer, plus rays from the vanishing point."""
    depth = H_DARK - HORIZON
    rungs, n, period = [], 8, 4.0
    for i in range(n):
        rungs.append(f'<line class="rung" x1="0" x2="{W}" y1="{HORIZON}" y2="{HORIZON}" '
                     f'style="animation-delay:-{i * period / n:.2f}s" />')
    rays = []
    vx = W / 2
    for k in range(-14, 15):
        bx = vx + k * 70
        rays.append(f'<line x1="{vx}" y1="{HORIZON}" x2="{bx}" y2="{H_DARK + 40}" />')
    css = (f"@keyframes roll{{from{{transform:translateY(0);opacity:0}}"
           f"15%{{opacity:.55}}to{{transform:translateY({depth}px);opacity:1}}}}\n"
           f".rung{{animation:roll {period}s cubic-bezier(.55,0,1,.45) infinite}}\n"
           "@media(prefers-reduced-motion:reduce){.rung{animation:none}}")
    body = (f'<g clip-path="url(#floor)" stroke="{t["accent"]}" stroke-width="1" opacity=".55">'
            f'<g opacity=".6">{"".join(rays)}</g>{"".join(rungs)}</g>'
            f'<line x1="0" x2="{W}" y1="{HORIZON}" y2="{HORIZON}" stroke="{t["hot"]}" '
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
    body = (f'<g clip-path="url(#sky)" mask="url(#slice)">'
            f'<circle cx="{cx}" cy="{HORIZON}" r="{r}" fill="url(#sunfill)" /></g>')
    defs = (f'<linearGradient id="sunfill" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{t["hot"]}" stop-opacity=".95" />'
            f'<stop offset="1" stop-color="{t["hot"]}" stop-opacity=".25" /></linearGradient>'
            f'<mask id="slice"><rect width="{W}" height="{H_DARK}" fill="#fff" />{"".join(cuts)}</mask>')
    return body, defs


def synthwave(t):
    x0, y1, y2 = 28, 50, 86
    g_body, g_css = grid(t)
    s_body, s_defs = sun(t)
    p_body, p_css = typed_prompt(t, x0, y1, 22, 13.2)
    body = (s_body + g_body + p_body
            + f'<text class="id" x="{x0}" y="{y2}" font-family="{MONO}" font-size="17" '
              f'fill="{t["text"]}">neo malesa · technologist · developer · trader · writer</text>'
            + f'<text class="where" x="{x0}" y="{y2 + 22}" font-family="{MONO}" font-size="13" '
              f'fill="{t["muted"]}">port moresby, png  09°26′S 147°11′E</text>')
    defs = (f'<clipPath id="sky"><rect width="{W}" height="{HORIZON}" /></clipPath>'
            f'<clipPath id="floor"><rect y="{HORIZON}" width="{W}" height="{H_DARK - HORIZON}" /></clipPath>'
            + GLOW + s_defs)
    css = "\n".join([g_css, p_css, reveal("id", TYPED + 0.25), reveal("where", TYPED + 0.6)])
    return svg(t, H_DARK, "n30dyn4m1c@pom:~$ whoami — neo malesa, technologist, developer, "
                          "trader, writer, port moresby", defs, css, body)


# ------------------------------------------------------------ light: flag and bird

H_LIGHT = 318

# bird glyph classes: the solid strokes carry the plumage gradient, the
# punctuation fades back into the paper like the dither it is
BIRD_BODY = set("#*=+")
BIRD_MID = set(":-")


def ascii_block(lines, x0, y0, cw, lh, row_class, fill_for):
    """Each line on a fixed grid; runs of one colour share a tspan to keep the file small."""
    out = []
    for r, line in enumerate(lines):
        runs, cur, buf = [], None, ""
        for ch in line:
            f = fill_for(ch)
            if f != cur and buf:
                runs.append((cur, buf))
                buf = ""
            cur = f
            buf += ch
        if buf:
            runs.append((cur, buf))
        spans = "".join(f'<tspan fill="{f}">{html.escape(s)}</tspan>' if f else html.escape(s)
                        for f, s in runs)
        out.append(f'<text class="{row_class} {row_class}{r}" xml:space="preserve" '
                   f'x="{xs(x0, line, cw)}" y="{y0 + r * lh:.1f}">{spans}</text>')
    return "".join(out)


def flag(t):
    banner, bird = art("banner.txt"), art("bird.txt")
    x0 = 28

    # left: prompt, then the banner as whoami's output, then who and where
    p_body, p_css = typed_prompt(t, x0, 46, 18, 10.8)
    b_cw, b_lh, b_y = 6.2, 12.4, 84
    banner_svg = ascii_block(banner, x0, b_y, b_cw, b_lh, "br",
                             lambda ch: None if ch in "█" else t["accent"])
    id_y = b_y + len(banner) * b_lh + 36
    who = (f'<text class="id" x="{x0}" y="{id_y:.0f}" font-family="{MONO}" font-size="15" '
           f'fill="{t["text"]}">neo malesa</text>'
           f'<text class="id" x="{x0}" y="{id_y + 22:.0f}" font-family="{MONO}" font-size="13" '
           f'fill="{t["text"]}">technologist · developer · trader · writer</text>'
           f'<text class="where" x="{x0}" y="{id_y + 44:.0f}" font-family="{MONO}" font-size="12" '
           f'fill="{t["muted"]}">port moresby, png  09°26′S 147°11′E</text>')

    # right: the bird of paradise, drawn in row by row while the command is typed
    k_cw, k_lh = 5.3, 9.4
    k_x = W - 14 - len(bird[0]) * k_cw
    k_y = (H_LIGHT - len(bird) * k_lh) / 2 + 7

    def plume(ch):
        if ch in BIRD_BODY:
            return "url(#plume)"
        if ch in BIRD_MID:
            return t["muted"]
        return None  # '.' and space take the faint group fill

    bird_svg = (f'<g font-family="{MONO}" font-size="9" fill="{t["grid"]}">'
                + ascii_block(bird, k_x, k_y, k_cw, k_lh, "bd", plume) + "</g>")

    defs = (f'<linearGradient id="plume" gradientUnits="userSpaceOnUse" '
            f'x1="0" y1="{k_y:.0f}" x2="0" y2="{k_y + len(bird) * k_lh:.0f}">'
            f'<stop offset=".15" stop-color="{t["hot"]}" />'
            f'<stop offset=".6" stop-color="{t["hot"]}" />'
            f'<stop offset=".9" stop-color="{t["gold"]}" /></linearGradient>')

    rows = [".bd{opacity:0;animation:ink .5s ease-out forwards}",
            "@keyframes ink{to{opacity:1}}"]
    rows += [f".bd{r}{{animation-delay:{0.1 + r * 0.045:.2f}s}}" for r in range(len(bird))]
    # the banner lands as one piece: fading its six overlapping rows one by one
    # leaves a row unpainted in Chrome
    rows += [f".bn{{opacity:0;animation:ink .35s ease-out {TYPED + 0.15:.2f}s forwards}}"]
    rows += ["@media(prefers-reduced-motion:reduce){.bd,.bn{animation:none;opacity:1}}"]
    after_banner = TYPED + 0.5
    css = "\n".join([p_css, *rows, reveal("id", after_banner + 0.1), reveal("where", after_banner + 0.4)])

    body = (p_body
            + f'<g class="bn" font-family="{MONO}" font-size="10.4" fill="{t["text"]}">{banner_svg}</g>'
            + who + bird_svg)
    return svg(t, H_LIGHT, "n30dyn4m1c@pom:~$ whoami — N30 PNG. neo malesa, technologist, developer, "
                           "trader, writer, port moresby, beside a bird of paradise in ASCII",
               defs, css, body)


def main():
    for name, render in (("dark", synthwave), ("light", flag)):
        path = os.path.join(ROOT, "assets", f"hero-{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(THEMES[name]))
        print(f"wrote assets/hero-{name}.svg ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
