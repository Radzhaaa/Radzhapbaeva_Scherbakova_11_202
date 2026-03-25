"""
vector_search.py — поисковая система на основе векторного поиска (TF-IDF + косинусное сходство).

Алгоритм:
1. Загружаем документы, лемматизируем, вычисляем TF-IDF векторы.
2. Принимаем запрос пользователя, лемматизируем слова запроса.
3. Строим TF-IDF вектор запроса (TF по запросу, IDF из корпуса).
4. Вычисляем косинусное сходство запроса с каждым документом.
5. Возвращаем документы, отсортированные по убыванию сходства.
"""

import math
import os
import re
from collections import defaultdict

import nltk
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer



try:
    stopwords.words("russian")
except LookupError:
    nltk.download("stopwords", quiet=True)

morph = MorphAnalyzer()
STOPWORDS = set(stopwords.words("russian"))
TOKEN_RE = re.compile(r"[а-яёa-z]+")

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'Task3', 'docs')


# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────

def lemmatize(text: str) -> list[str]:
    """Токенизация + лемматизация + удаление стоп-слов."""
    tokens = TOKEN_RE.findall(text.lower())
    lemmas = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        lemma = morph.parse(token)[0].normal_form
        lemmas.append(lemma)
    return lemmas


def compute_tf(lemmas: list[str]) -> dict[str, float]:
    """Вычислить TF (term frequency) для списка лемм."""
    tf: dict[str, float] = {}
    total = len(lemmas)
    if total == 0:
        return tf
    for lemma in lemmas:
        tf[lemma] = tf.get(lemma, 0) + 1
    for lemma in tf:
        tf[lemma] /= total
    return tf


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Косинусное сходство двух векторов, заданных словарями."""
    dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in vec_b)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ──────────────────────────────────────────────
# Построение индекса
# ──────────────────────────────────────────────

def load_and_index(docs_dir: str):
    """
    Загрузить документы, вычислить TF-IDF векторы.
    Возвращает:
        doc_vectors — dict[doc_id -> dict[lemma -> tfidf]]
        idf         — dict[lemma -> idf]
    """
    # 1. Читаем документы, лемматизируем
    doc_lemmas: dict[str, list[str]] = {}
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith('.txt'):
            continue
        path = os.path.join(docs_dir, filename)
        with open(path, encoding='utf-8') as f:
            text = f.read()
        doc_lemmas[filename] = lemmatize(text)

    N = len(doc_lemmas)

    # 2. Вычисляем DF (document frequency)
    df: dict[str, int] = defaultdict(int)
    for lemmas in doc_lemmas.values():
        for lemma in set(lemmas):
            df[lemma] += 1

    # 3. Вычисляем IDF
    idf = {lemma: math.log(N / df[lemma]) for lemma in df}

    # 4. Строим TF-IDF вектор для каждого документа
    doc_vectors: dict[str, dict[str, float]] = {}
    for doc_id, lemmas in doc_lemmas.items():
        tf = compute_tf(lemmas)
        doc_vectors[doc_id] = {lemma: tf[lemma] * idf[lemma] for lemma in tf}

    return doc_vectors, idf


# ──────────────────────────────────────────────
# Поиск
# ──────────────────────────────────────────────

def vector_search(
    query: str,
    doc_vectors: dict[str, dict[str, float]],
    idf: dict[str, float],
    top_k: int = 10
) -> list[tuple[str, float]]:
    """
    Найти документы по запросу с помощью косинусного сходства.
    Возвращает список (doc_id, score), отсортированный по убыванию score.
    """
    query_lemmas = lemmatize(query)
    if not query_lemmas:
        return []

    # TF-IDF вектор запроса (IDF берём из корпуса)
    tf_query = compute_tf(query_lemmas)
    query_vector = {lemma: tf_query[lemma] * idf.get(lemma, 0.0) for lemma in tf_query}

    scores = []
    for doc_id, doc_vec in doc_vectors.items():
        score = cosine_similarity(query_vector, doc_vec)
        if score > 0:
            scores.append((doc_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# ──────────────────────────────────────────────
# Интерактивный режим (CLI)
# ──────────────────────────────────────────────

def interactive():
    print("=" * 60)
    print("  Векторный поисковый движок (TF-IDF + косинусное сходство)")
    print("  Введите 'exit' для выхода")
    print("=" * 60)

    docs_dir = os.path.normpath(DOCS_DIR)
    print(f"\nЗагрузка документов из: {docs_dir}")
    doc_vectors, idf = load_and_index(docs_dir)
    print(f"Проиндексировано документов: {len(doc_vectors)}, уникальных лемм: {len(idf)}\n")

    while True:
        try:
            query = input("Запрос> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not query:
            continue
        if query.lower() in ('exit', 'quit', 'выход'):
            break

        results = vector_search(query, doc_vectors, idf)
        if results:
            print(f"Найдено документов: {len(results)}")
            for doc_id, score in results:
                print(f"  {doc_id}  (сходство: {score:.4f})")
        else:
            print("Ничего не найдено.")
        print()


if __name__ == '__main__':
    interactive()
