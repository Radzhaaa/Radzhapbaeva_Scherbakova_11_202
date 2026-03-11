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

DATA_DIR = Path(__file__).resolve().parent.parent / "Task 1" / "task1_pages" / "pages"

TOKENS_DIR = Path(__file__).resolve().parent / "tokens"
LEMMAS_DIR = Path(__file__).resolve().parent / "lemmas"

TOKENS_DIR.mkdir(parents=True, exist_ok=True)
LEMMAS_DIR.mkdir(parents=True, exist_ok=True)

TOKEN_RE = re.compile(r"[а-яёА-ЯЁ]+")

RU_STOPWORDS = set(stopwords.words("russian"))

morph = MorphAnalyzer()


def iter_docs():
    for path in DATA_DIR.rglob("*"):
        if path.is_file():
            yield path


def clean_tokens(text: str):
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group()

        if token in RU_STOPWORDS:
            continue

        yield token


def process_document(path: Path):

    text = path.read_text(encoding="utf-8", errors="replace")

    tokens = set()

    for tok in clean_tokens(text):
        tokens.add(tok)

    lemmas = {}

    for tok in tokens:
        lemma = morph.parse(tok)[0].normal_form
        lemmas.setdefault(lemma, set()).add(tok)

    return tokens, lemmas


def save_tokens(file_name, tokens):

    out_path = TOKENS_DIR / f"{file_name}_tokens.txt"

    out_path.write_text(
        "\n".join(sorted(tokens)),
        encoding="utf-8"
    )


def save_lemmas(file_name, lemmas):

    out_path = LEMMAS_DIR / f"{file_name}_lemmas.txt"

    with out_path.open("w", encoding="utf-8") as f:
        for lemma in sorted(lemmas):
            variants = " ".join(sorted(lemmas[lemma]))
            f.write(f"{lemma} {variants}\n")


def main():

    for path in iter_docs():

        file_name = path.stem

        tokens, lemmas = process_document(path)

        save_tokens(file_name, tokens)
        save_lemmas(file_name, lemmas)

        print(f"{file_name}: tokens={len(tokens)}, lemmas={len(lemmas)}")


if __name__ == "__main__":
    main()