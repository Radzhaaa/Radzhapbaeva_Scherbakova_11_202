#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import json
import time

WIKI_API = "https://ru.wikipedia.org/w/api.php"
OUTPUT_FILE = "urls.txt"
MIN_URLS = 100
BATCH_SIZE = 100


def fetch_random_article_ids(count):
    result = []
    fetched = 0

    while fetched < count:
        params = {
            "action": "query",
            "list": "random",
            "rnnamespace": 0,
            "rnlimit": min(BATCH_SIZE, count - fetched),
            "format": "json",
        }
        url = WIKI_API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "CrawlerHomework/1.0 (Educational)"})

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        for item in data.get("query", {}).get("random", []):
            result.append((item["id"], item["title"]))
            fetched += 1

        if fetched < count:
            time.sleep(0.3)

    return result


def title_to_url(title):
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe="/")
    return f"https://ru.wikipedia.org/wiki/{encoded}"


def main():
    print(f"Запрашиваем минимум {MIN_URLS} статей с ru.wikipedia.org ...")
    articles = fetch_random_article_ids(MIN_URLS)
    urls = [title_to_url(title) for _, title in articles]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

    print(f"Сохранено {len(urls)} URL в {OUTPUT_FILE}")
    print("Дальше запустите: python crawler.py")


if __name__ == "__main__":
    main()
