"""صفحه‌ی کتابخانه‌ی نقل‌قول"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.db import get_conn, ensure_quote_library, get_quotes, delete_quote, save_quote
from utils.export import to_markdown, filename
from utils.theme import render_header, render_footer, BRAND_DARK, BRAND_BLUE

render_header("کتابخانه‌ی نقل‌قول")

st.markdown("""
<style>
  .quote-card { background:#FFF9C4; border-right:4px solid #E91E63; border-radius:6px;
    padding:12px; margin-bottom:10px; direction:rtl; }
</style>
""", unsafe_allow_html=True)

conn = get_conn()
ensure_quote_library(conn)

# ─── افزودن نقل‌قول دستی ─────────────────────────────────────────────────────
with st.expander("افزودن نقل‌قول دستی", icon="➕"):
    doc_id_in = st.text_input("doc_id سند", key='q_doc')
    quote_in  = st.text_area("متن نقل‌قول", key='q_text', height=100)
    note_in   = st.text_input("یادداشت", key='q_note')
    tag_in    = st.text_input("تگ (مثلاً: برای قسمت ۲)", key='q_tag')
    if st.button("💾 ذخیره"):
        if doc_id_in and quote_in:
            save_quote(conn, doc_id_in, quote_in, note_in, tag_in)
            st.success("✓ ذخیره شد")
            st.rerun()
        else:
            st.warning("doc_id و متن نقل‌قول الزامی است.")

# ─── فیلتر ───────────────────────────────────────────────────────────────────
cur = conn.cursor()
cur.execute("SELECT DISTINCT tag FROM quote_library WHERE tag IS NOT NULL AND tag != '' ORDER BY tag")
all_tags = [r[0] for r in cur.fetchall()]

sel_tag = st.selectbox("فیلتر بر تگ", ['همه'] + all_tags, key='qt_filter')
sort_by = st.radio("مرتب‌سازی", ['تاریخ ذخیره (جدید)', 'تاریخ سند'], horizontal=True, key='qt_sort')

quotes = get_quotes(conn, tag=sel_tag if sel_tag != 'همه' else '')

if not quotes:
    st.info("هنوز نقل‌قولی ذخیره نشده. از صفحه‌ی جستجو دکمه‌ی 📌 را بزنید.")
else:
    st.markdown(f"**{len(quotes):,} نقل‌قول** ذخیره‌شده")

    for q in quotes:
        st.markdown(f"""
<div class="quote-card">
  <div style="font-size:0.82rem;color:#888;margin-bottom:6px">
    {q.get('date_persian','')} | {q.get('title','')[:60] or q.get('doc_id','')}
    {f"| 🏷️ {q['tag']}" if q.get('tag') else ''}
  </div>
  <div style="line-height:1.8;margin-bottom:8px">"{q.get('quote_text','')}"</div>
  {f"<div style='color:#555;font-size:0.85rem;font-style:italic'>📝 {q['note']}</div>" if q.get('note') else ''}
</div>
""", unsafe_allow_html=True)

        qc1, qc2, qc3, qc4 = st.columns([1,1,1,3])
        with qc1:
            if q.get('url'):
                st.markdown(f"[🔗 لینک]({q['url']})")
        with qc2:
            new_note = st.text_input("ویرایش یادداشت", value=q.get('note',''),
                                     key=f"note_{q['id']}", label_visibility='collapsed')
            if new_note != q.get('note',''):
                conn.execute("UPDATE quote_library SET note=? WHERE id=?", (new_note, q['id']))
                conn.commit()
        with qc3:
            if st.button("🗑️", key=f"del_{q['id']}", help="حذف"):
                delete_quote(conn, q['id'])
                st.rerun()

    # ─── صادرات کتابخانه ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("صادرات کتابخانه")

    ea, eb, ec = st.columns(3)

    # Markdown
    md_lines = [f"# کتابخانه‌ی نقل‌قول\n\n"]
    for q in quotes:
        md_lines.append(f"## {q.get('title','')}\n")
        md_lines.append(f"**تاریخ:** {q.get('date_persian','')} | **doc_id:** `{q.get('doc_id','')}`\n\n")
        md_lines.append(f"> {q.get('quote_text','')}\n\n")
        if q.get('note'):
            md_lines.append(f"*یادداشت: {q['note']}*\n\n")
        md_lines.append("---\n\n")
    ea.download_button("⬇️ Markdown", ''.join(md_lines).encode('utf-8'),
                        file_name=filename('md'), mime='text/markdown')

    # Excel
    try:
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        wb = Workbook()
        ws = wb.active
        ws.title = 'نقل‌قول‌ها'
        ws.sheet_view.rightToLeft = True
        ws.append(['doc_id','تاریخ','عنوان','نقل‌قول','یادداشت','تگ','لینک'])
        for q in quotes:
            ws.append([q.get('doc_id',''), q.get('date_persian',''),
                       q.get('title',''), q.get('quote_text',''),
                       q.get('note',''), q.get('tag',''), q.get('url','')])
        for cell in ws[1]:
            cell.font = Font(bold=True, name='Vazirmatn')
        buf = io.BytesIO()
        wb.save(buf)
        eb.download_button("⬇️ Excel", buf.getvalue(),
                            file_name=filename('xlsx'),
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception:
        pass

    # CSV
    df_q = pd.DataFrame([{
        'doc_id': q.get('doc_id',''),
        'date': q.get('date_persian',''),
        'title': q.get('title',''),
        'quote': q.get('quote_text',''),
        'note': q.get('note',''),
        'tag': q.get('tag',''),
        'url': q.get('url',''),
    } for q in quotes])
    ec.download_button("⬇️ CSV", df_q.to_csv(index=False).encode('utf-8-sig'),
                        file_name=filename('csv'), mime='text/csv')

render_footer()
