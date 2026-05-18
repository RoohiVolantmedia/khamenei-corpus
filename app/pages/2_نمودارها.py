"""صفحه‌ی نمودارها"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import sqlite3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
from utils.theme import render_header, render_footer

# مسیر دیتابیس — محلی یا سرور
def _resolve_db():
    from pathlib import Path as _P
    local = _P(__file__).resolve().parent.parent.parent / "database.db"
    if local.exists():
        return str(local)
    from utils.db import _get_db_path
    return str(_get_db_path())
DB_PATH = _resolve_db()

render_header("نمودارها و تحلیل بصری")

@st.cache_resource
def get_db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL"); c.row_factory = sqlite3.Row; return c
conn = get_db()

FONT = dict(family="Vazirmatn, sans-serif", size=12)
BG   = dict(plot_bgcolor='#fff', paper_bgcolor='#fff')
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

def dl(fig, name, df_csv=None):
    c1, c2 = st.columns(2)
    if df_csv is not None:
        c1.download_button("دانلود CSV", df_csv.to_csv(index=False).encode('utf-8-sig'),
                           file_name=f"{name}.csv", key=f"csv_{name}")
    c2.download_button("دانلود JSON", fig.to_json().encode(),
                       file_name=f"{name}.json", mime="application/json", key=f"dl_{name}")
    st.caption("PNG: روی نمودار hover کنید → دکمه دوربین")

def goto_search(y1=None, y2=None, kw=None, period=None,
                genre=None, tone=None, region=None):
    if y1:     st.session_state['nav_y1']    = y1
    if y2:     st.session_state['nav_y2']    = y2
    if kw:     st.session_state['nav_kw']    = kw
    if period: st.session_state['nav_period']= period
    if genre:  st.session_state['nav_genre'] = genre
    if tone:   st.session_state['nav_tone']  = tone
    if region: st.session_state['nav_region']= region
    st.switch_page("pages/1_جستجو.py")

# ─── فیلتر جهانی ─────────────────────────────────────────────────────────────
st.subheader("فیلتر جهانی")
gcol1, gcol2 = st.columns([2, 1])
global_kw = gcol1.text_input("کلیدواژه (اختیاری — روی همه نمودارها اعمال می‌شود)",
                              placeholder="مثال: آمریکا", key="global_kw").strip()
kw_cond   = "AND d.full_text LIKE ?" if global_kw else ""
kw_param  = (f"%{global_kw}%",) if global_kw else ()
kw_cond_s = "AND full_text LIKE ?" if global_kw else ""

if global_kw:
    total_kw = conn.execute(
        f"SELECT COUNT(*) FROM documents WHERE full_text LIKE ?", (f"%{global_kw}%",)
    ).fetchone()[0]
    gcol2.metric("تعداد اسناد حاوی کلیدواژه", f"{total_kw:,}")

st.divider()

# ─── ۱. توزیع سالانه ─────────────────────────────────────────────────────────
st.subheader("۱. توزیع سالانه کل پیکره")
st.caption("روی هر میله کلیک کنید تا خلاصه آماری آن سال نمایش داده شود")
tier_sel = st.selectbox(
    "فیلتر نوع سند",
    [('همه','همه (کل پیکره)'),('tier1','tier1 — سخنرانی مستقیم'),
     ('tier2','tier2 — متن ویرایش‌شده'),('tier3','tier3 — خلاصه'),('tier4','tier4 — گزارش راوی')],
    format_func=lambda x: x[1], key='t1')
where_t = "" if tier_sel[0]=='همه' else f"AND analytical_tier='{tier_sel[0]}'"
yr_rows = conn.execute(f"""
    SELECT substr(date_persian,1,4) y, COUNT(*) n FROM documents
    WHERE date_persian GLOB '1[34][0-9][0-9]/*' {where_t} {kw_cond_s}
    GROUP BY y HAVING CAST(y AS INTEGER) BETWEEN 1356 AND 1405 ORDER BY y
""", kw_param).fetchall()
if yr_rows:
    df_yr = pd.DataFrame(yr_rows, columns=['سال','تعداد'])
    fig_yr = px.bar(df_yr, x='سال', y='تعداد', color_discrete_sequence=['#E91E63'])
    fig_yr.update_layout(font=FONT, **BG, height=320, margin=dict(l=40,r=20,t=40,b=60),
                         xaxis=dict(range=['1356', '1406'], tickangle=-45))
    event_yr = st.plotly_chart(fig_yr, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_yr")
    dl(fig_yr, 'yearly', df_yr)
    if event_yr and hasattr(event_yr, 'selection') and event_yr.selection.get('points'):
        pt = event_yr.selection['points'][0]
        yr_sel = str(pt.get('x') or pt.get('label') or '')
        if yr_sel:
            goto_search(y1=yr_sel, y2=yr_sel, kw=global_kw or None)
st.divider()

# ─── ۲. توزیع بر دوره ─────────────────────────────────────────────────────────
st.subheader("۲. توزیع بر دوره‌های تاریخی")
st.caption("روی هر نوار کلیک کنید تا آمار آن دوره نمایش داده شود")
pr_rows = conn.execute(f"""
    SELECT d.period_label p, COUNT(*) n FROM documents d
    WHERE d.period_label IS NOT NULL {kw_cond}
    GROUP BY p ORDER BY MIN(d.date_persian)
""", kw_param).fetchall()
if pr_rows:
    df_pr = pd.DataFrame(pr_rows, columns=['دوره_en','تعداد'])
    df_pr['دوره'] = df_pr['دوره_en'].map(PERIOD_FA).fillna(df_pr['دوره_en'])
    fig_pr = px.bar(df_pr, x='تعداد', y='دوره', orientation='h',
                 color='تعداد', color_continuous_scale='Reds', text='تعداد')
    fig_pr.update_traces(textposition='outside')
    fig_pr.update_layout(font=FONT, **BG, height=340,
                      margin=dict(l=200,r=60,t=40,b=40), yaxis=dict(autorange='reversed'))
    event_pr = st.plotly_chart(fig_pr, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_pr")
    dl(fig_pr, 'periods', df_pr[['دوره','تعداد']])
    if event_pr and hasattr(event_pr, 'selection') and event_pr.selection.get('points'):
        pt = event_pr.selection['points'][0]
        period_fa = pt.get('y') or pt.get('label') or ''
        if period_fa:
            period_en_rows = df_pr.loc[df_pr['دوره']==period_fa, 'دوره_en'].values
            period_en = period_en_rows[0] if len(period_en_rows) else None
            goto_search(period=period_en, kw=global_kw or None)
st.divider()

# ─── ۳. توزیع بر ژانر ─────────────────────────────────────────────────────────
st.subheader("۳. توزیع بر ژانر")
if global_kw:
    gn_rows = conn.execute(f"""
        SELECT t.tag_form_genre g, COUNT(*) n FROM doc_tags t
        JOIN documents d ON d.doc_id=t.doc_id
        WHERE t.tag_form_genre IS NOT NULL {kw_cond}
        GROUP BY g ORDER BY n DESC LIMIT 20
    """, kw_param).fetchall()
else:
    gn_rows = conn.execute("""
        SELECT tag_form_genre g, COUNT(*) n FROM doc_tags
        WHERE tag_form_genre IS NOT NULL GROUP BY g ORDER BY n DESC LIMIT 20
    """).fetchall()
if gn_rows:
    df_gn = pd.DataFrame(gn_rows, columns=['ژانر','تعداد'])
    df_gn = df_gn.sort_values('تعداد', ascending=True)
    fig_gn = px.bar(df_gn, x='تعداد', y='ژانر', orientation='h',
                 color='تعداد', color_continuous_scale='Reds', text='تعداد')
    fig_gn.update_traces(textposition='outside')
    fig_gn.update_layout(font=FONT, **BG, height=500, margin=dict(l=230,r=60,t=40,b=40))
    fig_gn.update_yaxes(automargin=True)
    event_gn = st.plotly_chart(fig_gn, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_gn")
    dl(fig_gn, 'genre', df_gn)
    if event_gn and hasattr(event_gn, 'selection') and event_gn.selection.get('points'):
        pt = event_gn.selection['points'][0]
        genre_sel = pt.get('y') or pt.get('label') or ''
        if genre_sel:
            goto_search(genre=genre_sel, kw=global_kw or None)
st.divider()

# ─── ۴. توزیع بر لحن ─────────────────────────────────────────────────────────
st.subheader("۴. توزیع بر لحن")
if global_kw:
    tn_rows = conn.execute(f"""
        SELECT jt.value t, COUNT(*) n
        FROM doc_tags tg JOIN documents d ON d.doc_id=tg.doc_id
        JOIN json_each(tg.tag_tone) jt
        WHERE jt.value != '' {kw_cond}
        GROUP BY t ORDER BY n DESC LIMIT 20
    """, kw_param).fetchall()
else:
    tn_rows = conn.execute("""
        SELECT value t, COUNT(*) n FROM doc_tags, json_each(tag_tone)
        WHERE value != '' GROUP BY t ORDER BY n DESC LIMIT 20
    """).fetchall()
if tn_rows:
    df_tn = pd.DataFrame(tn_rows, columns=['لحن','تعداد'])
    df_tn = df_tn.sort_values('تعداد', ascending=True)
    fig_tn = px.bar(df_tn, x='تعداد', y='لحن', orientation='h',
                 color='تعداد', color_continuous_scale='Reds', text='تعداد')
    fig_tn.update_traces(textposition='outside')
    fig_tn.update_layout(font=FONT, **BG, height=480, margin=dict(l=200,r=60,t=40,b=40))
    fig_tn.update_yaxes(automargin=True)
    event_tn = st.plotly_chart(fig_tn, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_tn")
    dl(fig_tn, 'tone', df_tn)
    if event_tn and hasattr(event_tn, 'selection') and event_tn.selection.get('points'):
        pt = event_tn.selection['points'][0]
        tone_sel = pt.get('y') or pt.get('label') or ''
        if tone_sel:
            goto_search(tone=tone_sel, kw=global_kw or None)
st.divider()

# ─── ۵. تطور کلیدواژه در طول زمان ───────────────────────────────────────────
st.subheader("۵. تطور کلیدواژه در طول زمان")
st.caption("تا ۵ کلیدواژه با کاما جدا کنید — روی نقاط کلیک کنید تا آمار آن سال باز شود")
kw_default = global_kw if global_kw else "آمریکا, اسرائیل, استکبار"
kw_in = st.text_input("کلیدواژه‌ها", kw_default, key='kwt')
if kw_in:
    kws = [k.strip() for k in kw_in.split(',') if k.strip()][:5]
    fig_kw = go.Figure()
    colors = ['#E91E63','#2196F3','#4CAF50','#FF9800','#9C27B0']
    kw_trend_data = {}
    for i, kw in enumerate(kws):
        trend = conn.execute("""
            SELECT substr(date_persian,1,4) y, COUNT(*) n FROM documents
            WHERE date_persian GLOB '1[34][0-9][0-9]/*' AND full_text LIKE ?
            GROUP BY y ORDER BY y
        """, (f'%{kw}%',)).fetchall()
        if trend:
            yrs = [r[0] for r in trend]; cnts = [r[1] for r in trend]
            kw_trend_data[kw] = dict(zip(yrs, cnts))
            fig_kw.add_trace(go.Scatter(x=yrs, y=cnts, mode='lines+markers',
                name=kw, line=dict(color=colors[i%5], width=2), marker=dict(size=6)))
    fig_kw.update_layout(font=FONT, **BG, height=380,
                      margin=dict(l=60,r=20,t=40,b=60),
                      xaxis_title='سال شمسی', yaxis_title='تعداد سند',
                      hovermode='x unified')
    event_kw = st.plotly_chart(fig_kw, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_kw")
    if kw_trend_data:
        all_years = sorted(set(y for d in kw_trend_data.values() for y in d))
        df_kw = pd.DataFrame({'سال': all_years})
        for kw_c, yd in kw_trend_data.items():
            df_kw[kw_c] = df_kw['سال'].map(yd).fillna(0).astype(int)
        dl(fig_kw, 'keyword_trend', df_kw)
    if event_kw and hasattr(event_kw, 'selection') and event_kw.selection.get('points'):
        pt = event_kw.selection['points'][0]
        yr_sel = str(pt.get('x') or '')
        kw_sel = pt.get('legendgroup') or pt.get('name','')
        if yr_sel:
            goto_search(y1=yr_sel, y2=yr_sel, kw=kw_sel or global_kw or None)
st.divider()

# ─── ۶. ابر کلمات ────────────────────────────────────────────────────────────
st.subheader("۶. ابر کلمات (Word Cloud)")

# فیلترهای مشترک
wc_col1, wc_col2, wc_col3 = st.columns(3)
wc_y1     = wc_col1.number_input("از سال", 1356, 1404, 1356, step=1, key='wc_y1')
wc_y2     = wc_col1.number_input("تا سال", 1356, 1404, 1404, step=1, key='wc_y2')
wc_period = wc_col2.selectbox("دوره (اختیاری)", ['همه'] + list(PERIOD_FA.values()), key='wc_period')
wc_kw     = wc_col3.text_input("کلیدواژه (اختیاری)", global_kw, key='wc_kw')
wc_n      = wc_col3.slider("حداکثر کلمات", 50, 200, 100, step=25, key='wc_n')

def _wc_build_conds(y1, y2, period, kw):
    conds = ["d.date_persian BETWEEN ? AND ?"]
    params: list = [f"{y1}/01/01", f"{y2}/12/29"]
    if period != 'همه':
        period_en_val = {v: k for k, v in PERIOD_FA.items()}.get(period, period)
        conds.append("d.period_label=?"); params.append(period_en_val)
    if kw.strip():
        conds.append("d.full_text LIKE ?"); params.append(f"%{kw.strip()}%")
    return "WHERE " + " AND ".join(conds), params

def _wc_render(freq, wc_n, caption_text):
    """رندر WordCloud از دیکشنری freq"""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        freq = {get_display(arabic_reshaper.reshape(k)): v for k, v in freq.items() if k}
    except ImportError:
        pass
    if not freq:
        st.warning("داده‌ای برای رسم یافت نشد.")
        return
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    font_path = str(Path(__file__).parent.parent / "assets" / "Vazirmatn.ttf")
    if not Path(font_path).exists():
        font_path = None
    wc_obj = WordCloud(
        font_path=font_path,
        width=900, height=420,
        background_color='white',
        max_words=wc_n,
        colormap='Reds',
        prefer_horizontal=0.85,
    ).generate_from_frequencies(freq)
    fig_wc, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc_obj, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig_wc)
    plt.close(fig_wc)
    st.caption(caption_text)

wc_tab1, wc_tab2 = st.tabs(["🏷️ ابر کلمات تگ‌ها (AI)", "📝 ابر کلمات متن (بسامد)"])

with wc_tab1:
    st.caption("بر اساس تگ‌های ۷ بعدی AI — معنایی و خلاصه‌شده")
    wc_tag_dims = st.multiselect(
        "ابعاد تگ",
        ['موضوع','منطقه','مخاطب','لحن','ژانر','مناسبت'],
        default=['موضوع','منطقه','لحن'],
        key='wc_dims'
    )
    if st.button("ساخت ابر کلمات تگ‌ها", key="btn_wc_tag"):
        try:
            from wordcloud import WordCloud
            wc_where, wc_params = _wc_build_conds(wc_y1, wc_y2, wc_period, wc_kw)
            DIM_MAP = {
                'موضوع':  ('json', 'tg.tag_topics'),
                'منطقه':  ('json', 'tg.tag_regions'),
                'مخاطب':  ('json', 'tg.tag_audience'),
                'لحن':    ('json', 'tg.tag_tone'),
                'ژانر':   ('single', 'tg.tag_form_genre'),
                'مناسبت': ('single', 'tg.tag_occasion'),
            }
            IGNORE = {'سایر', '', 'None', 'null', None}
            freq: dict = {}
            for dim in wc_tag_dims:
                kind, col = DIM_MAP[dim]
                if kind == 'json':
                    rows = conn.execute(f"""
                        SELECT jt.value, COUNT(*) n
                        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
                        JOIN json_each({col}) jt
                        {wc_where} AND jt.value NOT IN ('سایر','','None')
                        GROUP BY jt.value
                    """, wc_params).fetchall()
                else:
                    rows = conn.execute(f"""
                        SELECT {col}, COUNT(*) n
                        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
                        {wc_where} AND {col} IS NOT NULL AND {col} NOT IN ('سایر','','None')
                        GROUP BY {col}
                    """, wc_params).fetchall()
                for val, cnt in rows:
                    if val and val not in IGNORE:
                        freq[val] = freq.get(val, 0) + cnt
            _wc_render(freq, wc_n, f"منابع: {' + '.join(wc_tag_dims)} — {sum(freq.values()):.0f} تگ از اسناد فیلترشده")
        except ImportError:
            st.error("pip install wordcloud matplotlib")

with wc_tab2:
    st.caption("بر اساس بسامد واژه در متن — با فیلتر کلمات توقف (stopwords) فارسی")
    wc_txt_max_docs = st.slider("حداکثر تعداد سند برای پردازش", 100, 2000, 500, step=100, key='wc_txt_n')
    wc_min_len = st.number_input("حداقل طول کلمه (کاراکتر)", 2, 10, 3, key='wc_min_len')

    if st.button("ساخت ابر کلمات متن", key="btn_wc_txt"):
        try:
            from wordcloud import WordCloud
            import re as _re_wc
            wc_where, wc_params = _wc_build_conds(wc_y1, wc_y2, wc_period, wc_kw)

            # کلمات توقف فارسی جامع
            FA_STOPWORDS = {
                # حروف ربط و اضافه
                'و','در','از','با','به','که','را','این','آن','یا','اما','ولی','چون',
                'زیرا','اگر','تا','بر','هم','نیز','برای','پس','بعد','قبل','بین',
                'هر','همه','چند','چندین','بسیار','خیلی','بیش','کمتر','بیشتر',
                # ضمایر
                'من','تو','او','ما','شما','آنها','آن‌ها','ایشان','خود','خویش',
                'همین','همان','اینجا','آنجا','کجا','کی','چی','چه','چرا','چگونه',
                # افعال کمکی و پربسامد
                'است','بود','هست','شد','شده','شدن','بودن','هستند','بودند','شدند',
                'می‌شود','می‌کند','می‌کنند','کرد','کردن','کرده','می‌کرد','می‌شد',
                'دارد','داشت','دارند','داشتند','داریم','دارم','داشته','داشتیم',
                'می‌دهد','می‌دهند','داد','دادن','داده','می‌داد',
                'می‌گوید','می‌گویند','گفت','گفته','گفتند','گفتن',
                'می‌رود','رفت','رفتند','رفتن','می‌رفت','رفته',
                'می‌آید','آمد','آمدن','آمده','می‌آمد',
                'می‌شوند','می‌شویم','شویم','بشود','بشوند','شوند','بشویم',
                'می‌باشد','می‌باشند','باشد','باشند','بود','باشیم',
                'می‌تواند','می‌توانند','می‌توان','توانست','توانستند',
                'کنند','کنیم','کنم','کنی','کنید','بکند','بکنند','بکنیم',
                'نیست','نبود','نشد','نمی‌شود','نمی‌کند','نمی‌تواند',
                # قیدها و کلمات ربطی
                'هنوز','دیگر','دیگری','دیگران','بار','وقت','زمان','هیچ',
                'فقط','تنها','فقط','صرفاً','بسیار','بسی','بیش','پیش',
                'پس','نه','بله','خیر','البته','حتی','مثل','مانند','همچون',
                'چنین','چنان','اینکه','آنکه','اینچنین','بنابراین','بنابر',
                'لذا','بدین','همچنین','ضمن','طی','تحت','علیه','علیرغم',
                'جهت','باید','نباید','باید','بایستی','باید','بیاید',
                # کلمات دستوری کوتاه
                'ای','می','ها','های','را','به','در','از','با','که','تر','ترین',
                'هایی','ای','ها','های','گان','ون','ات',
                # اعداد و کاراکترهای خاص
                '،','؛','؟','!','.',':',',','-','_','/',
                '۰','۱','۲','۳','۴','۵','۶','۷','۸','۹',
                '0','1','2','3','4','5','6','7','8','9',
                # دیگر
                'طور','شکل','نوع','گونه','نظر','لحاظ','اساس','مبنای',
                'مورد','رابطه','زمینه','حوزه','حوزۀ','بحث',
            }

            # واکشی متون
            with st.spinner("در حال پردازش متون…"):
                txt_rows = conn.execute(f"""
                    SELECT d.full_text FROM documents d
                    {wc_where} AND d.full_text IS NOT NULL AND length(d.full_text) > 200
                    ORDER BY RANDOM() LIMIT {wc_txt_max_docs}
                """, wc_params).fetchall()

            if not txt_rows:
                st.warning("متنی برای پردازش یافت نشد.")
            else:
                # توکنیزیشن ساده فارسی
                all_text = ' '.join(r[0] for r in txt_rows if r[0])
                # پاکسازی: حذف اعراب، علائم نگارشی، اعداد
                all_text = _re_wc.sub(r'[ً-ٰ]', '', all_text)  # اعراب
                all_text = _re_wc.sub(r'[،؛؟!«»\(\)\[\]{}\.:,\-_/\\،‌‍]', ' ', all_text)
                all_text = all_text.replace('ي', 'ی').replace('ك', 'ک').replace('ة', 'ه')
                tokens = all_text.split()

                # شمارش بسامد با فیلتر stopwords
                freq: dict = {}
                for tok in tokens:
                    tok = tok.strip()
                    if (len(tok) >= int(wc_min_len)
                            and tok not in FA_STOPWORDS
                            and not _re_wc.match(r'^[\d۰-۹]+$', tok)
                            and not _re_wc.match(r'^[a-zA-Z]+$', tok)):
                        freq[tok] = freq.get(tok, 0) + 1

                top_freq = dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:wc_n*3])
                _wc_render(top_freq, wc_n,
                           f"پردازش {len(txt_rows):,} سند — {len(freq):,} نوع واژه — "
                           f"بیشترین: {list(sorted(freq.items(), key=lambda x:-x[1])[:5])}")
        except ImportError:
            st.error("pip install wordcloud matplotlib")

st.divider()

# ─── ۷. Heatmap دوره × موضوع ─────────────────────────────────────────────────
st.subheader("۷. Heatmap دوره × موضوع")
if global_kw:
    hm_rows = conn.execute(f"""
        SELECT d.period_label p, jt.value t, COUNT(*) n
        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
        JOIN json_each(tg.tag_topics) jt
        WHERE d.period_label IS NOT NULL AND jt.value NOT IN ('سایر','') {kw_cond}
        GROUP BY p, t
    """, kw_param).fetchall()
else:
    hm_rows = conn.execute("""
        SELECT d.period_label p, jt.value t, COUNT(*) n
        FROM documents d JOIN doc_tags tg ON d.doc_id=tg.doc_id
        JOIN json_each(tg.tag_topics) jt
        WHERE d.period_label IS NOT NULL AND jt.value NOT IN ('سایر','')
        GROUP BY p, t
    """).fetchall()
if hm_rows:
    df_hm = pd.DataFrame(hm_rows, columns=['period','topic','cnt'])
    df_hm['period'] = df_hm['period'].map(PERIOD_FA).fillna(df_hm['period'])
    pivot = df_hm.pivot_table(index='topic', columns='period', values='cnt', fill_value=0)
    fig_hm = px.imshow(pivot, color_continuous_scale='Reds', aspect='auto',
                    title='هر سلول = تعداد سند با آن موضوع در آن دوره')
    fig_hm.update_layout(font=FONT, **BG, height=750, margin=dict(l=300,r=40,t=60,b=200))
    fig_hm.update_yaxes(automargin=True, tickfont=dict(size=10))
    fig_hm.update_xaxes(automargin=True, tickangle=-35, tickfont=dict(size=10))
    st.plotly_chart(fig_hm, use_container_width=True)
    dl(fig_hm, 'heatmap_period_topic')
st.divider()

# ─── ۸. همرخدادی موضوعات ─────────────────────────────────────────────────────
st.subheader("۸. همرخدادی موضوعات")
st.caption("هر سلول = تعداد سندی که هر دو موضوع را دارد")
with st.spinner("در حال محاسبه…"):
    if global_kw:
        co_rows = conn.execute(f"""
            SELECT tg.doc_id, tg.tag_topics FROM doc_tags tg
            JOIN documents d ON d.doc_id=tg.doc_id
            WHERE tg.tag_topics IS NOT NULL AND tg.tag_topics != '[]' {kw_cond}
            LIMIT 30000
        """, kw_param).fetchall()
    else:
        co_rows = conn.execute("""
            SELECT doc_id, tag_topics FROM doc_tags
            WHERE tag_topics IS NOT NULL AND tag_topics != '[]' LIMIT 30000
        """).fetchall()
    topic_cnt = defaultdict(int)
    cooc = defaultdict(int)
    for r in co_rows:
        try: tps = [t for t in json.loads(r[1]) if t not in ('سایر','')]
        except: continue
        for t in tps: topic_cnt[t] += 1
        for i in range(len(tps)):
            for j in range(i+1, len(tps)):
                k = tuple(sorted([tps[i], tps[j]]))
                cooc[k] += 1
    top30 = [t for t,_ in sorted(topic_cnt.items(), key=lambda x:-x[1])[:25]]
    mat = pd.DataFrame(0, index=top30, columns=top30)
    for (a,b), n in cooc.items():
        if a in mat.index and b in mat.columns:
            mat.loc[a,b] = n; mat.loc[b,a] = n

if not mat.empty:
    fig_co = go.Figure(go.Heatmap(
        z=mat.values, x=list(mat.columns), y=list(mat.index),
        colorscale='Reds',
        hovertemplate='%{y}<br>× %{x}<br>تعداد: %{z}<extra></extra>',
        showscale=True,
    ))
    fig_co.update_layout(font=FONT, **BG, height=680,
                      title='همرخدادی موضوعات',
                      margin=dict(l=260,r=40,t=60,b=260))
    fig_co.update_xaxes(automargin=True, tickangle=-45)
    fig_co.update_yaxes(automargin=True)
    st.plotly_chart(fig_co, use_container_width=True)
    dl(fig_co, 'cooccurrence')
st.divider()

# ─── ۹. توزیع منطقه‌ای ───────────────────────────────────────────────────────
st.subheader("۹. توزیع منطقه‌ای")
if global_kw:
    rg_rows = conn.execute(f"""
        SELECT jt.value r, COUNT(*) n
        FROM doc_tags tg JOIN documents d ON d.doc_id=tg.doc_id
        JOIN json_each(tg.tag_regions) jt
        WHERE jt.value NOT IN ('سایر','ایران','') {kw_cond}
        GROUP BY r ORDER BY n DESC LIMIT 25
    """, kw_param).fetchall()
else:
    rg_rows = conn.execute("""
        SELECT value r, COUNT(*) n FROM doc_tags, json_each(tag_regions)
        WHERE value NOT IN ('سایر','ایران','') GROUP BY r ORDER BY n DESC LIMIT 25
    """).fetchall()
if rg_rows:
    df_rg = pd.DataFrame(rg_rows, columns=['منطقه','تعداد'])
    df_rg = df_rg.sort_values('تعداد', ascending=True)
    fig_rg = px.bar(df_rg, x='تعداد', y='منطقه', orientation='h',
                 color='تعداد', color_continuous_scale='Blues', text='تعداد')
    fig_rg.update_traces(textposition='outside')
    fig_rg.update_layout(font=FONT, **BG, height=480, margin=dict(l=180,r=60,t=40,b=40))
    fig_rg.update_yaxes(automargin=True)
    event_rg = st.plotly_chart(fig_rg, use_container_width=True,
                                on_select="rerun", selection_mode="points", key="ch_rg")
    dl(fig_rg, 'regions', df_rg)
    if event_rg and hasattr(event_rg, 'selection') and event_rg.selection.get('points'):
        pt = event_rg.selection['points'][0]
        region_sel = pt.get('y') or pt.get('label') or ''
        if region_sel:
            goto_search(region=region_sel, kw=global_kw or None)

render_footer()
