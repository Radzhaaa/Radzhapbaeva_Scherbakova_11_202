"""
boolean_search.py — булев поиск по инвертированному индексу.

Поддерживает операторы: AND, OR, NOT
Поддерживает скобки для группировки, например:
  (Клеопатра AND Цезарь) OR (Антоний AND Цицерон) OR Помпей
"""

import json
import os
import re
import sys


# ──────────────────────────────────────────────
# Загрузка индекса
# ──────────────────────────────────────────────

def load_index(path: str) -> dict[str, set[str]]:
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    return {term: set(docs) for term, docs in raw.items()}


def get_all_docs(index: dict) -> set[str]:
    """Множество всех документов, встречающихся в индексе."""
    all_docs: set[str] = set()
    for docs in index.values():
        all_docs |= docs
    return all_docs


# ──────────────────────────────────────────────
# Лексер (токенизация запроса)
# ──────────────────────────────────────────────

TOKEN_LPAREN  = 'LPAREN'   # (
TOKEN_RPAREN  = 'RPAREN'   # )
TOKEN_AND     = 'AND'
TOKEN_OR      = 'OR'
TOKEN_NOT     = 'NOT'
TOKEN_TERM    = 'TERM'
TOKEN_EOF     = 'EOF'


class Token:
    def __init__(self, type_: str, value: str = ''):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value!r})'


def tokenize_query(query: str) -> list[Token]:
    """Разбить строку запроса на токены."""
    tokens: list[Token] = []
    i = 0
    query = query.strip()

    while i < len(query):
        ch = query[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '(':
            tokens.append(Token(TOKEN_LPAREN, '('))
            i += 1
            continue

        if ch == ')':
            tokens.append(Token(TOKEN_RPAREN, ')'))
            i += 1
            continue

        # Читаем слово (кириллица + латиница)
        if re.match(r'[а-яёa-zА-ЯЁA-Z]', ch, re.IGNORECASE):
            j = i
            while j < len(query) and re.match(r'[а-яёa-zА-ЯЁA-Z0-9_\-]', query[j], re.IGNORECASE):
                j += 1
            word = query[i:j]
            upper = word.upper()
            if upper == 'AND':
                tokens.append(Token(TOKEN_AND, 'AND'))
            elif upper == 'OR':
                tokens.append(Token(TOKEN_OR, 'OR'))
            elif upper == 'NOT':
                tokens.append(Token(TOKEN_NOT, 'NOT'))
            else:
                tokens.append(Token(TOKEN_TERM, word.lower()))
            i = j
            continue

        raise SyntaxError(f"Неизвестный символ: {ch!r} на позиции {i}")

    tokens.append(Token(TOKEN_EOF))
    return tokens


# ──────────────────────────────────────────────
# Рекурсивный парсер (LL(1))
#
# Грамматика:
#   expr   ::= term (OR term)*
#   term   ::= factor (AND factor)*
#   factor ::= NOT factor | '(' expr ')' | TERM
# ──────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token], index: dict, all_docs: set):
        self.tokens = tokens
        self.pos = 0
        self.index = index
        self.all_docs = all_docs

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected_type: str | None = None) -> Token:
        tok = self.tokens[self.pos]
        if expected_type and tok.type != expected_type:
            raise SyntaxError(
                f"Ожидался {expected_type}, получен {tok.type} ({tok.value!r})"
            )
        self.pos += 1
        return tok

    def parse(self) -> set[str]:
        result = self.expr()
        self.consume(TOKEN_EOF)
        return result

    def expr(self) -> set[str]:
        """expr ::= term (OR term)*"""
        result = self.term()
        while self.current().type == TOKEN_OR:
            self.consume(TOKEN_OR)
            right = self.term()
            result = result | right
        return result

    def term(self) -> set[str]:
        """term ::= factor (AND factor)*"""
        result = self.factor()
        while self.current().type == TOKEN_AND:
            self.consume(TOKEN_AND)
            right = self.factor()
            result = result & right
        return result

    def factor(self) -> set[str]:
        """factor ::= NOT factor | '(' expr ')' | TERM"""
        tok = self.current()

        if tok.type == TOKEN_NOT:
            self.consume(TOKEN_NOT)
            operand = self.factor()
            return self.all_docs - operand

        if tok.type == TOKEN_LPAREN:
            self.consume(TOKEN_LPAREN)
            result = self.expr()
            self.consume(TOKEN_RPAREN)
            return result

        if tok.type == TOKEN_TERM:
            self.consume(TOKEN_TERM)
            return set(self.index.get(tok.value, set()))

        raise SyntaxError(
            f"Неожиданный токен: {tok.type} ({tok.value!r})"
        )


# ──────────────────────────────────────────────
# Публичный API поиска
# ──────────────────────────────────────────────

def boolean_search(query: str, index: dict, all_docs: set) -> set[str]:
    """
    Выполнить булев поиск по запросу.
    Возвращает множество найденных документов.
    """
    tokens = tokenize_query(query)
    parser = Parser(tokens, index, all_docs)
    return parser.parse()


# ──────────────────────────────────────────────
# Интерактивный режим (CLI)
# ──────────────────────────────────────────────

def interactive(index_path: str):
    print("=" * 60)
    print("  Булев поисковый движок")
    print("  Операторы: AND, OR, NOT, скобки ( )")
    print("  Пример: (Клеопатра AND Цезарь) OR (Антоний AND Цицерон)")
    print("  Введите 'exit' для выхода")
    print("=" * 60)

    index = load_index(index_path)
    all_docs = get_all_docs(index)
    print(f"\nИндекс загружен. Документов: {len(all_docs)}, терминов: {len(index)}\n")

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

        try:
            results = boolean_search(query, index, all_docs)
            if results:
                print(f"Найдено документов ({len(results)}): {sorted(results)}")
            else:
                print("Ничего не найдено.")
        except SyntaxError as e:
            print(f"Ошибка в запросе: {e}")
        print()


if __name__ == '__main__':
    BASE_DIR   = os.path.dirname(__file__)
    INDEX_PATH = os.path.join(BASE_DIR, 'inverted_index.json')

    if not os.path.exists(INDEX_PATH):
        print(f"Файл индекса не найден: {INDEX_PATH}")
        print("Сначала запустите: python build_index.py")
        sys.exit(1)

    interactive(INDEX_PATH)
