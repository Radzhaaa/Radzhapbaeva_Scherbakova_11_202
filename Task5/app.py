import os
from flask import Flask, request, send_from_directory, jsonify
from Task5.vector_search import load_and_index, vector_search, lemmatize, compute_tf

app = Flask(__name__)

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'Task3', 'docs')

DOC_VECTORS, IDF = load_and_index(DOCS_DIR)


def load_docs_metadata(docs_dir: str) -> dict[str, dict[str, str]]:
    """Собираем короткий заголовок/сниппет для каждого документа."""
    meta: dict[str, dict[str, str]] = {}
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith('.txt'):
            continue
        path = os.path.join(docs_dir, filename)
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        first_sentence = text.split('.', 1)[0].strip()
        title = first_sentence[:120] + ('…' if len(first_sentence) > 120 else '')
        snippet = text[:240] + ('…' if len(text) > 240 else '')
        meta[filename] = {
            "title": title or filename,
            "snippet": snippet,
            "url": f"/docs/{filename}",
        }
    return meta


DOC_META = load_docs_metadata(DOCS_DIR)


@app.route("/", methods=["GET"])
def search():
    # Отдаём готовый HTML-шаблон из vector_search.html (Jinja не нужен)
    return send_from_directory(os.path.dirname(__file__), "vector_search.html")


@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"query": query, "results": [], "query_vector": {}})

    raw = vector_search(query, DOC_VECTORS, IDF, top_k=10)

    q_lemmas = lemmatize(query)
    tf_query = compute_tf(q_lemmas)
    query_vector = {lemma: tf_query[lemma] * IDF.get(lemma, 0.0) for lemma in tf_query if IDF.get(lemma, 0.0) > 0}

    results = []
    for doc_id, score in raw:
        meta = DOC_META.get(doc_id, {})
        results.append({
            "doc_id": doc_id,
            "score": score,
            "title": meta.get("title", doc_id),
            "snippet": meta.get("snippet", ""),
            "url": meta.get("url", f"/docs/{doc_id}"),
        })

    return jsonify({"query": query, "results": results, "query_vector": query_vector})


@app.route("/docs/<path:doc_id>")
def serve_doc(doc_id: str):
    # Отдаём исходный текст документа для кликабельной ссылки
    return send_from_directory(DOCS_DIR, doc_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1025, debug=True)
