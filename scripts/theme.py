"""Shared palette for every generated SVG.

Dark is synthwave on void. Light is the PNG flag on paper: black, flag red and
bird-of-paradise gold. Roles stay the same across both:
  accent  structure, commands, up-moves   (cyan / deep gold)
  hot     highlights, live items, down-moves (magenta / flag red)
Text-bearing light colours pass WCAG AA on #FAF6EE: ink 17.1:1, red 5.2:1,
deep gold 4.9:1, muted 6.7:1. Flag gold (#FCD116) is fill-only.
"""

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": {
        "bg": "#0D0221",
        "panel": "#12052C",
        "grid": "#1B0940",
        "text": "#C9D1D9",
        "muted": "#9A8FB8",
        "accent": "#00FFCC",
        "hot": "#FF00CC",
        # contribution heat, void through to cyan
        "heat": ["#160A33", "#1F3D63", "#177C8E", "#00C6A8", "#00FFCC"],
        "langs": ["#00FFCC", "#FF00CC", "#00C6A8", "#C31FD1", "#177C8E", "#7B1FA2"],
        "glow": True,
    },
    "light": {
        "bg": "#FAF6EE",
        "panel": "#F3ECDD",
        "grid": "#E6DCC8",
        "text": "#141414",
        "muted": "#5F564D",
        "accent": "#8A6500",
        "hot": "#CE1126",
        "gold": "#FCD116",
        # contribution heat, paper through flag gold to flag red
        "heat": ["#EFE7D6", "#F7E08A", "#FCD116", "#E88A1A", "#CE1126"],
        "langs": ["#CE1126", "#141414", "#E0B000", "#8A6500", "#E0574A", "#5F564D"],
        "glow": False,
    },
}
