# تعديل الكود السابق لإضافة تقييم الثقة (trust scoring) وربطها مع Whoosh indexing

import os
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from whoosh.fields import ID, TEXT, NUMERIC, Schema
from whoosh.index import create_in
from whoosh.analysis import StemmingAnalyzer
import whois
import datetime

from config import INDEX_DIR, MAX_PAGES_PER_SITE, TARGET_SITES, USER_AGENT

# ------------------ تقييم الثقة ------------------

def uses_https(url):
    return url.lower().startswith("https://")

def domain_trust_score(url):
    trusted_domains = ['.gov', '.edu', 'who.int', 'bbc.com', 'nytimes.com']
    return any(domain in url for domain in trusted_domains)

def get_domain_age(domain_name):
    try:
        w = whois.whois(domain_name)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            today = datetime.datetime.now()
            return (today - creation).days // 365
    except:
        pass
    return 0
def readability_score(text):
    if len(text) > 1000:
        return 55
    elif len(text) > 500:
        return 40
    else:
        return 25

def count_outgoing_links(soup):
    return len(soup.find_all('a'))

def has_author_info(text):
    return 'author' in text.lower() or 'by' in text.lower()

# دالة محسّنة لحساب درجة الثقة مع الأخذ في الاعتبار أنواع المصداقية
def calculate_trust_score(url, soup):
    from urllib.parse import urlparse
    text = soup.get_text(separator=' ', strip=True)
    parsed = urlparse(url)
    domain = parsed.netloc

    score = 0
    credibility_types_detected = [] # لتتبع أنواع المصداقية المكتشفة

    # 1. المصداقية المفترضة (Presumed credibility): تعتمد على افتراضات عامة عن المصدر
    #    (هنا: استخدام HTTPS، المجالات الموثوقة)
    if uses_https(url):
        score += 2
        credibility_types_detected.append("Presumed (HTTPS)")
    if domain_trust_score(url):
        score += 3
        credibility_types_detected.append("Presumed (Trusted Domain)")

    # 2. المصداقية المكتسبة (Reputed credibility): بناءً على تقييم أطراف ثالثة في الماضي
    #    (هنا: عمر النطاق كبديل بسيط للاسم الجيد أو السمعة)
    domain_age = get_domain_age(domain)
    if domain_age >= 5:
        score += 2
        credibility_types_detected.append("Reputed (Domain Age >= 5)")
    elif domain_age >= 1:
        score += 1
        credibility_types_detected.append("Reputed (Domain Age >= 1)")

    # 3. المصداقية السطحية (Surface credibility): المظهر الجمالي أو الاحترافي (صعب التقييم تلقائيًا)
    #    (يمكن تمثيله جزئيًا بمؤشرات مثل وجود معلومات المؤلف وعدد الروابط الخارجية)
    #    *ملاحظة: هذا تقدير تقريبي جداً. التقييم الحقيقي للمصداقية السطحية يتطلب تحليل التصميم، الأخطاء الإملائية/النحوية، إلخ.*
    readability = readability_score(text)
    if readability > 60:
        score += 2
        credibility_types_detected.append("Surface (High Readability)")
    elif readability > 30:
        score += 1
        credibility_types_detected.append("Surface (Moderate Readability)")

    if has_author_info(text):
        score += 1
        credibility_types_detected.append("Surface (Author Info Present)")

    links = count_outgoing_links(soup)
    if links > 10:
        score += 2
        credibility_types_detected.append("Surface (Many Outgoing Links)") # يمكن أن يشير إلى مصادر غنية، ولكن يمكن أن يكون إشارة لـ spam أيضاً
    elif links > 3:
        score += 1
        credibility_types_detected.append("Surface (Some Outgoing Links)")

    # 4. المصداقية القائمة على الخبرة (Experienced credibility): تتطلب تفاعل المستخدم المباشر
    #    (لا يمكن تقييمها مباشرة بواسطة الزاحف، ولكن يمكن دمجها لاحقاً من بيانات السلوك)

    return score, credibility_types_detected # إرجاع درجة الثقة وأنواع المصداقية المكتشفة

def extract_author(soup):
    # من <meta name="author">
    meta = soup.find("meta", attrs={"name": "author"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    # من class معروف
    author_tags = soup.find_all(class_=["author", "byline", "writer"])
    for tag in author_tags:
        if tag.get_text(strip=True):
            return tag.get_text(strip=True)

    # fallback: فحص كلمات like "by NAME"
    text = soup.get_text()
    for line in text.split("\n"):
        if line.lower().strip().startswith("by "):
            return line.strip()

    return "unknown"

# ------------------ إنشاء الفهرس ------------------

schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    trust_score=NUMERIC(stored=True),
    author=TEXT(stored=True),
    credibility_types=TEXT(stored=True) # حقل جديد لتخزين أنواع المصداقية
)

if not os.path.exists(INDEX_DIR):
    os.mkdir(INDEX_DIR)
ix = create_in(INDEX_DIR, schema)
writer = ix.writer()

# ------------------ الزحف ------------------

visited = set()
headers = {"User-Agent": USER_AGENT}

def crawl_site(start_url, max_pages):
    to_visit = [start_url]
    pages_crawled = 0

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"Crawling: {url}")
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                continue
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            continue

        visited.add(url)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
        content = soup.get_text(separator=' ', strip=True)

        # استدعاء دالة calculate_trust_score المعدلة
        trust_score, credibility_types = calculate_trust_score(url, soup)
        author = extract_author(soup)

        if trust_score >= 5:  # فقط الصفحات الموثوقة
            writer.add_document(
                url=url,
                title=title,
                content=content,
                trust_score=trust_score,
                author=author,
                credibility_types=",".join(credibility_types) # تخزين الأنواع كقائمة مفصولة بفاصلة
            )
            pages_crawled += 1
            print(f"✅ Indexed (Trust Score: {trust_score}, Author: {author}, Types: {', '.join(credibility_types)})")

        if max_pages > 0 and pages_crawled >= max_pages:
            break

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            if (
                urlparse(href).netloc == urlparse(start_url).netloc
                and href not in visited
            ):
                to_visit.append(href)

# تنفيذ الزحف
for site in TARGET_SITES:
    crawl_site(site, MAX_PAGES_PER_SITE)

writer.commit()
print("✅ Crawling and indexing with trust score and credibility types completed.")