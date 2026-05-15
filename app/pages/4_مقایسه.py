"""صفحه‌ی مقایسه کلیدواژه‌ها"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.theme import render_header, render_footer

# مسیر دیتابیس — محلی یا سرور
def _resolve_db():
    from pathlib import Path as _P
    local = _P(__file__).resolve().parent.parent.parent / "database.db"
    if local.exists():
        return str(local)
    tmp = _P("/tmp/khamenei_db.db")
    if tmp.exists():
        return str(tmp)
    from utils.db import _get_db_path
    return str(_get_db_path())
DB_PATH = _resolve_db()

render_header("مقایسه کلیدواژه‌ها")

@st.cache_resource
def get_db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL"); c.row_factory = sqlite3.Row; return c
conn = get_db()

FONT = dict(family="Vazirmatn, sans-serif", size=12)
BG   = dict(plot_bgcolor='#fff', paper_bgcolor='#fff')
COLORS = ['#E91E63','#2196F3','#4CAF50','#FF9800','#9C27B0','#00BCD4']

PERIOD_FA = {
    'pre_revolution':  'قبل از انقلاب',
    'early_revolution':'اوایل انقلاب',
    'presidency':      'دوران ریاست جمهوری',
    'hashemi':         'رفسنجانی',
    'khatami':         'خاتمی',
    'ahmadinejad':     'احمدی‌نژاد',
    'rouhani':         'روحانی',
    'raisi_to_death':  'رئیسی تا مرگ',
}

# ─── ورودی کلیدواژه‌ها ───────────────────────────────────────────────────────
st.subheader("کلیدواژه‌ها")
col_kw = st.columns(3)
kw_inputs = []
defaults = ['آمریکا', 'اسرائیل', 'استکبار', '', '', '']
for i, col in enumerate(col_kw):
    v = col.text_input(f"کلیدواژه {i+1}", value=defaults[i], key=f"kw{i}")
    if v.strip(): kw_inputs.append(v.strip())
col_kw2 = st.columns(3)
for i, col in enumerate(col_kw2):
    v = col.text_input(f"کلیدواژه {i+4}", value=defaults[i+3], key=f"kw{i+3}")
    if v.strip(): kw_inputs.append(v.strip())

if not kw_inputs:
    st.warning("حداقل یک کلیدواژه وارد کنید."); st.stop()

# ─── فیلترها ─────────────────────────────────────────────────────────────────
with st.expander("فیلترهای مقایسه", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    y1 = fc1.number_input("از سال", 1356, 1404, 1356, step=1, key='cy1')
    y2 = fc1.number_input("تا سال", 1356, 1404, 1404, step=1, key='cy2')
    sel_tier = fc2.multiselect("نوع سند", ['tier1','tier2','tier3','tier4'],
                                format_func=lambda x: {'tier1':'سخنرانی مستقیم','tier2':'متن ویرایش‌شده',
                                                        'tier3':'خلاصه','tier4':'گزارش راوی'}.get(x,x))
    sel_src  = fc3.multiselect("منبع", ['speech','speech_supplement','message','decree'])
    normalize = fc2.checkbox("یکسان‌سازی حروف", value=True)

def norm(t):
    import re
    t = re.sub(r'[ً-ٰ]','',t)
    return t.replace('ي','ی').replace('ك','ک').replace('ة','ه').replace('‌',' ')

def build_base_conds():
    conds, params = [], []
    if sel_tier:
        conds.append(f"analytical_tier IN ({','.join('?'*len(sel_tier))})"); params.extend(sel_tier)
    if sel_src:
        conds.append(f"content_source IN ({','.join('?'*len(sel_src))})"); params.extend(sel_src)
    conds.append("date_persian BETWEEN ? AND ?"); params.extend([f"{y1}/01/01", f"{y2}/12/29"])
    return conds, params

def dl_chart(fig, name, df=None):
    c1, c2 = st.columns(2)
    if df is not None:
        c1.download_button("CSV", df.to_csv(index=False).encode('utf-8-sig'),
                           file_name=f"cmp_{name}.csv", key=f"dlc_{name}")
    c2.download_button("JSON", fig.to_json().encode(),
                       file_name=f"cmp_{name}.json", key=f"dlj_{name}")
    st.caption("PNG: روی نمودار hover کنید → دکمه دوربین")

st.divider()

# ─── ۱. روند زمانی ──────────────────────────────────────────────────────────
st.subheader("۱. روند فراوانی در طول زمان")
norm_opt = st.checkbox("نرمال‌سازی (تعداد به ازای هر ۱۰۰ سند آن سال)", value=False, key="norm_trend")

base_conds, base_params = build_base_conds()
base_where = ("AND " + " AND ".join(base_conds)) if base_conds else ""

# تعداد کل اسناد به تفکیک سال (برای نرمال‌سازی)
total_by_year = {}
if norm_opt:
    yr_totals = conn.execute(f"""
        SELECT substr(date_persian,1,4) y, COUNT(*) n FROM documents
        WHERE date_persian GLOB '1[34][0-9][0-9]/*' {base_where}
        GROUP BY y
    """, base_params).fetchall()
    total_by_year = {r[0]: r[1] for r in yr_totals}

fig_trend = go.Figure()
trend_data = {}
for i, kw in enumerate(kw_inputs):
    kw_n = norm(kw) if normalize else kw
    extra_conds = list(base_conds)
    extra_params = list(base_params)
    extra_conds.append("full_text LIKE ?"); extra_params.append(f'%{kw_n}%')
    extra_where = "AND " + " AND ".join(extra_conds)
    rows = conn.execute(f"""
        SELECT substr(date_persian,1,4) y, COUNT(*) n FROM documents
        WHERE date_persian GLOB '1[34][0-9][0-9]/*' {extra_where}
        GROUP BY y ORDER BY y
    """, extra_params).fetchall()
    if rows:
        yrs  = [r[0] for r in rows]
        cnts = [r[1] for r in rows]
        if norm_opt:
            cnts = [round(c/total_by_year.get(y,1)*100, 2) for c,y in zip(cnts, yrs)]
        trend_data[kw] = dict(zip(yrs, cnts))
        fig_trend.add_trace(go.Scatter(x=yrs, y=cnts, mode='lines+markers', name=kw,
                                       line=dict(color=COLORS[i%6], width=2), marker=dict(size=6)))

y_title = "درصد از کل اسناد سال" if norm_opt else "تعداد سند"
fig_trend.update_layout(font=FONT, **BG, height=420, margin=dict(l=60,r=20,t=50,b=60),
                         xaxis_title='سال شمسی', yaxis_title=y_title,
                         hovermode='x unified', title='روند فراوانی')
st.plotly_chart(fig_trend, use_container_width=True)
if trend_data:
    all_years = sorted(set(y for d in trend_data.values() for y in d))
    df_tr = pd.DataFrame({'سال': all_years})
    for kw, yd in trend_data.items():
        df_tr[kw] = df_tr['سال'].map(yd).fillna(0)
    dl_chart(fig_trend, 'trend', df_tr)
st.divider()

# ─── ۲. مجموع فراوانی ───────────────────────────────────────────────────────
st.subheader("۲. مجموع فراوانی")
total_counts = {}
for kw in kw_inputs:
    kw_n = norm(kw) if normalize else kw
    extra_conds = list(base_conds) + ["full_text LIKE ?"]
    extra_params = list(base_params) + [f'%{kw_n}%']
    n = conn.execute(f"""
        SELECT COUNT(*) FROM documents
        WHERE date_persian BETWEEN ? AND ? {'AND ' + ' AND '.join(base_conds[2:]) if base_conds[2:] else ''}
        AND full_text LIKE ?
    """, [f"{y1}/01/01", f"{y2}/12/29"] + ([p for p in base_params[2:]] if base_params[2:] else []) + [f'%{kw_n}%']).fetchone()[0]
    total_counts[kw] = n

df_tot = pd.DataFrame(list(total_counts.items()), columns=['کلیدواژه','تعداد'])
df_tot = df_tot.sort_values('تعداد', ascending=True)
fig_tot = px.bar(df_tot, x='تعداد', y='کلیدواژه', orientation='h',
                 color='کلیدواژه', color_discrete_sequence=COLORS,
                 text='تعداد', title='مجموع اسناد حاوی هر کلیدواژه')
fig_tot.update_traces(textposition='outside')
fig_tot.update_layout(font=FONT, **BG, height=max(250, len(kw_inputs)*60+80),
                       margin=dict(l=150,r=80,t=50,b=20), showlegend=False)
st.plotly_chart(fig_tot, use_container_width=True)
dl_chart(fig_tot, 'totals', df_tot)
st.divider()

# ─── ۳. توزیع بر دوره ───────────────────────────────────────────────────────
st.subheader("۳. توزیع بر دوره تاریخی")
period_data = []
for kw in kw_inputs:
    kw_n = norm(kw) if normalize else kw
    rows = conn.execute(f"""
        SELECT period_label, COUNT(*) n FROM documents
        WHERE period_label IS NOT NULL AND full_text LIKE ?
        AND date_persian BETWEEN ? AND ?
        GROUP BY period_label ORDER BY MIN(date_persian)
    """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
    for r in rows:
        period_data.append({'کلیدواژه': kw,
                            'دوره': PERIOD_FA.get(r[0], r[0]),
                            'تعداد': r[1]})

if period_data:
    df_per = pd.DataFrame(period_data)
    fig_per = px.bar(df_per, x='دوره', y='تعداد', color='کلیدواژه',
                     barmode='group', color_discrete_sequence=COLORS,
                     title='توزیع بر دوره تاریخی')
    fig_per.update_layout(font=FONT, **BG, height=420,
                           margin=dict(l=60,r=20,t=50,b=120),
                           xaxis_tickangle=-30)
    st.plotly_chart(fig_per, use_container_width=True)
    dl_chart(fig_per, 'by_period', df_per)
st.divider()

# ─── ۴. توزیع بر لحن ────────────────────────────────────────────────────────
st.subheader("۴. توزیع بر لحن")
tone_data = []
for kw in kw_inputs:
    kw_n = norm(kw) if normalize else kw
    rows = conn.execute(f"""
        SELECT jt.value, COUNT(*) n
        FROM documents d
        JOIN doc_tags t ON d.doc_id=t.doc_id
        JOIN json_each(t.tag_tone) jt
        WHERE d.full_text LIKE ? AND jt.value != ''
        AND d.date_persian BETWEEN ? AND ?
        GROUP BY jt.value ORDER BY n DESC LIMIT 8
    """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
    for r in rows:
        tone_data.append({'کلیدواژه': kw, 'لحن': r[0], 'تعداد': r[1]})

if tone_data:
    df_tone = pd.DataFrame(tone_data)
    fig_tone = px.bar(df_tone, x='لحن', y='تعداد', color='کلیدواژه',
                      barmode='group', color_discrete_sequence=COLORS,
                      title='توزیع بر لحن')
    fig_tone.update_layout(font=FONT, **BG, height=420,
                            margin=dict(l=60,r=20,t=50,b=120),
                            xaxis_tickangle=-30)
    st.plotly_chart(fig_tone, use_container_width=True)
    dl_chart(fig_tone, 'by_tone', df_tone)
st.divider()

# ─── ۵. توزیع بر موضوع ──────────────────────────────────────────────────────
st.subheader("۵. توزیع بر موضوع")
topic_data = []
for kw in kw_inputs:
    kw_n = norm(kw) if normalize else kw
    rows = conn.execute(f"""
        SELECT jt.value, COUNT(*) n
        FROM documents d
        JOIN doc_tags t ON d.doc_id=t.doc_id
        JOIN json_each(t.tag_topics) jt
        WHERE d.full_text LIKE ? AND jt.value NOT IN ('سایر','')
        AND d.date_persian BETWEEN ? AND ?
        GROUP BY jt.value ORDER BY n DESC LIMIT 10
    """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
    for r in rows:
        topic_data.append({'کلیدواژه': kw, 'موضوع': r[0], 'تعداد': r[1]})

if topic_data:
    df_top = pd.DataFrame(topic_data)
    fig_top = px.bar(df_top, x='موضوع', y='تعداد', color='کلیدواژه',
                     barmode='group', color_discrete_sequence=COLORS,
                     title='توزیع بر موضوع')
    fig_top.update_layout(font=FONT, **BG, height=450,
                           margin=dict(l=60,r=20,t=50,b=150),
                           xaxis_tickangle=-35)
    st.plotly_chart(fig_top, use_container_width=True)
    dl_chart(fig_top, 'by_topic', df_top)
st.divider()

# ─── ۶. نمودار پای — سهم کلیدواژه‌ها از کل ────────────────────────────────
st.subheader("۶. نمودار پای — سهم نسبی کلیدواژه‌ها")
if total_counts:
    df_pie = pd.DataFrame(list(total_counts.items()), columns=['کلیدواژه','تعداد'])
    df_pie = df_pie[df_pie['تعداد'] > 0]
    if not df_pie.empty:
        fig_pie = px.pie(df_pie, values='تعداد', names='کلیدواژه',
                         color_discrete_sequence=COLORS,
                         title='سهم نسبی هر کلیدواژه از کل اسناد فیلترشده')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(font=FONT, **BG, height=420, margin=dict(l=20,r=20,t=60,b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        dl_chart(fig_pie, 'pie_share', df_pie)
st.divider()

# ─── ۷. نمودار پای دوره — هر کلیدواژه جداگانه ──────────────────────────────
st.subheader("۷. توزیع دوره‌ای هر کلیدواژه (پای جداگانه)")
if kw_inputs:
    pie_cols = st.columns(min(len(kw_inputs), 3))
    for idx, kw in enumerate(kw_inputs):
        kw_n = norm(kw) if normalize else kw
        rows_p = conn.execute(f"""
            SELECT period_label, COUNT(*) n FROM documents
            WHERE period_label IS NOT NULL AND full_text LIKE ?
            AND date_persian BETWEEN ? AND ?
            GROUP BY period_label ORDER BY MIN(date_persian)
        """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
        if rows_p:
            df_p = pd.DataFrame(rows_p, columns=['دوره_en','تعداد'])
            df_p['دوره'] = df_p['دوره_en'].map(PERIOD_FA).fillna(df_p['دوره_en'])
            fig_p = px.pie(df_p, values='تعداد', names='دوره',
                           title=f'«{kw}»',
                           color_discrete_sequence=px.colors.qualitative.Set2)
            fig_p.update_traces(textposition='inside', textinfo='percent+label')
            fig_p.update_layout(font=FONT, **BG, height=360,
                                 margin=dict(l=10,r=10,t=50,b=10),
                                 showlegend=False)
            pie_cols[idx % 3].plotly_chart(fig_p, use_container_width=True)
st.divider()

# ─── ۸. ابر کلمات مقایسه‌ای ─────────────────────────────────────────────────
st.subheader("۸. ابر کلمات مقایسه‌ای")
st.caption("برای هر کلیدواژه: فراوانی تگ‌های موضوع، منطقه، لحن و مخاطب در اسناد مرتبط")

cmp_dims = st.multiselect(
    "ابعاد تگ برای ابر کلمات",
    ['موضوع','منطقه','مخاطب','لحن','ژانر','مناسبت'],
    default=['موضوع','منطقه','لحن'],
    key='cmp_wc_dims'
)

if st.button("ساخت ابر کلمات", key="btn_wc_cmp"):
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            _reshape = lambda s: get_display(arabic_reshaper.reshape(s))
        except ImportError:
            _reshape = lambda s: s

        DIM_MAP = {
            'موضوع':  ('json',   'tg.tag_topics'),
            'منطقه':  ('json',   'tg.tag_regions'),
            'مخاطب':  ('json',   'tg.tag_audience'),
            'لحن':    ('json',   'tg.tag_tone'),
            'ژانر':   ('single', 'tg.tag_form_genre'),
            'مناسبت': ('single', 'tg.tag_occasion'),
        }
        IGNORE = {'سایر', '', 'None', 'null'}

        font_path = str(Path(__file__).parent.parent / "assets" / "Vazirmatn.ttf")
        if not Path(font_path).exists():
            font_path = None

        n_kw = len(kw_inputs)
        ncols = min(n_kw, 3)
        nrows = (n_kw + ncols - 1) // ncols
        wc_fig, axes = plt.subplots(nrows, ncols, figsize=(6*ncols, 4*nrows))
        axes_flat = axes.flat if hasattr(axes, 'flat') else [axes]

        for ax, kw in zip(axes_flat, kw_inputs):
            kw_n = norm(kw) if normalize else kw
            freq: dict[str, int] = {}
            for dim in (cmp_dims or ['موضوع','منطقه','لحن']):
                kind, col = DIM_MAP[dim]
                if kind == 'json':
                    rows_t = conn.execute(f"""
                        SELECT jt.value, COUNT(*) n
                        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
                        JOIN json_each({col}) jt
                        WHERE d.full_text LIKE ?
                        AND d.date_persian BETWEEN ? AND ?
                        AND jt.value NOT IN ('سایر','','None')
                        GROUP BY jt.value
                    """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
                else:
                    rows_t = conn.execute(f"""
                        SELECT {col}, COUNT(*) n
                        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
                        WHERE d.full_text LIKE ?
                        AND d.date_persian BETWEEN ? AND ?
                        AND {col} IS NOT NULL AND {col} NOT IN ('سایر','','None')
                        GROUP BY {col}
                    """, [f'%{kw_n}%', f"{y1}/01/01", f"{y2}/12/29"]).fetchall()
                for val, cnt in rows_t:
                    if val and val not in IGNORE:
                        freq[val] = freq.get(val, 0) + cnt

            if freq:
                freq_r = {_reshape(k): v for k, v in freq.items()}
                wc = WordCloud(
                    font_path=font_path, width=600, height=300,
                    background_color='white', max_words=80,
                    colormap='Reds', prefer_horizontal=0.85,
                ).generate_from_frequencies(freq_r)
                ax.imshow(wc, interpolation='bilinear')
            else:
                ax.text(0.5, 0.5, 'داده‌ای یافت نشد', ha='center', va='center',
                        transform=ax.transAxes, fontsize=12)
            ax.set_title(kw, fontsize=13)
            ax.axis('off')

        # حذف محورهای اضافی
        for ax in list(axes_flat)[n_kw:]:
            ax.axis('off')

        plt.tight_layout()
        st.pyplot(wc_fig)
        plt.close(wc_fig)
    except ImportError:
        st.error("کتابخانه wordcloud نصب نشده. دستور: pip install wordcloud matplotlib")

render_footer()
