"""
build_index.py — построение инвертированного индекса из текстовых документов.
"""

import os
import re
import json
from collections import defaultdict


def tokenize(text: str) -> list[str]:
    """Разбить текст на токены: нижний регистр, только буквы."""
    text = text.lower()
    tokens = re.findall(r'[а-яёa-z]+', text)
    return tokens


def build_inverted_index(docs_dir: str) -> dict[str, list[str]]:
    """
    Построить инвертированный индекс из всех .txt файлов в папке docs_dir.
    Возвращает словарь: термин -> список документов (отсортированный).
    """
    index: dict[str, set] = defaultdict(set)

    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(docs_dir, filename)
        doc_id = filename  # используем имя файла как ID документа

        with open(filepath, encoding='utf-8') as f:
            text = f.read()

        tokens = tokenize(text)
        for token in tokens:
            index[token].add(doc_id)

    # Преобразуем set -> отсортированный list для JSON-сериализации
    return {term: sorted(doc_ids) for term, doc_ids in sorted(index.items())}


def save_index(index: dict, output_path: str) -> None:
    """Сохранить индекс в JSON-файл."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Индекс сохранён: {output_path}")
    print(f"Всего уникальных терминов: {len(index)}")


if __name__ == '__main__':
    DOCS_DIR = os.path.join(os.path.dirname(__file__), 'docs')
    OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'inverted_index.json')

    index = build_inverted_index(DOCS_DIR)
    save_index(index, OUTPUT_PATH)

    # Пример вывода нескольких записей
    print("\nПример записей индекса:")
    sample_terms = ['цезарь', 'клеопатра', 'антоний', 'помпей', 'цицерон']
    for term in sample_terms:
        if term in index:
            print(f"  {term}: {index[term]}")
