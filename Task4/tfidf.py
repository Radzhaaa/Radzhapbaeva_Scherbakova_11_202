import math
import re
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer


try:
    stopwords.words("russian")
except LookupError:
    nltk.download("stopwords", quiet=True)


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR.parent / "Task 1" / "task1_pages" / "pages"

TOKENS_DIR = BASE_DIR / "Task2" / "tokens"
LEMMAS_DIR = BASE_DIR / "Task2" /"lemmas"

OUT_TERMS = BASE_DIR / "tfidf_terms"
OUT_LEMMAS = BASE_DIR / "tfidf_lemmas"

OUT_TERMS.mkdir(exist_ok=True)
OUT_LEMMAS.mkdir(exist_ok=True)


TOKEN_RE = re.compile(r"[а-яёА-ЯЁ]+")

STOPWORDS = set(stopwords.words("russian"))

morph = MorphAnalyzer()


def tokenize(text):

    tokens = []

    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group()

        if token in STOPWORDS:
            continue

        tokens.append(token)

    return tokens


def load_documents():

    docs = {}

    for path in DATA_DIR.rglob("*"):

        if not path.is_file():
            continue

        text = path.read_text(encoding="utf-8", errors="replace")

        tokens = tokenize(text)

        docs[path.stem] = tokens

    return docs


def compute_df(docs):

    df = {}

    for tokens in docs.values():

        unique = set(tokens)

        for term in unique:

            df[term] = df.get(term, 0) + 1

    return df


def compute_lemma_df(docs):

    df = {}

    for tokens in docs.values():

        lemmas = set()

        for token in tokens:
            lemma = morph.parse(token)[0].normal_form
            lemmas.add(lemma)

        for lemma in lemmas:
            df[lemma] = df.get(lemma, 0) + 1

    return df


def compute_tf(tokens):

    tf = {}

    total = len(tokens)

    for token in tokens:
        tf[token] = tf.get(token, 0) + 1

    for token in tf:
        tf[token] = tf[token] / total

    return tf


def compute_lemma_tf(tokens):

    lemma_counts = {}

    total = len(tokens)

    for token in tokens:

        lemma = morph.parse(token)[0].normal_form

        lemma_counts[lemma] = lemma_counts.get(lemma, 0) + 1

    for lemma in lemma_counts:
        lemma_counts[lemma] = lemma_counts[lemma] / total

    return lemma_counts


def main():

    docs = load_documents()

    N = len(docs)

    df_terms = compute_df(docs)
    df_lemmas = compute_lemma_df(docs)

    idf_terms = {t: math.log(N / df_terms[t]) for t in df_terms}
    idf_lemmas = {l: math.log(N / df_lemmas[l]) for l in df_lemmas}

    for doc_name, tokens in docs.items():

        tf_terms = compute_tf(tokens)
        tf_lemmas = compute_lemma_tf(tokens)

        term_file = OUT_TERMS / f"{doc_name}_tfidf_terms.txt"
        lemma_file = OUT_LEMMAS / f"{doc_name}_tfidf_lemmas.txt"

        with term_file.open("w", encoding="utf-8") as f:

            for term in sorted(tf_terms):

                tfidf = tf_terms[term] * idf_terms.get(term, 0)

                f.write(f"{term} {idf_terms.get(term,0):.6f} {tfidf:.6f}\n")

        with lemma_file.open("w", encoding="utf-8") as f:

            for lemma in sorted(tf_lemmas):

                tfidf = tf_lemmas[lemma] * idf_lemmas.get(lemma, 0)

                f.write(f"{lemma} {idf_lemmas.get(lemma,0):.6f} {tfidf:.6f}\n")

        print(f"Processed {doc_name}")


if __name__ == "__main__":
    main()