"""داشبورد اصلی — پیکره‌ی علی خامنه‌ای"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.db import get_stats, get_period_distribution, get_yearly_counts
from utils.charts import yearly_bar, period_bar
from utils.theme import render_header, render_footer, BRAND_DARK, BRAND_BLUE

render_header()

# ─── آماره‌های کلی ──────────────────────────────────────────────────────────
stats = get_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric("کل اسناد", f"{stats['total']:,}")
c2.metric("tier1 — صدای مستقیم", f"{stats['tier1']:,}")
c3.metric("بازه‌ی زمانی", f"{stats['date_min']}–{stats['date_max']}")
c4.metric("کل کلمات", f"{stats['total_words']:,}")

st.divider()

# ─── کارت‌های ابزار ─────────────────────────────────────────────────────────
st.markdown(f'<div style="direction:rtl;font-size:18px;font-weight:700;color:{BRAND_DARK};margin-bottom:12px">ابزارهای تحلیل</div>', unsafe_allow_html=True)

TOOLS = [
    ("pages/1_جستجو.py",     "🔍", "جستجوی پیشرفته",
     "فیلتر ۷ بعدی AI، ریشه‌یابی، wildcard، استناددهی، صادرات Excel/PDF"),
    ("pages/2_نمودارها.py",  "📊", "نمودارها",
     "توزیع زمانی، دوره‌ای، ژانر، لحن، ابر کلمات، heatmap منطقه‌ای"),
    ("pages/5_KWIC.py",       "🔎", "KWIC — کلیدواژه در بافت",
     "ظهور کلیدواژه با متن قبل/بعد · بارکد پراکنش · هم‌نشین‌های محتوایی"),
    ("pages/6_هم‌نشینی.py",  "🕸️", "هم‌نشینی آماری",
     "MI · Log-Likelihood · t-score · نمودار شبکه‌ای"),
    ("pages/7_کلیدواژگی.py", "🔑", "کلیدواژگی (Keyness)",
     "واژه‌های متمایزکننده بین دو دوره یا فیلتر"),
    ("pages/4_مقایسه.py",    "⚖️", "مقایسه کلیدواژه‌ها",
     "روند زمانی و توزیع چند کلیدواژه کنار هم"),
    ("pages/3_صادرات.py",    "⬇️", "صادرات داده",
     "دانلود انبوه: CSV · Excel · JSON با فیلتر دلخواه"),
    ("pages/8_کلیدواژه‌های_مفهومی.py", "💡", "کلیدواژه‌های مفهومی",
     "فهرست و نمودار مفاهیم کلیدی · روند ۳۷ساله · مضامین اصلی · مفاهیم مرکب"),
]

cols = st.columns(4)
for i, (page, icon, label, desc) in enumerate(TOOLS):
    with cols[i % 4]:
        st.markdown(f"""
<div style="background:#fff;border:1px solid #dce8ee;border-radius:10px;
            padding:16px;margin-bottom:8px;border-top:3px solid {BRAND_BLUE};
            min-height:110px;box-shadow:0 1px 4px rgba(0,0,0,.05)">
  <div style="font-size:20px;margin-bottom:6px">{icon}</div>
  <div style="font-weight:700;color:{BRAND_DARK};font-size:14px;
              margin-bottom:4px;direction:rtl">{label}</div>
  <div style="color:#5a7a8a;font-size:11px;line-height:1.6;direction:rtl">{desc}</div>
</div>
""", unsafe_allow_html=True)
        st.page_link(page, label="باز کردن ←", use_container_width=True)

st.divider()

# ─── نمودارها ────────────────────────────────────────────────────────────────
col_l, col_r = st.columns([3, 2])
with col_l:
    st.markdown(f'<div style="direction:rtl;font-weight:700;color:{BRAND_DARK};margin-bottom:6px">توزیع سالانه</div>', unsafe_allow_html=True)
    yearly = get_yearly_counts()
    if yearly:
        fig = yearly_bar(yearly, '')
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=30))
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown(f'<div style="direction:rtl;font-weight:700;color:{BRAND_DARK};margin-bottom:6px">دوره‌های تاریخی</div>', unsafe_allow_html=True)
    period_data = get_period_distribution()
    if period_data:
        fig3 = period_bar(period_data)
        fig3.update_layout(height=280, margin=dict(l=10, r=150, t=10, b=30))
        st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ─── راهنما ──────────────────────────────────────────────────────────────────
with st.expander("راهنمای کاربر", icon="📖"):
    st.markdown("""
**جستجو:**
- کلمات با فاصله = AND یا OR (انتخابی)
- «عبارت کامل» در گیومه = جستجوی دقیق
- `‒کلمه` = حذف از نتایج
- `استکبار*` = wildcard (پیشوند/پسوند)

**فیلترها:** tier1 = سخنرانی مستقیم | tier4 = متن ثانویه

**۷ بعد تگ AI:** voice · genre · audience · occasion · topics · regions · tone

**صادرات:** Excel · CSV · JSON · DOCX · PDF
""")

render_footer()
