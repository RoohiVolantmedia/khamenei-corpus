"""تم و هدر مشترک برای همه صفحات"""
from pathlib import Path
import base64
import streamlit as st
import streamlit.components.v1 as components

BRAND_DARK  = "#033246"
BRAND_BLUE  = "#1091EC"
BRAND_RED   = "#EC1010"
BRAND_LIGHT = "#F4F7FA"

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "ii-logo-fa.svg"


def _logo_b64(width=110, height=50) -> str:
    if _LOGO_PATH.exists():
        svg = _LOGO_PATH.read_text(encoding="utf-8")
        svg = svg.replace(
            '<svg width="752" height="376"',
            f'<svg width="{width}" height="{height}" viewBox="0 0 752 376"',
        )
        b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f'data:image/svg+xml;base64,{b64}'
    return None


# ── CSS پایه (فونت، سایدبار، کارت‌ها، ...) ───────────────────────────────────
_BASE_CSS = f"""
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css"
      rel="stylesheet">
<style>
body, p, div, span, h1, h2, h3, h4, h5, h6,
button, label, a, li, td, th, input, select, textarea,
[data-testid="stMarkdownContainer"],
[data-testid="stText"], [data-testid="stMetric"], [data-testid="stAlert"] {{
    font-family: 'Vazirmatn', sans-serif;
}}

#MainMenu {{ visibility: hidden !important; }}
footer    {{ visibility: hidden !important; }}

[data-testid="stSidebar"] {{
    background: #0d2232 !important;
    border-left: none !important;
}}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {{ color: #cde !important; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{ color: #fff !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: {BRAND_BLUE}22 !important;
    border: 1px solid {BRAND_BLUE}55 !important;
    color: #fff !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {BRAND_BLUE}44 !important;
}}
[data-testid="stSidebarNav"] a {{
    color: #aaccdd !important; border-radius: 6px;
    padding: 6px 12px; transition: background 0.15s;
}}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a[aria-selected="true"] {{
    background: {BRAND_BLUE}33 !important; color: #fff !important;
}}

[data-testid="stMetric"] {{
    background: #fff; border: 1px solid #e0e8ee;
    border-radius: 10px; padding: 14px 18px !important;
    border-top: 3px solid {BRAND_BLUE};
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}}
[data-testid="stMetric"] label {{ color: #5a7a8a !important; font-size: 0.82rem; }}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {BRAND_DARK} !important; font-size: 1.5rem; font-weight: 700;
}}

.stButton > button[kind="primary"] {{
    background: {BRAND_RED} !important; border: none !important;
    color: white !important; border-radius: 6px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
}}
.stButton > button[kind="primary"]:hover {{ background: #c0000d !important; }}
.stButton > button:not([kind="primary"]) {{
    border: 1px solid {BRAND_BLUE}66 !important;
    border-radius: 6px !important; color: {BRAND_DARK} !important;
}}

hr {{ border-color: #e0e8ee !important; }}

/* ── RTL برای پاراگراف‌های فارسی مختلط ───────────────────────────────────── */
/* وقتی متن فارسی دارای کلمات انگلیسی است، direction:rtl ساختار جمله را حفظ می‌کند */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5 {{
    direction: rtl;
    text-align: right;
    unicode-bidi: embed;
}}
/* کد و pre باید LTR بمانند */
[data-testid="stMarkdownContainer"] pre,
[data-testid="stMarkdownContainer"] code {{
    direction: ltr;
    text-align: left;
    unicode-bidi: embed;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: {BRAND_LIGHT}; border-radius: 8px 8px 0 0;
    padding: 4px 8px 0; border-bottom: 2px solid {BRAND_BLUE}44;
}}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{
    border-bottom: 2px solid {BRAND_BLUE} !important;
    color: {BRAND_BLUE} !important; font-weight: 700 !important;
}}

[data-testid="stTextInput"] input {{
    border: 1.5px solid #c5d8e4 !important; border-radius: 6px !important;
    background: #fff !important; color: {BRAND_DARK} !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {BRAND_BLUE} !important;
    box-shadow: 0 0 0 2px {BRAND_BLUE}22 !important;
}}

[data-testid="stAlert"] {{ border-radius: 6px; }}

.app-footer {{
    background: {BRAND_LIGHT}; border-top: 1px solid #d0dde5;
    padding: 10px 24px; text-align: center;
    color: #6a8a9a; font-size: 11px; margin-top: 2rem;
}}
.app-footer a {{ color: {BRAND_BLUE}; text-decoration: none; }}
.app-footer a:hover {{ text-decoration: underline; }}
</style>
"""


def render_header(page_subtitle: str = ""):
    # ۱. CSS پایه
    st.html(_BASE_CSS)

    # ۲. JavaScript مستقیم روی DOM والد — رنگ هدر + inject لوگو
    logo_src = _logo_b64(width=110, height=50) or ""
    logo_img = (
        f'<a href="https://www.iranintl.com" target="_blank" style="display:block;line-height:0">'
        f'<img src="{logo_src}" width="110" height="50" style="display:block"></a>'
        if logo_src else ""
    )
    subtitle_html = (
        f'<span style="color:#8bb8cc;font-size:11px;display:block">{page_subtitle}</span>'
        if page_subtitle else ""
    )

    components.html(f"""
<script>
(function() {{
    const doc = window.parent.document;

    // ── رنگ هدر native ─────────────────────────────────────────────
    const header = doc.querySelector('[data-testid="stHeader"]');
    if (header) {{
        header.style.background    = '{BRAND_DARK}';
        header.style.borderBottom  = '3px solid {BRAND_BLUE}';
        // همه آیکون‌های داخل هدر را سفید کن
        header.querySelectorAll('svg, button').forEach(el => {{
            el.style.color = '#ffffff';
            el.style.fill  = '#ffffff';
        }});
        header.querySelectorAll('svg path, svg rect, svg circle').forEach(el => {{
            el.style.fill = '#ffffff';
        }});
        // مخفی کردن دکمه Deploy
        header.querySelectorAll('button').forEach(btn => {{
            if (btn.innerText && btn.innerText.trim() === 'Deploy') {{
                btn.style.display = 'none';
            }}
        }});
    }}

    // ── inject لوگو + عنوان در سمت راست هدر ───────────────────────
    if (header && !doc.getElementById('app-brand-in-header')) {{
        const brand = doc.createElement('div');
        brand.id = 'app-brand-in-header';
        brand.style.cssText = [
            'position:absolute',
            'top:0', 'right:14px',
            'height:100%',
            'display:flex',
            'align-items:center',
            'gap:10px',
            'direction:rtl',
            'z-index:9999',
            'pointer-events:auto',
        ].join(';');
        brand.innerHTML = `
            {logo_img}
            <div style="line-height:1.35">
                <a href="https://www.volantmedia.net" target="_blank"
                   style="font-size:9px;font-weight:600;letter-spacing:1px;
                          text-transform:uppercase;color:{BRAND_BLUE};text-decoration:none">
                    Volant Media
                </a>
                <div style="color:#fff;font-size:15px;font-weight:700">
                    پیکره‌ی گفتاری خامنه‌ای
                </div>
                {subtitle_html}
            </div>
        `;
        header.style.position = 'relative';
        header.appendChild(brand);
    }} else if (doc.getElementById('app-brand-in-header')) {{
        // بروزرسانی subtitle در صورت تغییر صفحه
        const sub = doc.getElementById('app-brand-subtitle');
        if (sub) sub.innerHTML = '{page_subtitle}';
    }}
}})();
</script>
""", height=0, scrolling=False)


def render_footer():
    st.html("""
<div class="app-footer">
  پیکره‌ی گفتاری خامنه‌ای &nbsp;·&nbsp;
  <a href="https://www.volantmedia.net" target="_blank">Volant Media</a>
  &nbsp;·&nbsp; داده‌های عمومی سایت رسمی
</div>
""")
