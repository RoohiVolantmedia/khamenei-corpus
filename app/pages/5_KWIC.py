"""صفحه‌ی KWIC — کلیدواژه در بافت"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import sqlite3
import pandas as pd
import csv, io
from datetime import datetime
from utils.theme import render_header, render_footer

DB_PATH = str(Path.home() / "Desktop/khamenei_corpus/database.db")

render_header("کلیدواژه در بافت")
st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:15px;line-height:1.9;color:#033246">
  <p>
    <strong>کلیدواژه‌در-بافت (<bdi>KWIC</bdi>)</strong>
    هر بار که کلمه‌ای در پیکره ظاهر می‌شود را با متن قبل و بعد نشان می‌دهد.
    این ابزار برای مطالعه‌ی <strong>هم‌نشینی، معنا و تحول مفهومی</strong> واژه‌ها در طول زمان مفید است.
  </p>
</div>
""")
st.divider()

@st.cache_resource
def get_db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.row_factory = sqlite3.Row
    return c
conn = get_db()

# ─── فیلترها ─────────────────────────────────────────────────────────────────
with st.expander("تنظیمات جستجو", expanded=True):
    c1, c2 = st.columns([3, 2])
    keyword = c1.text_input("کلیدواژه *", placeholder="مثال: استکبار  یا  جمهوری اسلامی",
                             key="kwic_kw")
    whole_word = c1.checkbox("تطابق کل کلمه", value=True,
                              help="فقط کلمه مستقل پیدا کند — مثلاً «دشمن» داخل «دشمنان» را نشان ندهد.\n"
                                   "برای جستجوی پیشوند/پسوند این گزینه را بردارید.")
    use_regex = c1.checkbox("جستجوی پیشرفته (regex / wildcard)", value=False,
                             help="مثال: استکبار.* یا ^انقلاب | برای wildcard از .* استفاده کنید")

    c3, c4, c5 = c2.columns(3)
    win_size = c3.selectbox("پنجره (کاراکتر)", [60, 80, 120, 160], index=1,
                             format_func=lambda x: f"±{x}")
    max_hits = c4.selectbox("حداکثر نتیجه", [100, 300, 500, 1000], index=1,
                             format_func=lambda x: f"{x:,}")
    SORT_OPTS = {
        "واژه قبلی":  "واژه قبلی (الفبایی بر اساس واژه محتوایی بلافاصله پیش از کلیدواژه)",
        "واژه بعدی":  "واژه بعدی (الفبایی بر اساس واژه محتوایی بلافاصله پس از کلیدواژه)",
        "تاریخ":      "از جدیدترین به قدیمی‌ترین",
        "شناسه سند":  "بر اساس doc_id",
    }
    sort_by = c5.selectbox("مرتب‌سازی", list(SORT_OPTS.keys()),
                            help="\n\n".join(f"**{k}**: {v}" for k, v in SORT_OPTS.items()))

    cc1, cc2 = st.columns(2)
    yr1 = cc1.number_input("از سال", 1360, 1404, 1368, step=1, key='kwic_y1')
    yr2 = cc1.number_input("تا سال", 1356, 1404, 1404, step=1, key='kwic_y2')
    sel_tier = cc2.multiselect("نوع سند",
                                ['tier1','tier2','tier3','tier4'],
                                format_func=lambda x: {
                                    'tier1':'tier1 — سخنرانی مستقیم',
                                    'tier2':'tier2 — متن ویرایش‌شده',
                                    'tier3':'tier3 — خلاصه / گزیده',
                                    'tier4':'tier4 — گزارش راوی',
                                }.get(x, x))
    SRC_FA = {
        'speech':             'speech — سخنرانی',
        'speech_supplement':  'speech_supplement — متمم سخنرانی',
        'message':            'message — پیام',
        'decree':             'decree — حکم / فرمان',
    }
    sel_src = cc2.multiselect("منبع",
                               ['speech','speech_supplement','message','decree'],
                               format_func=lambda x: SRC_FA.get(x, x))

# خواندن query_params برای permalink
_qp = st.query_params
if _qp and not keyword:
    keyword = _qp.get('kw', '')
    if keyword and 'kwic_kw' not in st.session_state:
        st.session_state['kwic_kw'] = keyword
    try:    yr1 = int(_qp.get('y1', yr1))
    except: pass
    try:    yr2 = int(_qp.get('y2', yr2))
    except: pass

run_btn = st.button("🔍 اجرا", type="primary", use_container_width=False,
                     disabled=not keyword.strip())

if not run_btn and not keyword.strip():
    st.info("یک کلیدواژه وارد کنید و دکمه «اجرا» را بزنید.")
    st.stop()

if not keyword.strip():
    st.stop()

kw = keyword.strip()

# ─── کوئری پایگاه داده ───────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def fetch_docs(_conn, kw, yr1, yr2, sel_tier, sel_src, use_regex, max_hits):
    conds = ["(d.date_persian IS NULL OR d.date_persian BETWEEN ? AND ?)"]
    params = [f"{int(yr1)}/01/01", f"{int(yr2)}/12/29"]

    if use_regex:
        # برای regex از Python فیلتر می‌کنیم — ابتدا همه docها را با LIKE گسترده می‌گیریم
        # سپس در Python regex اعمال می‌شود
        pass
    else:
        conds.append("d.full_text LIKE ?")
        params.append(f'%{kw}%')

    if sel_tier:
        conds.append(f"d.analytical_tier IN ({','.join('?'*len(sel_tier))})")
        params.extend(sel_tier)
    if sel_src:
        conds.append(f"d.content_source IN ({','.join('?'*len(sel_src))})")
        params.extend(sel_src)

    where = "WHERE " + " AND ".join(conds)
    rows = _conn.execute(f"""
        SELECT d.doc_id, d.date_persian, d.title, d.analytical_tier, d.url,
               d.full_text
        FROM documents d {where}
        ORDER BY d.date_persian DESC
        LIMIT {max_hits * 5}
    """, params).fetchall()
    return [dict(r) for r in rows]

with st.spinner("در حال جستجو در پیکره…"):
    docs = fetch_docs(conn, kw, yr1, yr2,
                      tuple(sel_tier), tuple(sel_src),
                      use_regex, max_hits)

# ─── استخراج KWIC در Python ──────────────────────────────────────────────────
def extract_kwic(text, kw, win, use_regex, whole_word=True):
    """Returns list of (before, matched_kw, after) tuples"""
    results = []
    if not text:
        return results
    if use_regex:
        try:
            pat = kw
            if whole_word:
                pat = r'(?<!\w)' + kw + r'(?!\w)'
            pattern = re.compile(pat, re.IGNORECASE)
        except re.error:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
    else:
        base = re.escape(kw)
        if whole_word:
            base = r'(?<!\w)' + base + r'(?!\w)'
        pattern = re.compile(base, re.IGNORECASE)

    for m in pattern.finditer(text):
        start, end = m.start(), m.end()
        before = text[max(0, start - win): start]
        after  = text[end: end + win]
        matched = m.group()
        # trim to word boundaries approximately
        if start - win > 0:
            # cut to first space in before
            sp = before.find(' ')
            if sp != -1:
                before = before[sp+1:]
        if end + win < len(text):
            # cut to last space in after
            sp = after.rfind(' ')
            if sp != -1:
                after = after[:sp]
        results.append((before.strip(), matched, after.strip()))
    return results

# ─── کلمات توقف فارسی ────────────────────────────────────────────────────────
FA_STOP = {
    # حروف ربط و اضافه
    'و','در','از','با','به','که','را','یا','اما','ولی','چون','زیرا',
    'اگر','تا','بر','هم','نیز','برای','پس','بعد','قبل','بین','هر','همه','چند',
    'مگر','گرچه','هرچه','هرچند','اگرچه','چنانچه','چنانکه','چراکه',
    # ضمایر و اشاره
    'این','آن','من','تو','او','ما','شما','آنها','آن‌ها','ایشان','خود','خویش',
    'همین','همان','اینجا','آنجا','کجا','کی','چی','چه','چرا','چگونه',
    'آن‌که','این‌که','بدان','بدین','آیا','هیچ',
    # افعال کمکی — با نیم‌فاصله
    'است','بود','هست','شد','شده','شدن','بودن','هستند','بودند','شدند',
    'می‌شود','می‌کند','می‌کنند','می‌کرد','می‌شد',
    'کرد','کردن','کرده','دارد','داشت','دارند','داشتند','داریم','دارم',
    'می‌دهد','داد','دادن','داده','می‌گوید','گفت','گفته','گفتند',
    'می‌رود','رفت','رفته','رفتند','می‌آید','آمد','آمده','آمدند',
    'می‌شوند','می‌باشد','می‌باشند','باشد','باشند','باشیم',
    'می‌تواند','می‌توانند','می‌توان','توانست','کنند','کنیم','کنم','کنید',
    'بکند','بکنند','بکنیم','نیست','نبود','نشد','نمی‌شود','نمی‌کند',
    # افعال کمکی — بدون نیم‌فاصله (در متون قدیمی‌تر)
    'میشود','میکند','میکنند','میکرد','میشد','میدهد','میگوید',
    'میرود','میاید','میباشد','میباشند','میتواند','میتوانند','میتوان',
    'میخواهد','میخواهند','میخواهم','میخواهیم',
    'می‌خواهد','می‌خواهند','می‌خواهم','خواست','خواهد','خواهند',
    # قیود
    'هنوز','دیگر','فقط','تنها','البته','حتی','مثل','مانند','همچون',
    'چنین','چنان','بنابراین','لذا','همچنین','ضمن','طی','تحت','علیه',
    'جهت','باید','نباید','بله','خیر','نه','بلی','آری',
    'پیش','زیر','روی','کنار','میان','بالا','پایین','همواره','اکنون','الان',
    # پسوندهای تکی (اگر whole_word خاموش باشد)
    'ای','می','ها','های','گان','ات','ان','ی',
}

def first_content_word(words: list[str], reverse: bool = False) -> str:
    """اولین واژه محتوایی (غیر توقف) را برمی‌گرداند"""
    seq = reversed(words) if reverse else iter(words)
    for w in seq:
        w = w.strip('،؛؟!«»()[]{}.:،-_/‌‍‌‍‎‏﻿')
        if not w:
            continue
        if len(w) < 2:
            continue
        if w in FA_STOP:
            continue
        if re.match(r'^[\d۰-۹]+$', w):   # عدد
            continue
        if re.match(r'^[a-zA-Z]+$', w):   # انگلیسی خالص
            continue
        if re.match(r'^[\W_]+$', w):       # فقط علامت‌گذاری
            continue
        if re.match(r'^[ـ\-_]+$', w):      # خط کشیده / tatweel
            continue
        return w
    return ''

hits = []
for doc in docs:
    if len(hits) >= max_hits:
        break
    occurrences = extract_kwic(doc['full_text'], kw, win_size, use_regex, whole_word)
    for before, matched, after in occurrences:
        if len(hits) >= max_hits:
            break
        before_words = [w for w in before.split() if w]
        after_words  = [w for w in after.split()  if w]
        # واژه محتوایی قبل: آخرین واژه غیر توقف در متن قبل
        l1 = first_content_word(before_words, reverse=True)
        # واژه محتوایی بعد: اولین واژه غیر توقف در متن بعد
        r1 = first_content_word(after_words,  reverse=False)
        hits.append({
            'before':  before,
            'keyword': matched,
            'after':   after,
            'l1':      l1,
            'r1':      r1,
            'doc_id':  doc['doc_id'],
            'date':    doc['date_persian'] or '',
            'title':   (doc['title'] or '')[:40],
            'tier':    doc['analytical_tier'] or '',
            'url':     doc['url'] or '',
        })

# ─── مرتب‌سازی ────────────────────────────────────────────────────────────────
if sort_by == "واژه قبلی":
    hits.sort(key=lambda h: h['l1'])
elif sort_by == "واژه بعدی":
    hits.sort(key=lambda h: h['r1'])
elif sort_by == "تاریخ":
    hits.sort(key=lambda h: h['date'])
elif sort_by == "شناسه سند":
    hits.sort(key=lambda h: h['doc_id'])

# ─── نمایش آمار ──────────────────────────────────────────────────────────────
total_docs  = len(docs)
total_hits  = len(hits)
shown_hits  = min(total_hits, max_hits)

col_a, col_b, col_c = st.columns(3)
col_a.metric("کل نتایج (محل ظهور)", f"{total_hits:,}")
col_b.metric("اسناد حاوی کلیدواژه", f"{total_docs:,}")
col_c.metric("نمایش داده‌شده", f"{shown_hits:,}")

if not hits:
    st.warning(f"کلیدواژه «{kw}» در پیکره با این فیلترها پیدا نشد.")
    st.stop()

st.divider()

# ─── نمایش KWIC ───────────────────────────────────────────────────────────────
st.subheader(f"نتایج KWIC برای: «{kw}»")
st.caption(f"مرتب‌سازی: {sort_by} | پنجره: ±{win_size} کاراکتر | رنگ قرمز = کلیدواژه | حروف ربط از مرتب‌سازی حذف شده‌اند")

# Build HTML table for proper RTL KWIC display
rows_html = ""
for h in hits:
    doc_link = f'<a href="{h["url"]}" target="_blank" style="color:#2980b9;text-decoration:none">{h["doc_id"]}</a>' if h["url"] else h["doc_id"]
    rows_html += f"""
    <tr>
      <td class="left" dir="rtl">{h["before"]}</td>
      <td class="kw">{h["keyword"]}</td>
      <td class="right" dir="rtl">{h["after"]}</td>
      <td class="meta">{h["date"][:7] if h["date"] else "—"}</td>
      <td class="meta">{doc_link}</td>
      <td class="meta">{h["tier"]}</td>
    </tr>"""

table_html = f"""
<div style="overflow-x:auto; max-height:600px; overflow-y:auto;">
<table class="kwic-table">
  <thead>
    <tr>
      <th style="text-align:right">متن قبل</th>
      <th style="text-align:center">کلیدواژه</th>
      <th style="text-align:right">متن بعد</th>
      <th>تاریخ</th>
      <th>سند</th>
      <th>نوع</th>
    </tr>
  </thead>
  <tbody>{rows_html}</tbody>
</table>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# ─── نمودارهای توزیع — query مستقل از کل پیکره ──────────────────────────────
import plotly.express as px
import plotly.graph_objects as go

st.divider()
st.subheader("توزیع زمانی ظهور کلیدواژه")
st.caption("بر اساس **کل** اسناد منطبق در پیکره — نه فقط نتایج نمایش‌داده‌شده در جدول")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_year_dist(_conn, kw, yr1, yr2, sel_tier, sel_src, use_regex, whole_word):
    """توزیع سالانه از کل پیکره — بدون محدودیت max_hits"""
    conds = ["date_persian BETWEEN ? AND ?",
             "date_persian GLOB '1[34][0-9][0-9]/*'"]
    params = [f"{int(yr1)}/01/01", f"{int(yr2)}/12/29"]

    if not use_regex:
        # برای جستجوی ساده: LIKE در SQL (substring) — کافی است برای شمارش سند
        conds.append("full_text LIKE ?")
        params.append(f'%{kw}%')
    # اگر whole_word یا regex: ابتدا با LIKE فیلتر می‌کنیم، سپس Python دقیق‌تر می‌کند
    # اما برای نمودار سالانه، LIKE کافی است (تفاوت جزئی)

    if sel_tier:
        conds.append(f"analytical_tier IN ({','.join('?'*len(sel_tier))})"); params.extend(sel_tier)
    if sel_src:
        conds.append(f"content_source IN ({','.join('?'*len(sel_src))})"); params.extend(sel_src)

    where = "WHERE " + " AND ".join(conds)
    rows = _conn.execute(f"""
        SELECT substr(date_persian,1,4) AS year, COUNT(*) AS n
        FROM documents {where}
        GROUP BY year ORDER BY year
    """, params).fetchall()
    return [(int(r[0]), r[1]) for r in rows if r[0] and r[0].isdigit()]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_doc_dates(_conn, kw, yr1, yr2, sel_tier, sel_src):
    """تاریخ و شناسه همه اسناد حاوی کلیدواژه — برای بارکد"""
    conds = ["date_persian BETWEEN ? AND ?",
             "date_persian GLOB '1[34][0-9][0-9]/*'",
             "full_text LIKE ?"]
    params = [f"{int(yr1)}/01/01", f"{int(yr2)}/12/29", f'%{kw}%']
    if sel_tier:
        conds.append(f"analytical_tier IN ({','.join('?'*len(sel_tier))})"); params.extend(sel_tier)
    if sel_src:
        conds.append(f"content_source IN ({','.join('?'*len(sel_src))})"); params.extend(sel_src)
    where = "WHERE " + " AND ".join(conds)
    rows = _conn.execute(f"""
        SELECT doc_id, substr(date_persian,1,4) AS year
        FROM documents {where}
        ORDER BY date_persian
    """, params).fetchall()
    return [(r[0], int(r[1])) for r in rows if r[1] and r[1].isdigit()]

with st.spinner("بارگذاری توزیع زمانی…"):
    year_dist  = fetch_year_dist(conn, kw, yr1, yr2,
                                 tuple(sel_tier), tuple(sel_src), use_regex, whole_word)
    doc_dates  = fetch_doc_dates(conn, kw, yr1, yr2,
                                 tuple(sel_tier), tuple(sel_src))

tab_bar, tab_barcode = st.tabs(["📊 نمودار میله‌ای", "🎼 بارکد پراکنش"])

with tab_bar:
    if year_dist:
        df_yr = pd.DataFrame(year_dist, columns=['year', 'count'])
        fig_bar = px.bar(df_yr, x='year', y='count',
                     labels={'year':'سال (شمسی)', 'count':'تعداد سند'},
                     title=f"تعداد اسناد حاوی «{kw}» به تفکیک سال ({sum(df_yr['count']):,} سند)",
                     color_discrete_sequence=['#c0392b'])
        fig_bar.update_layout(
            font_family='Vazirmatn', title_font_size=14,
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(tickmode='linear', dtick=5, type='linear'),
            yaxis=dict(rangemode='tozero'),
            height=340, margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("داده سالانه‌ای یافت نشد.")

with tab_barcode:
    st.caption(
        "هر خط عمودی = یک سند حاوی کلیدواژه. "
        "هر چه خطوط متراکم‌تر باشند، کلیدواژه در آن دوره پُربسامدتر است."
    )
    if doc_dates:
        df_bc = pd.DataFrame(doc_dates, columns=['doc_id', 'year'])
        # شمارش سند بر سال برای opacity
        yr_counts = df_bc.groupby('year').size().reset_index(name='n')
        max_n = yr_counts['n'].max()

        fig_bc = go.Figure()
        for _, row in yr_counts.iterrows():
            opacity = float(row['n']) / max_n * 0.85 + 0.15
            fig_bc.add_shape(
                type="line",
                x0=row['year'], x1=row['year'],
                y0=0, y1=1,
                line=dict(color=f"rgba(192,57,43,{opacity:.2f})", width=2)
            )

        fig_bc.update_layout(
            title=f"بارکد پراکنش «{kw}» در پیکره ({len(df_bc):,} سند)",
            xaxis=dict(
                title="سال (شمسی)",
                tickmode='linear', dtick=5, type='linear',
                range=[int(yr1) - 1, int(yr2) + 1]
            ),
            yaxis=dict(visible=False, range=[0, 1]),
            height=200,
            plot_bgcolor='#fafafa', paper_bgcolor='white',
            font_family='Vazirmatn',
            margin=dict(l=20, r=20, t=40, b=40),
            showlegend=False
        )
        st.plotly_chart(fig_bc, use_container_width=True)

        # توزیع دهه
        df_bc['decade'] = (df_bc['year'] // 10 * 10).astype(str) + 's'
        decade_tbl = df_bc.groupby('decade').size().reset_index(name='تعداد سند')
        decade_tbl.columns = ['دهه', 'تعداد سند']
        st.caption("توزیع به تفکیک دهه:")
        st.dataframe(decade_tbl, hide_index=True, use_container_width=False)
    else:
        st.info("داده تاریخی کافی نیست.")

# ─── هم‌نشین‌های پُربسامد ─────────────────────────────────────────────────────
st.divider()
st.subheader("پُربسامدترین واژه‌های هم‌نشین")
st.caption(
    "واژه‌های محتوایی که بیشتر از همه **قبل** یا **بعد** از کلیدواژه ظاهر می‌شوند. "
    "حروف ربط، ضمایر و افعال کمکی فیلتر شده‌اند تا فقط واژه‌های معنادار بمانند."
)
from collections import Counter

l1_counts = Counter(h['l1'] for h in hits if h['l1'])
r1_counts = Counter(h['r1'] for h in hits if h['r1'])

col_l, col_r = st.columns(2)
with col_l:
    st.markdown(f"**← پیش از «{kw}»** (واژه محتوایی قبلی)")
    if l1_counts:
        df_l1 = pd.DataFrame(l1_counts.most_common(15), columns=['واژه', 'تعداد'])
        st.dataframe(df_l1, use_container_width=True, hide_index=True, height=320)
    else:
        st.info("داده کافی نیست")
with col_r:
    st.markdown(f"**پس از «{kw}» →** (واژه محتوایی بعدی)")
    if r1_counts:
        df_r1 = pd.DataFrame(r1_counts.most_common(15), columns=['واژه', 'تعداد'])
        st.dataframe(df_r1, use_container_width=True, hide_index=True, height=320)
    else:
        st.info("داده کافی نیست")

# ─── Permalink ───────────────────────────────────────────────────────────────
st.divider()
import urllib.parse as _up
with st.expander("پیوند اشتراک‌گذاری این جستجو", icon="🔗", expanded=False):
    _base = "http://localhost:8502/KWIC"
    _pp = {'kw': kw, 'y1': str(int(yr1)), 'y2': str(int(yr2))}
    _qs = _up.urlencode(_pp, quote_via=_up.quote)
    _link = f"{_base}?{_qs}"
    st.code(_link, language=None)
    st.caption("این لینک کلیدواژه و بازه سال را ذخیره می‌کند.")

# ─── دانلود CSV ───────────────────────────────────────────────────────────────
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
buf = io.StringIO()
writer = csv.DictWriter(buf,
    fieldnames=['before','keyword','after','l1','r1','date','doc_id','title','tier','url'],
    extrasaction='ignore')
writer.writeheader()
writer.writerows(hits)
st.download_button(
    "⬇ دانلود نتایج KWIC (CSV)",
    ('﻿' + buf.getvalue()).encode('utf-8'),
    file_name=f"kwic_{kw[:20]}_{ts}.csv",
    mime="text/csv",
    use_container_width=True
)

render_footer()
