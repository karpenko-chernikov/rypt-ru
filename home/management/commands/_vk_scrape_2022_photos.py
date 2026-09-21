#!/usr/bin/env python3
"""Scrape public VK album photo URLs into season_2022_photos.json."""
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ALBUMS = ["https://vk.ru/album-44049348_283368624"]
OUT = Path(__file__).with_name("season_2022_photos.json")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TITLE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
ROW = re.compile(r'<div([^>]*id="photo_row_(-?\d+)_(\d+)"[^>]*)>', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", "replace")


def album_parts(url):
    m = re.search(r"album(-?\d+)_(\d+)", url)
    if not m:
        raise SystemExit(f"bad album url: {url}")
    return m.group(1), m.group(2)


def scrape_album(url):
    owner, album = album_parts(url)
    seen = set()
    shots = []
    title = ""
    offset = 0
    while True:
        page_url = f"https://vk.com/album{owner}_{album}?offset={offset}"
        print(f"  {owner}_{album} offset {offset}", flush=True)
        body = fetch(page_url)
        if not title:
            m = TITLE.search(body)
            title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() if m else ""
        new = 0
        for m in ROW.finditer(body):
            attrs, oid, pid = m.group(1), m.group(2), m.group(3)
            um = re.search(r"url\(([^)]+)\)", attrs)
            if not um:
                continue
            key = f"{oid}_{pid}"
            if key in seen:
                continue
            seen.add(key)
            shots.append(
                {
                    "id": pid,
                    "owner": oid,
                    "src": html.unescape(um.group(1).strip("\"'")),
                    "original": f"https://vk.ru/photo{oid}_{pid}",
                    "album": url,
                    "caption": "",
                }
            )
            new += 1
        print(f"    new {new} total {len(shots)} title={title!r}", flush=True)
        if new == 0:
            break
        offset += 40
        time.sleep(0.35)
    return shots


def main():
    all_shots = []
    for url in ALBUMS:
        print("ALBUM", url, flush=True)
        all_shots.extend(scrape_album(url))
    OUT.write_text(json.dumps(all_shots, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, "count", len(all_shots), flush=True)


if __name__ == "__main__":
    main()
