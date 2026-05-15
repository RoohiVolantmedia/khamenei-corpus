"""صفحه‌ی کلیدواژگی (Keyness Analysis)"""
import sys
import math
import io
import random
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

from utils.corpus_index import tokenize, normalize_fa, is_built, DB_PATH, FA_STOP, FA_STOP_EXTENDED
from utils.theme import render_header, render_footer

render_header("کلیدواژگی — Keyness")
st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:15px;line-height:1.9;color:#033246">
  <p>
    <strong>کلیدواژگی (<bdi>Keyness</bdi>)</strong>
    نشان می‌دهد کدام واژه‌ها در یک دوره یا فیلتر مشخص، نسبت به مابقی پیکره،
    به‌طور آماری بیشتر از حد انتظار ظاهر می‌شوند.
  </p>
  <p>
    این تحلیل بر اساس معیار
    <strong><bdi>G²</bdi> (لگاریتم درستنمایی)</strong>
    انجام می‌شود —
    مقدار مثبت = کلیدی در پیکره الف،
    مقدار منفی = کلیدی در پیکره ب.
  </p>
</div>
""")
st.divider()

# ─── بررسی جدول بسامد ─────────────────────────────────────────────────────────
if not is_built():
    st.error(
        "جدول بسامد پیکره ساخته نشده است. "
        "ابتدا به صفحه «هم‌نشینی» بروید و جدول بسامد را بسازید."
    )
    st.stop()

PERIOD_FA = {
    'pre_revolution':  'قبل از انقلاب',
    'early_revolution': 'اوایل انقلاب',
    'presidency':      'دوران ریاست جمهوری',
    'hashemi':         'رفسنجانی',
    'khatami':         'خاتمی',
    'ahmadinejad':     'احمدی‌نژاد',
    'rouhani':         'روحانی',
    'raisi_to_death':  'رئیسی تا مرگ',
}

ALL_PERIODS = list(PERIOD_FA.keys())


@st.cache_resource
def get_db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.row_factory = sqlite3.Row
    return c


conn = get_db()


def _build_doc_query(periods, yr1, yr2, keyword_filter, tier_filter):
    """ساخت کوئری SQL برای گرفتن اسناد با فیلترهای داده‌شده"""
    conds = ["date_persian BETWEEN ? AND ?"]
    params = [f"{int(yr1)}/01/01", f"{int(yr2)}/12/29"]

    if periods:
        conds.append(f"period_label IN ({','.join('?' * len(periods))})")
        params.extend(periods)

    if keyword_filter and keyword_filter.strip():
        conds.append("full_text LIKE ?")
        params.append(f'%{keyword_filter.strip()}%')

    if tier_filter:
        conds.append(f"analytical_tier IN ({','.join('?' * len(tier_filter))})")
        params.extend(tier_filter)

    where = "WHERE " + " AND ".join(conds)
    return where, params


# ─── انتخاب دو پیکره ─────────────────────────────────────────────────────────
st.subheader("انتخاب دو پیکره برای مقایسه")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### پیکره الف")
    periods_a = st.multiselect(
        "دوره‌های زمانی",
        ALL_PERIODS,
        default=['pre_revolution', 'early_revolution', 'presidency'],
        format_func=lambda x: PERIOD_FA.get(x, x),
        key="ks_periods_a"
    )
    ca1, ca2 = st.columns(2)
    yr1_a = ca1.number_input("از سال", 1356, 1404, 1356, step=1, key="ks_yr1a")
    yr2_a = ca2.number_input("تا سال", 1356, 1404, 1376, step=1, key="ks_yr2a")
    kw_filter_a = st.text_input("فیلتر کلیدواژه (اختیاری)", key="ks_kw_a", placeholder="برای محدود کردن به اسناد حاوی این واژه")
    tier_a = st.multiselect(
        "نوع سند",
        ['tier1', 'tier2', 'tier3', 'tier4'],
        format_func=lambda x: {
            'tier1': 'tier1 — سخنرانی مستقیم',
            'tier2': 'tier2 — متن ویرایش‌شده',
            'tier3': 'tier3 — خلاصه / گزیده',
            'tier4': 'tier4 — گزارش راوی',
        }.get(x, x),
        key="ks_tier_a"
    )

with col_b:
    st.markdown("#### پیکره ب")
    periods_b = st.multiselect(
        "دوره‌های زمانی",
        ALL_PERIODS,
        default=['hashemi', 'khatami', 'ahmadinejad', 'rouhani', 'raisi_to_death'],
        format_func=lambda x: PERIOD_FA.get(x, x),
        key="ks_periods_b"
    )
    cb1, cb2 = st.columns(2)
    yr1_b = cb1.number_input("از سال", 1356, 1404, 1377, step=1, key="ks_yr1b")
    yr2_b = cb2.number_input("تا سال", 1356, 1404, 1404, step=1, key="ks_yr2b")
    kw_filter_b = st.text_input("فیلتر کلیدواژه (اختیاری)", key="ks_kw_b", placeholder="برای محدود کردن به اسناد حاوی این واژه")
    tier_b = st.multiselect(
        "نوع سند",
        ['tier1', 'tier2', 'tier3', 'tier4'],
        format_func=lambda x: {
            'tier1': 'tier1 — سخنرانی مستقیم',
            'tier2': 'tier2 — متن ویرایش‌شده',
            'tier3': 'tier3 — خلاصه / گزیده',
            'tier4': 'tier4 — گزارش راوی',
        }.get(x, x),
        key="ks_tier_b"
    )

st.divider()
col_opt1, col_opt2, col_opt3 = st.columns([2, 2, 2])

with col_opt1:
    min_freq = st.slider(
        "حداقل بسامد در هر پیکره",
        min_value=2,
        max_value=20,
        value=5,
        step=1,
        help="واژه‌هایی که در مجموع کمتر از این تعداد ظاهر شده‌اند نادیده گرفته می‌شوند",
        key="ks_min_freq"
    )

with col_opt2:
    filter_stopwords = st.checkbox(
        "حذف واژه‌های دستوری (stop words)",
        value=True,
        key="ks_filter_stop",
        help="افعال کمکی، ضمایر، حروف ربط و اضافه را از نتایج حذف می‌کند",
    )

with col_opt3:
    filter_stopwords_ext = st.checkbox(
        "حذف افعال عام (فرمود، نمود...)",
        value=False,
        key="ks_filter_stop_ext",
        help="علاوه بر stop words پایه، افعال پرتکرار گفتاری مثل فرمود، نمود، دانست را هم حذف می‌کند",
    )

run_btn = st.button("🔑 محاسبه کلیدواژگی", type="primary")

if not run_btn:
    st.info("پیکره الف و ب را انتخاب کنید و دکمه «محاسبه» را بزنید.")
    st.stop()


# ─── محاسبه کلیدواژگی ────────────────────────────────────────────────────────
MAX_DOCS_PER_CORPUS = 3000


@st.cache_data(ttl=300, show_spinner=False)
def compute_keyness(_conn, filters_a: tuple, filters_b: tuple,
                   min_freq: int = 5, stop_set: frozenset = frozenset()):
    """
    محاسبه کلیدواژگی با G² (log-likelihood) برای دو زیر‌پیکره.
    filters_a/b: (periods, yr1, yr2, kw_filter, tier_filter)
    stop_set: مجموعه‌ی واژه‌هایی که از نتایج حذف می‌شوند
    """
    def get_doc_texts(filters):
        periods, yr1, yr2, kw_filter, tier_filter = filters
        where, params = _build_doc_query(
            list(periods), yr1, yr2,
            kw_filter, list(tier_filter)
        )
        rows = _conn.execute(
            f"SELECT doc_id, full_text FROM documents {where}",
            params
        ).fetchall()
        return [(r[0], r[1]) for r in rows if r[1]]

    docs_a = get_doc_texts(filters_a)
    docs_b = get_doc_texts(filters_b)

    sampled_a = False
    sampled_b = False

    if len(docs_a) > MAX_DOCS_PER_CORPUS:
        random.seed(42)
        docs_a = random.sample(docs_a, MAX_DOCS_PER_CORPUS)
        sampled_a = True

    if len(docs_b) > MAX_DOCS_PER_CORPUS:
        random.seed(42)
        docs_b = random.sample(docs_b, MAX_DOCS_PER_CORPUS)
        sampled_b = True

    # توکن‌سازی و شمارش بسامد
    freq_a: Counter = Counter()
    for _, text in docs_a:
        freq_a.update(tokenize(text))

    freq_b: Counter = Counter()
    for _, text in docs_b:
        freq_b.update(tokenize(text))

    N_A = sum(freq_a.values())
    N_B = sum(freq_b.values())
    N = N_A + N_B

    if N == 0:
        return pd.DataFrame(), len(docs_a), len(docs_b), sampled_a, sampled_b

    # همه واژه‌ها با بسامد کافی — حذف stop words
    all_words = (
        set(w for w, f in freq_a.items() if f >= min_freq) |
        set(w for w, f in freq_b.items() if f >= min_freq)
    ) - stop_set

    records = []
    for word in all_words:
        O11 = freq_a.get(word, 0)
        O12 = freq_b.get(word, 0)
        total_word = O11 + O12
        if total_word < min_freq:
            continue

        E11 = total_word * N_A / N if N > 0 else 0
        E12 = total_word * N_B / N if N > 0 else 0

        def _safe_xlogx(o, e):
            if o > 0 and e > 0:
                return o * math.log(o / e)
            return 0.0

        ll = 2 * (_safe_xlogx(O11, E11) + _safe_xlogx(O12, E12))

        # علامت: مثبت = کلیدی در A، منفی = کلیدی در B
        rate_a = O11 / N_A if N_A > 0 else 0
        rate_b = O12 / N_B if N_B > 0 else 0
        sign = 1 if rate_a >= rate_b else -1
        keyness = ll * sign

        per_mil_a = round(O11 * 1_000_000 / N_A, 2) if N_A > 0 else 0
        per_mil_b = round(O12 * 1_000_000 / N_B, 2) if N_B > 0 else 0

        records.append({
            'word': word,
            'freq_A': O11,
            'freq_B': O12,
            'per_million_A': per_mil_a,
            'per_million_B': per_mil_b,
            'LL': round(ll, 4),
            'keyness': round(keyness, 4),
        })

    if not records:
        return pd.DataFrame(), len(docs_a), len(docs_b), sampled_a, sampled_b

    df = pd.DataFrame(records)
    df = df.sort_values('keyness', key=abs, ascending=False).reset_index(drop=True)
    return df, len(docs_a), len(docs_b), sampled_a, sampled_b


filters_a = (
    tuple(periods_a), yr1_a, yr2_a,
    kw_filter_a or '', tuple(tier_a)
)
filters_b = (
    tuple(periods_b), yr1_b, yr2_b,
    kw_filter_b or '', tuple(tier_b)
)

# تعیین مجموعه stop words بر اساس انتخاب کاربر
if filter_stopwords_ext:
    _active_stop_set = frozenset(FA_STOP_EXTENDED)
elif filter_stopwords:
    _active_stop_set = frozenset(FA_STOP)
else:
    _active_stop_set = frozenset()


with st.spinner("در حال محاسبه کلیدواژگی..."):
    result = compute_keyness(conn, filters_a, filters_b, min_freq, _active_stop_set)

df_key, n_docs_a, n_docs_b, sampled_a, sampled_b = result

if df_key is None or df_key.empty:
    st.warning("نتیجه‌ای یافت نشد. فیلترها را تنظیم کنید یا حداقل بسامد را کاهش دهید.")
    st.stop()

# هشدار در صورت نمونه‌گیری
if sampled_a:
    st.info(f"تعداد اسناد پیکره الف بیش از {MAX_DOCS_PER_CORPUS:,} بود — نمونه‌ای تصادفی استفاده شد.")
if sampled_b:
    st.info(f"تعداد اسناد پیکره ب بیش از {MAX_DOCS_PER_CORPUS:,} بود — نمونه‌ای تصادفی استفاده شد.")

# ─── آمار کلی ────────────────────────────────────────────────────────────────
st.divider()
ma1, ma2, ma3, ma4 = st.columns(4)
ma1.metric("اسناد پیکره الف", f"{n_docs_a:,}")
ma2.metric("اسناد پیکره ب", f"{n_docs_b:,}")
ma3.metric("واژه‌های کلیدی کل", f"{len(df_key):,}")
ma4.metric("حداقل بسامد فیلتر", str(min_freq))

# ─── جداسازی واژه‌های کلیدی ──────────────────────────────────────────────────
df_key_a = df_key[df_key['keyness'] > 0].head(20)
df_key_b = df_key[df_key['keyness'] < 0].copy()
df_key_b['keyness_abs'] = df_key_b['keyness'].abs()
df_key_b = df_key_b.sort_values('keyness_abs', ascending=False).head(20)

st.divider()
st.subheader("واژه‌های کلیدی به تفکیک پیکره")

col_chart_a, col_chart_b = st.columns(2)

with col_chart_a:
    st.markdown("#### واژه‌های کلیدی پیکره الف")
    if not df_key_a.empty:
        fig_a = go.Figure(go.Bar(
            x=df_key_a['LL'].tolist(),
            y=df_key_a['word'].tolist(),
            orientation='h',
            marker=dict(color='#e74c3c'),
            text=[f"LL={v:.1f}" for v in df_key_a['LL']],
            textposition='outside',
            hovertemplate=(
                '<b>%{y}</b><br>'
                'LL: %{x:.2f}<br>'
                'بسامد A: %{customdata[0]:,}<br>'
                'در میلیون A: %{customdata[1]:,.1f}<extra></extra>'
            ),
            customdata=list(zip(df_key_a['freq_A'], df_key_a['per_million_A']))
        ))
        fig_a.update_layout(
            font=dict(family='Vazirmatn', size=11),
            height=500,
            margin=dict(l=10, r=80, t=20, b=20),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(title='LL'),
            yaxis=dict(autorange='reversed'),
        )
        st.plotly_chart(fig_a, use_container_width=True)
    else:
        st.info("واژه‌ی کلیدی برای پیکره الف یافت نشد.")

with col_chart_b:
    st.markdown("#### واژه‌های کلیدی پیکره ب")
    if not df_key_b.empty:
        fig_b = go.Figure(go.Bar(
            x=df_key_b['keyness_abs'].tolist(),
            y=df_key_b['word'].tolist(),
            orientation='h',
            marker=dict(color='#2980b9'),
            text=[f"LL={v:.1f}" for v in df_key_b['LL']],
            textposition='outside',
            hovertemplate=(
                '<b>%{y}</b><br>'
                'LL: %{x:.2f}<br>'
                'بسامد B: %{customdata[0]:,}<br>'
                'در میلیون B: %{customdata[1]:,.1f}<extra></extra>'
            ),
            customdata=list(zip(df_key_b['freq_B'], df_key_b['per_million_B']))
        ))
        fig_b.update_layout(
            font=dict(family='Vazirmatn', size=11),
            height=500,
            margin=dict(l=10, r=80, t=20, b=20),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(title='LL'),
            yaxis=dict(autorange='reversed'),
        )
        st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.info("واژه‌ی کلیدی برای پیکره ب یافت نشد.")

# ─── جدول کامل ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("جدول کامل نتایج")

col_labels = {
    'word': 'واژه',
    'freq_A': 'بسامد الف',
    'freq_B': 'بسامد ب',
    'per_million_A': 'در میلیون الف',
    'per_million_B': 'در میلیون ب',
    'LL': 'LL',
    'keyness': 'کلیدواژگی',
}
df_display = df_key.rename(columns=col_labels)
st.dataframe(df_display, use_container_width=True, hide_index=True, height=450)

# دانلود CSV
csv_buf = io.StringIO()
df_key.to_csv(csv_buf, index=False, encoding='utf-8-sig')
st.download_button(
    "⬇ دانلود CSV",
    ('﻿' + csv_buf.getvalue()).encode('utf-8'),
    file_name="keyness_analysis.csv",
    mime="text/csv"
)

render_footer()
