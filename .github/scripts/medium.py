#!/usr/bin/env python3
"""Daily check of the Medium feed: update README only when new articles exist."""
import html
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

START, END = "<!-- MEDIUM:START -->", "<!-- MEDIUM:END -->"
README = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "README.md"))
FEED = "https://medium.com/feed/@neomalesa"
PROFILE = "https://medium.com/@neomalesa"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def feed_items(limit=5):
    xml_text = re.sub(r'\sxmlns="[^"]*"', "", fetch(FEED), count=1)
    root = ET.fromstring(xml_text)
    items = []
    for it in root.findall(".//item")[:limit]:
        title = (it.findtext("title") or "untitled").strip()
        link = (it.findtext("link") or "#").split("?")[0]
        date = " ".join((it.findtext("pubDate") or "").split()[1:3])
        items.append({"title": title, "link": link, "date": date})
    return items


def latest_in_readme(block):
    m = re.search(r'<td><a href="[^"]*">(.*?)</a></td>', block, re.S)
    return html.unescape(m.group(1)) if m else None


def build_block(items):
    source = f'<sub>source &middot; <a href="{PROFILE}">medium.com/@neomalesa</a></sub>'
    if not items:
        return source
    lines = ["<table>"]
    for it in items:
        lines.append(
            "<tr>\n"
            f'<td width="90"><code>{html.escape(it["date"])}</code></td>\n'
            f'<td><a href="{html.escape(it["link"], quote=True)}">{html.escape(it["title"])}</a></td>\n'
            "</tr>"
        )
    lines += ["</table>", "", source]
    return "\n".join(lines)


def main():
    try:
        items = feed_items()
    except Exception:
        print("feed down, keeping existing content")
        return
    with open(README, encoding="utf-8") as f:
        text = f.read()
    a = text.index(START)
    b = text.index(END)
    block = text[a + len(START):b]
    if items and latest_in_readme(block) == items[0]["title"]:
        print("no new articles")
        return
    new_block = build_block(items)
    new_text = text[: a + len(START)] + "\n\n" + new_block + "\n\n" + text[b:]
    with open(README, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("README updated with new articles")


if __name__ == "__main__":
    main()
