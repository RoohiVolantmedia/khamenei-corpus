"""اتصال دیتابیس و کوئری‌های مرکزی"""
import sqlite3
import json
import os
import urllib.request
from pathlib import Path
from typing import Optional
import streamlit as st

# ─── مسیر دیتابیس ────────────────────────────────────────────────────────────
# ۱) محیط توسعه: فایل در کنار پوشه‌ی app
# ۲) محیط production: دانلود از Supabase Storage به /tmp

_DB_CACHE: Optional[Path] = None

# آدرس دیتابیس روی GitHub Releases
_DEFAULT_DB_URL = (
    "https://github.com/RoohiVolantmedia/khamenei-corpus"
    "/releases/download/V1.0/database_deploy.db"
)

def _get_db_path() -> Path:
    global _DB_CACHE
    if _DB_CACHE is not None:
        return _DB_CACHE

    # اجرای محلی: دیتابیس کنار پوشه‌ی app
    local = Path(__file__).resolve().parent.parent.parent / "database.db"
    if local.exists():
        _DB_CACHE = local
        return _DB_CACHE

    # production: بررسی cache در /tmp
    tmp = Path("/tmp/khamenei_db.db")
    if tmp.exists():
        _DB_CACHE = tmp
        return _DB_CACHE

    # دانلود — از secret یا URL پیش‌فرض
    url = os.environ.get("DB_URL", "") or _DEFAULT_DB_URL

    import requests
    tmp_partial = Path("/tmp/khamenei_db.db.part")
    try:
        with requests.get(url, stream=True, allow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            expected = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(str(tmp_partial), "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
        # بررسی کامل بودن فایل
        if expected > 0 and downloaded < expected * 0.99:
            raise RuntimeError(
                f"دانلود ناقص: {downloaded:,} از {expected:,} بایت دریافت شد"
            )
        # بررسی سلامت دیتابیس
        test_conn = sqlite3.connect(str(tmp_partial))
        count = test_conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        test_conn.close()
        if count < 10000:
            raise RuntimeError(
                f"دیتابیس ناقص است: فقط {count} سند یافت شد"
            )
        # انتقال اتمیک
        tmp_partial.rename(tmp)
    except Exception:
        if tmp_partial.exists():
            tmp_partial.unlink()
        raise

    _DB_CACHE = tmp
    return _DB_CACHE


def get_conn():
    db_path = _get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=600)
def get_stats() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    stats = {}
    cur.execute("SELECT COUNT(*) FROM documents")
    stats['total'] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM documents WHERE analytical_tier='tier1'")
    stats['tier1'] = cur.fetchone()[0]
    # فقط تاریخ‌های معتبر با ارقام ASCII (نه عربی-هندی) و بازه منطقی
    cur.execute("""
        SELECT MIN(date_persian), MAX(date_persian)
        FROM documents
        WHERE (date_persian GLOB '135[6-9]*'
            OR date_persian GLOB '136[0-9]*'
            OR date_persian GLOB '137[0-9]*'
            OR date_persian GLOB '138[0-9]*'
            OR date_persian GLOB '139[0-9]*'
            OR date_persian GLOB '14[0-9][0-9]*')
    """)
    r = cur.fetchone()
    stats['date_min'] = (r[0] or '')[:4]
    stats['date_max'] = (r[1] or '')[:4]
    cur.execute("SELECT COALESCE(SUM(word_count),0) FROM documents")
    stats['total_words'] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM documents WHERE date_persian >= '1404/01/01'")
    stats['last_year'] = cur.fetchone()[0]
    conn.close()
    return stats


@st.cache_data(ttl=600)
def get_period_distribution() -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT period_label, COUNT(*) AS cnt
        FROM documents
        WHERE period_label IS NOT NULL
        GROUP BY period_label ORDER BY MIN(date_persian)
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@st.cache_data(ttl=600)
def get_tier_distribution() -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(analytical_tier,'نامشخص') AS tier, COUNT(*) AS cnt
        FROM documents GROUP BY tier ORDER BY cnt DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@st.cache_data(ttl=600)
def get_yearly_counts(tier: Optional[str] = None) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    where = "WHERE date_persian GLOB '1[34][0-9][0-9]/*'"
    params = []
    if tier:
        where += " AND analytical_tier = ?"
        params.append(tier)
    cur.execute(f"""
        SELECT substr(date_persian,1,4) AS year, COUNT(*) AS cnt
        FROM documents {where}
        GROUP BY year
        HAVING CAST(year AS INTEGER) BETWEEN 1356 AND 1405
        ORDER BY year
    """, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@st.cache_data(ttl=600)
def get_tag_options() -> dict:
    """همه‌ی مقادیر یکتا برای فیلترهای تگ"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT tag_voice_type FROM doc_tags WHERE tag_voice_type IS NOT NULL ORDER BY 1")
    voice = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT tag_form_genre FROM doc_tags WHERE tag_form_genre IS NOT NULL ORDER BY 1")
    genre = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT value FROM doc_tags, json_each(tag_audience)
        WHERE tag_audience IS NOT NULL ORDER BY value
    """)
    audience = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT tag_occasion FROM doc_tags
        WHERE tag_occasion IS NOT NULL AND tag_occasion != ''
        ORDER BY 1
    """)
    occasion = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT value FROM doc_tags, json_each(tag_topics)
        WHERE tag_topics IS NOT NULL ORDER BY value
    """)
    topics = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT value FROM doc_tags, json_each(tag_regions)
        WHERE tag_regions IS NOT NULL ORDER BY value
    """)
    regions = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT value FROM doc_tags, json_each(tag_tone)
        WHERE tag_tone IS NOT NULL ORDER BY value
    """)
    tone = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT period_label, MIN(date_persian) AS first_date
        FROM documents
        WHERE period_label IS NOT NULL
        GROUP BY period_label
        ORDER BY first_date
    """)
    periods = [r[0] for r in cur.fetchall()]

    conn.close()
    return dict(voice=voice, genre=genre, audience=audience,
                occasion=occasion, topics=topics, regions=regions,
                tone=tone, periods=periods)


def build_search_query(
    keyword: str = '',
    logic: str = 'AND',
    search_in: str = 'both',
    normalize_fa: bool = True,
    stem: bool = True,
    tiers: list = None,
    sources: list = None,
    voice: list = None,
    genre: list = None,
    audience: list = None,
    occasion: list = None,
    topics: list = None,
    regions: list = None,
    tone: list = None,
    year_from: int = 1356,
    year_to: int = 1404,
    word_min: int = 0,
    word_max: int = 100000,
    periods: list = None,
    sort: str = 'date_desc',
    offset: int = 0,
    limit: int = 25,
) -> tuple[str, list]:
    from utils.persian import normalize, expand_stem

    conditions = []
    params = []

    # تگ‌های AI — JOIN با doc_tags
    join_clause = "LEFT JOIN doc_tags t ON d.doc_id = t.doc_id"

    # فیلتر کلیدواژه
    if keyword.strip():
        words = keyword.strip().split()
        kw_conds = []
        for w in words:
            if w.startswith('"') and w.endswith('"'):
                phrase = w[1:-1]
                variants = [phrase]
            elif w.startswith('-'):
                # NOT
                exclude = w[1:]
                if normalize_fa:
                    exclude = normalize(exclude)
                if search_in in ('title', 'both'):
                    conditions.append("d.title NOT LIKE ?")
                    params.append(f'%{exclude}%')
                if search_in in ('text', 'both'):
                    conditions.append("d.full_text NOT LIKE ?")
                    params.append(f'%{exclude}%')
                continue
            else:
                if normalize_fa:
                    w = normalize(w)
                variants = expand_stem(w) if stem else [w]

            col_conds = []
            for v in variants:
                if search_in in ('title', 'both'):
                    col_conds.append("d.title LIKE ?")
                    params.append(f'%{v}%')
                if search_in in ('text', 'both'):
                    col_conds.append("d.full_text LIKE ?")
                    params.append(f'%{v}%')
            if col_conds:
                kw_conds.append('(' + ' OR '.join(col_conds) + ')')

        if kw_conds:
            sep = ' AND ' if logic == 'AND' else ' OR '
            conditions.append('(' + sep.join(kw_conds) + ')')

    # فیلترهای ساختاری
    if tiers:
        ph = ','.join('?' * len(tiers))
        conditions.append(f"d.analytical_tier IN ({ph})")
        params.extend(tiers)
    if sources:
        ph = ','.join('?' * len(sources))
        conditions.append(f"d.content_source IN ({ph})")
        params.extend(sources)
    if periods:
        ph = ','.join('?' * len(periods))
        conditions.append(f"d.period_label IN ({ph})")
        params.extend(periods)

    # بازه زمانی
    conditions.append("(d.date_persian IS NULL OR (d.date_persian >= ? AND d.date_persian <= ?))")
    params.extend([f"{year_from}/01/01", f"{year_to}/12/29"])

    # تعداد کلمات
    if word_min > 0:
        conditions.append("d.word_count >= ?")
        params.append(word_min)
    if word_max < 100000:
        conditions.append("d.word_count <= ?")
        params.append(word_max)

    # فیلترهای تگ
    if voice:
        ph = ','.join('?' * len(voice))
        conditions.append(f"t.tag_voice_type IN ({ph})")
        params.extend(voice)
    if genre:
        ph = ','.join('?' * len(genre))
        conditions.append(f"t.tag_form_genre IN ({ph})")
        params.extend(genre)
    if audience:
        aud_conds = []
        for a in audience:
            aud_conds.append("EXISTS (SELECT 1 FROM json_each(t.tag_audience) WHERE value = ?)")
            params.append(a)
        conditions.append('(' + ' OR '.join(aud_conds) + ')')
    if occasion:
        ph = ','.join('?' * len(occasion))
        conditions.append(f"t.tag_occasion IN ({ph})")
        params.extend(occasion)
    if topics:
        top_conds = []
        for tp in topics:
            top_conds.append("EXISTS (SELECT 1 FROM json_each(t.tag_topics) WHERE value = ?)")
            params.append(tp)
        conditions.append('(' + ' OR '.join(top_conds) + ')')
    if regions:
        reg_conds = []
        for r in regions:
            reg_conds.append("EXISTS (SELECT 1 FROM json_each(t.tag_regions) WHERE value = ?)")
            params.append(r)
        conditions.append('(' + ' OR '.join(reg_conds) + ')')
    if tone:
        tone_conds = []
        for tn in tone:
            tone_conds.append("EXISTS (SELECT 1 FROM json_each(t.tag_tone) WHERE value = ?)")
            params.append(tn)
        conditions.append('(' + ' OR '.join(tone_conds) + ')')

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    order = {
        'date_desc':  "d.date_persian DESC",
        'date_asc':   "d.date_persian ASC",
        'words_desc': "d.word_count DESC",
        'words_asc':  "d.word_count ASC",
    }.get(sort, "d.date_persian DESC")

    sql = f"""
        SELECT d.doc_id, d.date_persian, d.title, d.word_count,
               d.content_source, d.analytical_tier, d.period_label,
               d.url, substr(d.full_text,1,600) AS snippet,
               t.tag_voice_type, t.tag_form_genre, t.tag_audience,
               t.tag_occasion, t.tag_topics, t.tag_regions, t.tag_tone
        FROM documents d {join_clause}
        {where}
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """
    count_sql = f"SELECT COUNT(*) FROM documents d {join_clause} {where}"
    return sql, count_sql, params, limit, offset


def search(conn, keyword='', logic='AND', search_in='both',
           normalize_fa=True, stem=True, tiers=None, sources=None,
           voice=None, genre=None, audience=None, occasion=None,
           topics=None, regions=None, tone=None,
           year_from=1356, year_to=1404, word_min=0, word_max=100000,
           periods=None, sort='date_desc', offset=0, limit=25):
    sql, count_sql, params, lim, off = build_search_query(
        keyword=keyword, logic=logic, search_in=search_in,
        normalize_fa=normalize_fa, stem=stem, tiers=tiers,
        sources=sources, voice=voice, genre=genre, audience=audience,
        occasion=occasion, topics=topics, regions=regions, tone=tone,
        year_from=year_from, year_to=year_to, word_min=word_min,
        word_max=word_max, periods=periods, sort=sort,
        offset=offset, limit=limit,
    )
    cur = conn.cursor()
    cur.execute(count_sql, params)
    total = cur.fetchone()[0]
    cur.execute(sql, params + [lim, off])
    rows = [dict(r) for r in cur.fetchall()]
    return total, rows


def get_doc(conn, doc_id: str) -> Optional[dict]:
    cur = conn.cursor()
    cur.execute("""
        SELECT d.*, t.tag_voice_type, t.tag_form_genre, t.tag_audience,
               t.tag_occasion, t.tag_topics, t.tag_regions, t.tag_tone
        FROM documents d
        LEFT JOIN doc_tags t ON d.doc_id = t.doc_id
        WHERE d.doc_id = ?
    """, (doc_id,))
    r = cur.fetchone()
    return dict(r) if r else None


def get_related_docs(conn, doc: dict, limit: int = 5) -> list[dict]:
    cur = conn.cursor()
    cur.execute("""
        SELECT d.doc_id, d.date_persian, d.title, d.word_count,
               d.content_source, d.analytical_tier
        FROM documents d
        LEFT JOIN doc_tags t ON d.doc_id = t.doc_id
        WHERE d.doc_id != ?
          AND (d.period_label = ? OR t.tag_form_genre = ?)
        ORDER BY RANDOM()
        LIMIT ?
    """, (doc['doc_id'], doc.get('period_label'), doc.get('tag_form_genre'), limit))
    return [dict(r) for r in cur.fetchall()]


def get_keyword_trend(conn, keywords: list[str], normalize_fa: bool = True) -> dict:
    from utils.persian import normalize
    result = {}
    for kw in keywords:
        q = normalize(kw) if normalize_fa else kw
        cur = conn.cursor()
        cur.execute("""
            SELECT substr(date_persian,1,4) AS year, COUNT(*) AS cnt
            FROM documents
            WHERE date_persian IS NOT NULL AND full_text LIKE ?
            GROUP BY year ORDER BY year
        """, (f'%{q}%',))
        result[kw] = {r['year']: r['cnt'] for r in cur.fetchall()}
    return result


def ensure_quote_library(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quote_library (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id      TEXT,
            quote_text  TEXT,
            note        TEXT,
            tag         TEXT,
            saved_at    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def save_quote(conn, doc_id: str, quote_text: str, note: str = '', tag: str = ''):
    ensure_quote_library(conn)
    conn.execute("""
        INSERT INTO quote_library (doc_id, quote_text, note, tag)
        VALUES (?, ?, ?, ?)
    """, (doc_id, quote_text, note, tag))
    conn.commit()


def get_quotes(conn, tag: str = '') -> list[dict]:
    ensure_quote_library(conn)
    if tag:
        cur = conn.execute("""
            SELECT q.*, d.title, d.date_persian, d.url
            FROM quote_library q
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            WHERE q.tag = ? ORDER BY q.saved_at DESC
        """, (tag,))
    else:
        cur = conn.execute("""
            SELECT q.*, d.title, d.date_persian, d.url
            FROM quote_library q
            LEFT JOIN documents d ON q.doc_id = d.doc_id
            ORDER BY q.saved_at DESC
        """)
    return [dict(r) for r in cur.fetchall()]


def delete_quote(conn, quote_id: int):
    conn.execute("DELETE FROM quote_library WHERE id = ?", (quote_id,))
    conn.commit()
