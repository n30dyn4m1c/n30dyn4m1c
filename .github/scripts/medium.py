#!/usr/bin/env python3
"""Daily check of the Medium feed: update README only when new articles exist."""
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

START, END = "<!-- MEDIUM:START -->", "<!-- MEDIUM:END -->"
README = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "README.md"))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def feed_items(limit=5):
    xml_text = re.sub(r'\sxmlns="[^"]*"', "", fetch("https://medium.com/feed/@neomalesa"), count=1)
    root = ET.fromstring(xml_text)
    items = []
    for it in root.findall(".//item")[:limit]:
        title = (it.findtext("title") or "untitled").strip()
        link = (it.findtext("link") or "#").split("?")[0]
        date = " ".join((it.findtext("pubDate") or "").split()[1:3])
        items.append({"title": title, "link": link, "date": date})
    return items


def latest_in_readme(block):
    m = re.search(r"- \d{1,2} \w{3} — \[([^\]]+)\]", block)
    return m.group(1) if m else None


def build_block(items):
    if not items:
        return "**latest from Medium** — none yet"
    lines = ["**latest from Medium**"]
    for it in items:
        title = it["title"].replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- {it['date']} — [{title}]({it['link']})")
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
