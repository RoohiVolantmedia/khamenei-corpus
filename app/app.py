"""ناوبری اصلی — پیکره‌ی علی خامنه‌ای"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="پیکره‌ی خامنه‌ای",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/خانه.py",                          title="خانه",                   icon="🏠"),
    st.Page("pages/0_راهنما.py",                      title="راهنما",                 icon="📖"),
    st.Page("pages/1_جستجو.py",                       title="جستجو",                  icon="🔍"),
    st.Page("pages/2_نمودارها.py",                    title="نمودارها",               icon="📊"),
    st.Page("pages/3_صادرات.py",                      title="صادرات",                 icon="⬇️"),
    st.Page("pages/4_مقایسه.py",                      title="مقایسه",                 icon="⚖️"),
    st.Page("pages/5_KWIC.py",                         title="KWIC",                   icon="🔎"),
    st.Page("pages/6_هم‌نشینی.py",                   title="هم‌نشینی",              icon="🕸️"),
    st.Page("pages/7_کلیدواژگی.py",                  title="کلیدواژگی",             icon="🔑"),
    st.Page("pages/8_کلیدواژه‌های_مفهومی.py",       title="کلیدواژه‌های مفهومی",  icon="💡"),
    st.Page("pages/4_کتابخانه.py",                    title="کتابخانه",               icon="📚"),
])

pg.run()
