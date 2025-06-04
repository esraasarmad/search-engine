from math import ceil

from flask import Flask, render_template, request, url_for
from markupsafe import escape
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, PhrasePlugin
from whoosh.scoring import BM25F

from config import INDEX_DIR

app = Flask(__name__)

# 🔍 دالة توليد مقتطف ذكي
def extract_snippet(text, query):
    lines = text.split('.')
    query_words = query.lower().split()
    best_line = ""
    max_score = 0

    for line in lines:
        score = sum(1 for word in query_words if word in line.lower())
        if score > max_score:
            best_line = line.strip()
            max_score = score

    return best_line if best_line else text[:200] + "..."

# 🔎 صفحة البحث الرئيسية
@app.route("/")
def home():
    return render_template("search.html", search_url=url_for("results"))

# 📄 صفحة نتائج البحث
@app.route("/results")
def results():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = 5  # عدد النتائج لكل صفحة

    if not query.strip():
        return render_template(
            "results.html",
            query=query,
            results_list=[],
            search_url=url_for("results"),
            pagination=None,
        )

    ix = open_dir(INDEX_DIR)
    qp = MultifieldParser(["title", "content"], schema=ix.schema)
    qp.add_plugin(PhrasePlugin())
    q = qp.parse(escape(query))

    with ix.searcher(weighting=BM25F(B=0.5, K1=1.5)) as searcher:
        results = searcher.search(q, limit=None)
        total_results = len(results)
        total_pages = ceil(total_results / per_page)

        start = (page - 1) * per_page
        end = start + per_page
        current_results = results[start:end]

        results_list = []
        for result in current_results:
            content = result.get("content", "")
            teaser = extract_snippet(content, query)

            results_list.append({
                "url": result["url"],
                "title": result["title"],
                "teaser": teaser,
                "author": result.get("author", "غير معروف"),
                "trust_score": result.get("trust_score", 0)
            })

        pagination = {
            "page": page,
            "per_page": per_page,
            "total_results": total_results,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_num": page - 1,
            "next_num": page + 1,
        }

    return render_template(
        "results.html",
        query=query,
        results_list=results_list,
        search_url=url_for("results"),
        pagination=pagination,
    )
