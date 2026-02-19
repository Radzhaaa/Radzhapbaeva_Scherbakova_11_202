#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import urllib.request
from pathlib import Path

URLS_FILE = "urls.txt"
PAGES_DIR = "pages"
INDEX_FILE = "index.txt"
DELAY_SEC = 0.8
TIMEOUT_SEC = 15
USER_AGENT = "CrawlerHomework/1.0 (Educational; Python)"
SKIP_EXTENSIONS = (".js", ".css", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".woff", ".woff2", ".pdf")
CONTENT_TYPE_OK = re.compile(r"text/html", re.I)


def load_urls(path):
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def should_skip_url(url):
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in SKIP_EXTENSIONS)


def fetch_page(url):
    if should_skip_url(url):
        return False, "это не текст (js/css/картинка и т.д.)"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if not CONTENT_TYPE_OK.search(content_type):
                return False, f"Content-Type не text/html: {content_type}"

            encoding = resp.headers.get("Content-Charset") or "utf-8"
            if "charset=" in content_type:
                match = re.search(r"charset=([\w-]+)", content_type, re.I)
                if match:
                    encoding = match.group(1).strip()
            try:
                body = resp.read().decode(encoding, errors="replace")
            except LookupError:
                body = resp.read().decode("utf-8", errors="replace")

            return True, body
    except Exception as e:
        return False, str(e)


def main():
    script_dir = Path(__file__).resolve().parent
    urls_path = script_dir / URLS_FILE
    pages_path = script_dir / PAGES_DIR
    index_path = script_dir / INDEX_FILE

    if not urls_path.exists():
        print(f"Файл {URLS_FILE} не найден. Сначала запустите: python get_urls.py")
        return 1

    urls = load_urls(urls_path)
    if not urls:
        print("Список URL пуст. Добавьте ссылки в urls.txt (по одной на строку).")
        return 1

    pages_path.mkdir(exist_ok=True)
    index_lines = []
    success_count = 0
    file_number = 0

    print(f"Всего URL в списке: {len(urls)}. Сохраняем в {PAGES_DIR}/, индекс в {INDEX_FILE}")

    for i, url in enumerate(urls, start=1):
        ok, data = fetch_page(url)
        if not ok:
            print(f"  [{i}] Пропуск: {url} — {data}")
            continue

        file_number += 1
        filename = f"page_{file_number:03d}.txt"
        filepath = pages_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
        index_lines.append(f"{file_number}\t{url}")
        success_count += 1
        print(f"  [{i}] OK: {filename} <- {url[:60]}...")

        if i < len(urls):
            time.sleep(DELAY_SEC)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

    print(f"\nГотово. Успешно скачано: {success_count}. Индекс: {INDEX_FILE}")
    if success_count < 100:
        print("  Замечание: для сдачи нужно минимум 100 страниц. Добавьте URL в urls.txt и запустите снова.")
    return 0


if __name__ == "__main__":
    exit(main())
