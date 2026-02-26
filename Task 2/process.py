#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer

try:
    stopwords.words("russian")
except LookupError:
    nltk.download("stopwords", quiet=True)

DATA_DIR = Path(__file__).resolve().parent.parent / "Task 1" / "pages"
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOKEN_FILE = OUT_DIR / "tokens.txt"
LEMMA_FILE = OUT_DIR / "lemmas.txt"

TOKEN_RE = re.compile(r"[а-яёА-ЯЁ]+")
RU_STOPWORDS = set(stopwords.words("russian"))
morph = MorphAnalyzer()


def iter_docs():
    for path in DATA_DIR.rglob("*"):
        if path.is_file():
            yield path.read_text(encoding="utf-8", errors="replace")


def clean_tokens(text: str):
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group()
        if token in RU_STOPWORDS:
            continue
        yield token


def main():
    tokens = set()
    for doc in iter_docs():
        for tok in clean_tokens(doc):
            tokens.add(tok)

    lemmas = {}
    for tok in tokens:
        lemma = morph.parse(tok)[0].normal_form
        lemmas.setdefault(lemma, set()).add(tok)

    TOKEN_FILE.write_text("\n".join(sorted(tokens)), encoding="utf-8")
    with LEMMA_FILE.open("w", encoding="utf-8") as f:
        for lemma in sorted(lemmas):
            variants = " ".join(sorted(lemmas[lemma]))
            f.write(f"{lemma} {variants}\n")

    print(f"Done. Tokens: {len(tokens)}, Lemmas: {len(lemmas)}")
    print(f"Output: {TOKEN_FILE}, {LEMMA_FILE}")


if __name__ == "__main__":
    main()
