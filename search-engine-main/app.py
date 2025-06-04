from math import ceil
from flask import Flask, render_template, request, url_for
from markupsafe import escape
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, PhrasePlugin
from whoosh.scoring import BM25F
from config import INDEX_DIR
from bs4 import BeautifulSoup
import re


app = Flask(__name__)

def extract_main_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    selectors = [
        {"id": "main"},
        {"role": "main"},
        {"class_": "article-body"},
        {"class_": "story-body"},
        {"class_": "main-content"},
        {"class_": "article__content"},
    ]
    for sel in selectors:
        main = soup.find(**sel)
        if main:
            return main.get_text(separator=' ', strip=True)

    # fallback: article tag
    article = soup.find('article')
    if article:
        return article.get_text(separator=' ', strip=True)

    # fallback: أول 3 فقرات
    paragraphs = soup.find_all('p')
    long_paras = [p.get_text() for p in paragraphs if len(p.get_text()) > 100]
    if long_paras:
        return ' '.join(long_paras[:3])

    return soup.get_text(separator=' ', strip=True)


# 🔍 دالة تلخيص ذكية لتحديد نوع المحتوى والرياضات
def summarize_result(content, query):
    content_lower = content.lower()

    # نوع المحتوى
    if "live" in content_lower or "results" in content_lower or "score" in content_lower:
        kind = "Live Scores Page"
    elif "schedule" in content_lower or "fixtures" in content_lower:
        kind = "Match Schedule"
    elif "news" in content_lower or "preview" in content_lower:
        kind = "News Article"
    else:
        kind = "General Sports Content"

    # أنواع الرياضات
    sports_keywords = ["football", "soccer", "tennis", "golf", "basketball", "f1", "cricket", "rugby", "nfl"]
    sports_found = [sport.capitalize() for sport in sports_keywords if sport in content_lower]
    sports_str = ", ".join(sports_found) if sports_found else "Unspecified"

    # حالة التحديث
    is_live = "Live" if any(word in content_lower for word in ["live", "now", "updated", "streaming"]) else "Not Live"

    return kind, sports_str, is_live

def extract_weighted_keywords_snippet(text, query, max_words=20):
    # تنظيف النص وتحويله إلى كلمات
    words = re.findall(r'\b\w+\b', text.lower())
    query_words = query.lower().split()

    # قائمة بالكلمات المهمة المحيطة بالكلمات المفتاحية
    important_words = []
    for i, word in enumerate(words):
        if any(q in word for q in query_words):
            # نأخذ الجيران: 3 قبل و3 بعد الكلمة
            context = words[max(0, i-3): i+4]
            important_words.extend(context)

    # إزالة التكرارات والإضافات العامة
    stop_words = {"the", "and", "a", "to", "of", "in", "on", "for", "is", "are", "be", "by", "with", "at", "from", "it"}
    filtered = [w for w in important_words if w not in stop_words]

    # نختار أول 20 كلمة فقط
    snippet = " ".join(filtered[:max_words])
    return snippet.capitalize() + "..." if snippet else text[:200] + "..."


# صفحة البحث الرئيسية
@app.route("/")
def home():
    return render_template("search.html", search_url=url_for("results"))

# صفحة عرض النتائج
@app.route("/results")
def results():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = 5

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
            raw_html = result.get("content", "")
            main_text = extract_main_content(raw_html)
            teaser = extract_weighted_keywords_snippet(main_text, query)
            kind, sports_str, is_live = summarize_result(main_text, query)

            results_list.append({
                "url": result["url"],
                "title": result["title"],
                "teaser": teaser,
                "author": result.get("author", "Unknown"),
                "trust_score": result.get("trust_score", 0),
                "kind": kind,
                "sports": sports_str,
                "live_status": is_live
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
