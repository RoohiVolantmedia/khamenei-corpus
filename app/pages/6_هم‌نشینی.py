"""صفحه‌ی هم‌نشینی آماری (Collocation)"""
import sys
import re
import math
import io
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

from utils.corpus_index import (
    is_built, build_index, get_total_tokens, get_word_freq,
    tokenize, normalize_fa, DB_PATH, FA_STOP
)
from utils.theme import render_header, render_footer

render_header("هم‌نشینی آماری")
st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:15px;line-height:1.9;color:#033246">
  <p>
    <strong>هم‌نشینی (<bdi>Collocation</bdi>)</strong>
    واژه‌هایی را نشان می‌دهد که به‌طور آماری معنادار در کنار یک کلیدواژه ظاهر می‌شوند.
  </p>
  <p>
    سه معیار آماری موجود است:
    <strong><bdi>MI</bdi></strong> (اطلاعات متقابل)،
    <strong><bdi>LL</bdi></strong> (لگاریتم درستنمایی) و
    <strong><bdi>t-score</bdi></strong>.
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

# ─── بررسی جدول بسامد ────────────────────────────────────────────────────────
index_ready = is_built()

if not index_ready:
    st.warning(
        "جدول بسامد پیکره ساخته نشده است. "
        "برای محاسبه‌ی آماری هم‌نشینی باید یک‌بار این جدول ساخته شود (حدود ۵ دقیقه)."
    )
    if st.button("ساخت جدول بسامد (یک‌بار، ~۵ دقیقه)", type="primary"):
        progress_bar = st.progress(0, text="در حال پردازش...")
        status_text = st.empty()

        def _cb(done, total):
            pct = done / total if total > 0 else 0
            progress_bar.progress(pct, text=f"پردازش {done:,} از {total:,} سند...")
            status_text.text(f"{done:,} / {total:,}")

        with st.spinner("در حال ساخت جدول بسامد..."):
            result = build_index(progress_callback=_cb)

        progress_bar.progress(1.0, text="تمام شد!")
        st.success(
            f"جدول بسامد ساخته شد — "
            f"{result['total_docs']:,} سند، "
            f"{result['total_tokens']:,} توکن، "
            f"{result['unique_words']:,} واژه منحصربه‌فرد"
        )
        st.rerun()
    st.stop()
else:
    unique_count = 0
    try:
        _tmp = sqlite3.connect(DB_PATH)
        unique_count = _tmp.execute("SELECT COUNT(*) FROM word_freq").fetchone()[0]
        _tmp.close()
    except Exception:
        pass
    st.success(f"جدول بسامد آماده است — {unique_count:,} توکن منحصربه‌فرد")

# ─── تنظیمات ─────────────────────────────────────────────────────────────────
with st.expander("تنظیمات", expanded=True):
    c1, c2 = st.columns([2, 2])

    keyword = c1.text_input(
        "کلیدواژه *",
        placeholder="مثال: انقلاب",
        key="col_kw"
    )
    window_size = c1.selectbox(
        "پنجره (تعداد کلمه هر طرف)",
        [2, 3, 5, 8, 10],
        index=2,
        key="col_win"
    )
    max_col = c1.selectbox(
        "حداکثر هم‌نشین",
        [20, 50, 100],
        index=1,
        key="col_max"
    )
    stat_metric = c1.radio(
        "معیار آماری",
        ["MI", "LL", "t-score"],
        index=0,
        horizontal=True,
        key="col_metric"
    )

    METRIC_HELP = {
        "MI": {
            "icon": "🔍",
            "title": "MI — اطلاعات متقابل (Mutual Information)",
            "body": "می‌سنجد دو واژه چقدر **منحصراً** با هم ظاهر می‌شوند — بیش از آنچه تصادف پیش‌بینی می‌کند.",
            "use": "ترکیب‌های اصطلاحی و عبارات ثابت — مثل «دشمن قسم‌خورده»، «مقاومت اسلامی»",
            "limit": "به واژه‌های نادر حساس است. واژه‌ای که فقط ۳ بار آمده ممکن است MI بالایی داشته باشد.",
            "color": "#1091EC",
        },
        "LL": {
            "icon": "📊",
            "title": "LL — لگاریتم درستنمایی (Log-Likelihood / G²)",
            "body": "آزمون آماری: «آیا همرخدادی این دو واژه فراتر از شانس است؟» عدد بزرگ‌تر = ارتباط قوی‌تر.",
            "use": "قابل‌اعتمادترین معیار برای پیکره‌های بزرگ — **توصیه برای استناد علمی**",
            "limit": "واژه‌های پربسامد معمولی را بالاتر نشان می‌دهد؛ ترکیب‌های نادر ممکن است پنهان شوند.",
            "color": "#27ae60",
        },
        "t-score": {
            "icon": "📈",
            "title": "t-score",
            "body": "انحراف همرخدادی مشاهده‌شده از مقدار مورد انتظار را بر اساس واریانس می‌سنجد.",
            "use": "واژه‌های پربسامدی که **پیوسته** کنار کلیدواژه می‌آیند — مثل «ملت» کنار «ایران»",
            "limit": "واژه‌های پربسامد را بیش از حد برجسته می‌کند؛ نتایج ممکن است بدیهی به نظر برسند.",
            "color": "#e67e22",
        },
    }

    if stat_metric in METRIC_HELP:
        m = METRIC_HELP[stat_metric]
        st.html(f"""
<div dir="rtl" style="
    font-family:Vazirmatn,sans-serif;
    border-right: 4px solid {m['color']};
    background: {m['color']}11;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.8;
">
  <div style="font-weight:700;font-size:14px;color:{m['color']};margin-bottom:6px">
    {m['icon']} {m['title']}
  </div>
  <div style="color:#033246;margin-bottom:6px">{m['body']}</div>
  <div>✅ <strong>بهترین کاربرد:</strong> {m['use']}</div>
  <div>⚠️ <strong>محدودیت:</strong> {m['limit']}</div>
</div>
""")

    c3, c4 = c2.columns(2)
    yr1 = c3.number_input("از سال", 1356, 1404, 1356, step=1, key="col_y1")
    yr2 = c4.number_input("تا سال", 1356, 1404, 1404, step=1, key="col_y2")

    sel_tier = c2.multiselect(
        "نوع سند",
        ['tier1', 'tier2', 'tier3', 'tier4'],
        format_func=lambda x: {
            'tier1': 'tier1 — سخنرانی مستقیم',
            'tier2': 'tier2 — متن ویرایش‌شده',
            'tier3': 'tier3 — خلاصه / گزیده',
            'tier4': 'tier4 — گزارش راوی',
        }.get(x, x),
        key="col_tier"
    )

run_btn = st.button("🔍 محاسبه هم‌نشینی", type="primary", disabled=not (keyword or '').strip())

if not (keyword or '').strip():
    st.info("یک کلیدواژه وارد کنید و دکمه «محاسبه» را بزنید.")
    st.stop()

if not run_btn and 'col_results' not in st.session_state:
    st.stop()

kw = keyword.strip()
kw_norm = normalize_fa(kw)


# ─── محاسبه هم‌نشینی ─────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def compute_collocations(_conn, kw, window, yr1, yr2, sel_tier, max_col):
    """محاسبه هم‌نشین‌های آماری برای کلیدواژه داده‌شده"""
    kw_norm_local = normalize_fa(kw)

    # کوئری برای گرفتن اسناد حاوی کلیدواژه
    conds = [
        "date_persian BETWEEN ? AND ?",
        "full_text LIKE ?"
    ]
    params = [
        f"{int(yr1)}/01/01",
        f"{int(yr2)}/12/29",
        f'%{kw}%'
    ]

    if sel_tier:
        conds.append(f"analytical_tier IN ({','.join('?' * len(sel_tier))})")
        params.extend(sel_tier)

    where = "WHERE " + " AND ".join(conds)
    rows = _conn.execute(
        f"SELECT doc_id, full_text FROM documents {where}",
        params
    ).fetchall()

    # الگو برای یافتن کلیدواژه
    pat = re.compile(r'(?<!\w)' + re.escape(kw_norm_local) + r'(?!\w)')

    collocate_freq: Counter = Counter()
    kw_occurrence_count = 0
    docs_searched = len(rows)

    for row in rows:
        doc_id, full_text = row[0], row[1]
        if not full_text:
            continue
        text_norm = normalize_fa(full_text)
        tokens_all = tokenize(text_norm)

        # یافتن موقعیت توکن‌ها در متن نرمال‌شده برای استخراج پنجره
        # روش: کار با لیست توکن‌ها مستقیم و یافتن کلیدواژه در آن
        kw_token = kw_norm_local

        # جستجو برای کلیدواژه چندکلمه‌ای یا تکی
        kw_parts = kw_token.split()

        if len(kw_parts) == 1:
            # جستجوی توکن تکی در لیست توکن‌ها
            for i, tok in enumerate(tokens_all):
                if tok == kw_token or normalize_fa(tok) == kw_token:
                    kw_occurrence_count += 1
                    start = max(0, i - window)
                    end = min(len(tokens_all), i + window + 1)
                    ctx = tokens_all[start:i] + tokens_all[i + 1:end]
                    collocate_freq.update(ctx)
        else:
            # جستجوی چندکلمه‌ای در متن
            for m in pat.finditer(text_norm):
                kw_occurrence_count += 1
                # استخراج توکن‌های قبل و بعد بر اساس موقعیت کاراکتری
                start_char = m.start()
                end_char = m.end()
                before_text = text_norm[:start_char]
                after_text = text_norm[end_char:]
                before_tokens = tokenize(before_text)[-window:]
                after_tokens = tokenize(after_text)[:window]
                collocate_freq.update(before_tokens + after_tokens)

    if not collocate_freq:
        return pd.DataFrame()

    # فیلتر stop words — لایه‌ی امنیتی اضافه علاوه بر tokenize
    _stop_normalized = {normalize_fa(w).strip('‌') for w in FA_STOP}
    _all_stops = _stop_normalized
    collocate_freq = Counter({
        w: f for w, f in collocate_freq.items()
        if normalize_fa(w).strip('‌') not in _all_stops
    })

    # فیلتر: فقط هم‌نشین‌هایی با بسامد >= 3
    collocate_freq = Counter({w: f for w, f in collocate_freq.items() if f >= 3})

    if not collocate_freq:
        return pd.DataFrame()

    # جستجوی بسامد پس‌زمینه از word_freq
    all_words = list(collocate_freq.keys())
    bg_freqs = get_word_freq(all_words)

    # پارامترهای آماری
    N = get_total_tokens()
    if N == 0:
        return pd.DataFrame()

    f_K = kw_occurrence_count if kw_occurrence_count > 0 else 1

    records = []
    # ─── مهم: همه‌ی هم‌نشین‌ها محاسبه می‌شوند، نه فقط پربسامدترین‌ها
    # دلیل: MI برای کلمات نادر اما منحصربه‌فرد عدد بالایی دارد — اگر ابتدا
    # بر اساس بسامد فیلتر کنیم، این کلمات از دست می‌روند و MI = LL به نظر می‌رسد
    for word, obs_freq in collocate_freq.items():
        f_C = bg_freqs.get(word, (0, 0))[0]
        if f_C == 0:
            f_C = obs_freq  # حداقل بسامد مشاهده‌شده

        E11 = f_K * f_C / N if N > 0 else 0

        # MI
        if E11 > 0 and obs_freq > 0:
            mi = math.log2(obs_freq / E11)
        else:
            mi = 0.0

        # t-score
        if obs_freq > 0:
            t_score = (obs_freq - E11) / math.sqrt(obs_freq)
        else:
            t_score = 0.0

        # LL (G²): جدول ۲×۲ کامل
        O11 = obs_freq
        O12 = f_K - O11  # تعداد دفعاتی که کلید ظاهر شد ولی C نبود
        if O12 < 0:
            O12 = 0
        O21 = f_C - O11  # C در غیر از پنجره کلید
        if O21 < 0:
            O21 = 0
        O22 = N - O11 - O12 - O21
        if O22 < 0:
            O22 = 1

        R1 = O11 + O12
        R2 = O21 + O22
        C1 = O11 + O21
        C2 = O12 + O22
        N_total = R1 + R2

        def _ll_cell(o, e):
            if o > 0 and e > 0:
                return o * math.log(o / e)
            return 0.0

        E11_ll = R1 * C1 / N_total if N_total > 0 else 0
        E12_ll = R1 * C2 / N_total if N_total > 0 else 0
        E21_ll = R2 * C1 / N_total if N_total > 0 else 0
        E22_ll = R2 * C2 / N_total if N_total > 0 else 0

        ll = 2 * (
            _ll_cell(O11, E11_ll) +
            _ll_cell(O12, E12_ll) +
            _ll_cell(O21, E21_ll) +
            _ll_cell(O22, E22_ll)
        )

        records.append({
            'collocate': word,
            'freq': obs_freq,
            'MI': round(mi, 4),
            't_score': round(t_score, 4),
            'LL': round(ll, 4),
            'f_C': f_C,
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    return df


# ─── اجرا ─────────────────────────────────────────────────────────────────────
with st.spinner("در حال محاسبه هم‌نشینی..."):
    df_col = compute_collocations(
        conn, kw, window_size,
        yr1, yr2, tuple(sel_tier), max_col
    )

if df_col is None or df_col.empty:
    st.warning(f"هم‌نشینی معناداری برای «{kw}» با این فیلترها یافت نشد.")
    st.stop()

# مرتب‌سازی بر اساس معیار انتخابی
sort_col = {'MI': 'MI', 'LL': 'LL', 't-score': 't_score'}.get(stat_metric, 'MI')
df_sorted = df_col.sort_values(sort_col, ascending=False).head(max_col).reset_index(drop=True)

# ─── نمایش آمار ──────────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3)
m1.metric("هم‌نشین‌های یافت‌شده", f"{len(df_sorted):,}")
m2.metric("معیار مرتب‌سازی", stat_metric)
m3.metric("پنجره", f"±{window_size} واژه")

# ─── جدول نتایج ──────────────────────────────────────────────────────────────
st.subheader(f"هم‌نشین‌های «{kw}»")

# نمایش تفاوت معیارها — سه ستون، هر کدام top-5 یک معیار
_top5_mi = df_col.sort_values('MI', ascending=False).head(5)['collocate'].tolist()
_top5_ll = df_col.sort_values('LL', ascending=False).head(5)['collocate'].tolist()
_top5_ts = df_col.sort_values('t_score', ascending=False).head(5)['collocate'].tolist()

# فقط نمایش اگر سه لیست متفاوت هستند
if _top5_mi != _top5_ll or _top5_mi != _top5_ts:
    with st.expander("📊 مقایسه‌ی سه معیار — چرا نتایج فرق می‌کنند؟", expanded=False):
        st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:12px;color:#5a7a8a;margin-bottom:8px;line-height:1.7">
هر معیار یک «سوال» متفاوت می‌پرسد. جدول زیر ۵ هم‌نشین برتر هر معیار را نشان می‌دهد.
</div>
""")
        _cmp_c1, _cmp_c2, _cmp_c3 = st.columns(3)
        with _cmp_c1:
            st.html(f"""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif">
  <div style="font-weight:700;color:#1091EC;margin-bottom:6px;font-size:13px">🔍 MI — منحصربه‌فردترین</div>
  {"".join(f'<div style="padding:3px 0;border-bottom:1px solid #eee;font-size:13px">{i+1}. {w}</div>' for i, w in enumerate(_top5_mi))}
  <div style="font-size:11px;color:#888;margin-top:6px">کلمه‌هایی که تقریباً فقط با «{kw}» ظاهر می‌شوند</div>
</div>""")
        with _cmp_c2:
            st.html(f"""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif">
  <div style="font-weight:700;color:#27ae60;margin-bottom:6px;font-size:13px">📊 LL — آماری‌ترین</div>
  {"".join(f'<div style="padding:3px 0;border-bottom:1px solid #eee;font-size:13px">{i+1}. {w}</div>' for i, w in enumerate(_top5_ll))}
  <div style="font-size:11px;color:#888;margin-top:6px">قابل‌اعتمادترین — برای استناد علمی</div>
</div>""")
        with _cmp_c3:
            st.html(f"""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif">
  <div style="font-weight:700;color:#e67e22;margin-bottom:6px;font-size:13px">📈 t-score — پربسامدترین</div>
  {"".join(f'<div style="padding:3px 0;border-bottom:1px solid #eee;font-size:13px">{i+1}. {w}</div>' for i, w in enumerate(_top5_ts))}
  <div style="font-size:11px;color:#888;margin-top:6px">کلمه‌هایی که پیوسته کنار «{kw}» می‌آیند</div>
</div>""")

col_labels = {
    'collocate': 'هم‌نشین',
    'freq': 'بسامد مشترک',
    'MI': 'MI',
    't_score': 't-score',
    'LL': 'LL',
    'f_C': 'بسامد کل',
}
df_display = df_sorted.rename(columns=col_labels)
st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)

# دانلود CSV
csv_buf = io.StringIO()
df_sorted.to_csv(csv_buf, index=False, encoding='utf-8-sig')
st.download_button(
    "⬇ دانلود CSV",
    ('﻿' + csv_buf.getvalue()).encode('utf-8'),
    file_name=f"collocation_{kw[:20]}.csv",
    mime="text/csv"
)

st.divider()


# ─── نمودار شبکه‌ای ───────────────────────────────────────────────────────────
def draw_network(df: pd.DataFrame, kw: str, metric: str, top_n: int = 25):
    """رسم شبکه‌ی هم‌نشینی با چیدمان شعاعی"""
    metric_col = {'MI': 'MI', 'LL': 'LL', 't-score': 't_score'}.get(metric, 'MI')
    df_net = df.sort_values(metric_col, ascending=False).head(top_n).reset_index(drop=True)

    if df_net.empty:
        return None

    n = len(df_net)
    angles = [2 * math.pi * i / n for i in range(n)]

    # مختصات گره‌ها
    node_x = [0.0] + [math.cos(a) for a in angles]
    node_y = [0.0] + [math.sin(a) for a in angles]

    # اندازه گره‌ها
    max_freq = df_net['freq'].max() if df_net['freq'].max() > 0 else 1
    node_sizes = [30] + [
        10 + 25 * (df_net.loc[i, 'freq'] / max_freq)
        for i in range(n)
    ]

    # رنگ گره‌ها بر اساس معیار (آبی‌تر = بالاتر)
    scores = df_net[metric_col].tolist()
    min_s = min(scores) if scores else 0
    max_s = max(scores) if scores else 1
    rng = max_s - min_s if max_s != min_s else 1

    def score_color(s):
        t = (s - min_s) / rng
        r = int(30 + (1 - t) * 100)
        g = int(100 + t * 100)
        b = int(200 + t * 55)
        return f'rgb({r},{g},{b})'

    node_colors = ['#e74c3c'] + [score_color(s) for s in scores]
    node_labels = [kw] + df_net['collocate'].tolist()

    # لبه‌ها (خطوط اتصال)
    edge_traces = []
    metric_vals = df_net[metric_col].tolist()
    max_mv = max(metric_vals) if max(metric_vals) > 0 else 1
    for i in range(n):
        width = 0.5 + 3.0 * (metric_vals[i] / max_mv) if max_mv > 0 else 1
        edge_traces.append(go.Scatter(
            x=[0, node_x[i + 1], None],
            y=[0, node_y[i + 1], None],
            mode='lines',
            line=dict(width=width, color='rgba(150,150,150,0.4)'),
            hoverinfo='none',
            showlegend=False
        ))

    # hover text
    hover_texts = [f'<b>{kw}</b><br>کلیدواژه مرکزی']
    for i in range(n):
        row = df_net.iloc[i]
        hover_texts.append(
            f"<b>{row['collocate']}</b><br>"
            f"بسامد: {row['freq']:,}<br>"
            f"MI: {row['MI']:.3f}<br>"
            f"LL: {row['LL']:.3f}<br>"
            f"t-score: {row['t_score']:.3f}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_labels,
        textposition='middle center',
        textfont=dict(family='Vazirmatn', size=10, color='#222'),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=1, color='white'),
        ),
        hovertext=hover_texts,
        hoverinfo='text',
        showlegend=False
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title=dict(
            text=f"شبکه‌ی هم‌نشینی «{kw}» — بر اساس {metric}",
            font=dict(family='Vazirmatn', size=14)
        ),
        xaxis=dict(visible=False, range=[-1.3, 1.3]),
        yaxis=dict(visible=False, range=[-1.3, 1.3]),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=550,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family='Vazirmatn'),
    )
    return fig


st.subheader(f"نمودار شبکه‌ی هم‌نشینی (برترین ۲۵)")
net_fig = draw_network(df_sorted, kw, stat_metric, top_n=25)
if net_fig:
    st.plotly_chart(net_fig, use_container_width=True)
else:
    st.info("داده کافی برای رسم نمودار وجود ندارد.")

render_footer()
