"""Shared palette for every generated SVG: synthwave on void, and its light twin.

Light values are the same three hues pushed dark enough to pass WCAG AA on the
off-white base (cyan 5.9:1, magenta 6.7:1, muted 6.3:1 against #F6F4FA).
"""

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": {
        "bg": "#0D0221",
        "panel": "#12052C",
        "grid": "#1B0940",
        "text": "#C9D1D9",
        "muted": "#9A8FB8",
        "cyan": "#00FFCC",
        "magenta": "#FF00CC",
        # contribution heat, void through to cyan
        "heat": ["#160A33", "#1F3D63", "#177C8E", "#00C6A8", "#00FFCC"],
        "langs": ["#00FFCC", "#FF00CC", "#00C6A8", "#C31FD1", "#177C8E", "#7B1FA2"],
        "glow": True,
    },
    "light": {
        "bg": "#F6F4FA",
        "panel": "#EFEBF6",
        "grid": "#DDD6EA",
        "text": "#0D0221",
        "muted": "#5E5480",
        "cyan": "#006B57",
        "magenta": "#A3007F",
        "heat": ["#E7E2F0", "#B3DDD3", "#6CBFAE", "#2A9C86", "#006B57"],
        "langs": ["#006B57", "#A3007F", "#2A9C86", "#C3149C", "#177C8E", "#7B1FA2"],
        "glow": False,
    },
}
