"""صفحه‌ی راهنمای پیکره‌ی گفتاری خامنه‌ای"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.theme import render_header, render_footer, BRAND_BLUE, BRAND_DARK, BRAND_RED

render_header("راهنمای پیکره")


def _card(title, icon, color, body):
    st.html(f"""
<div style="
    border-right: 4px solid {color};
    background: {color}0d;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-family: Vazirmatn, sans-serif;
    direction: rtl;
">
  <div style="font-weight:700;font-size:15px;color:{color};margin-bottom:8px">
    {icon} {title}
  </div>
  <div style="font-size:13px;color:#033246;line-height:1.9">{body}</div>
</div>
""")


# ══════════════════════════════════════════════════════════════════════════════
# بلوک معرفی پیکره
st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;color:#033246">

  <!-- عنوان -->
  <div style="font-size:22px;font-weight:800;margin-bottom:6px">
    پیکره‌ی گفتاری علی خامنه‌ای
  </div>
  <div style="font-size:13px;color:#6a8a9a;margin-bottom:20px">
    بزرگ‌ترین مجموعه‌ی متنی قابل‌جستجو از گفتار رهبر جمهوری اسلامی ایران
  </div>

  <!-- سه کارت آمار کلیدی -->
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px">
    <div style="flex:1;min-width:140px;background:#f0f7ff;border-radius:10px;
                padding:14px 18px;border-top:3px solid #1091EC">
      <div style="font-size:28px;font-weight:800;color:#1091EC">۴۲,۷۴۹</div>
      <div style="font-size:12px;color:#5a7a8a;margin-top:2px">سند متنی</div>
    </div>
    <div style="flex:1;min-width:140px;background:#f0fff4;border-radius:10px;
                padding:14px 18px;border-top:3px solid #27ae60">
      <div style="font-size:28px;font-weight:800;color:#27ae60">۴۸ سال</div>
      <div style="font-size:12px;color:#5a7a8a;margin-top:2px">پوشش زمانی (۱۳۵۶–۱۴۰۴)</div>
    </div>
    <div style="flex:1;min-width:140px;background:#fff8f0;border-radius:10px;
                padding:14px 18px;border-top:3px solid #e67e22">
      <div style="font-size:28px;font-weight:800;color:#e67e22">۱۸ میلیون</div>
      <div style="font-size:12px;color:#5a7a8a;margin-top:2px">توکن پردازش‌شده</div>
    </div>
    <div style="flex:1;min-width:140px;background:#fdf0ff;border-radius:10px;
                padding:14px 18px;border-top:3px solid #8e44ad">
      <div style="font-size:28px;font-weight:800;color:#8e44ad">۱۹۸,۷۶۷</div>
      <div style="font-size:12px;color:#5a7a8a;margin-top:2px">واژه‌ی منحصربه‌فرد</div>
    </div>
  </div>

  <!-- این پیکره چیست -->
  <div style="font-size:16px;font-weight:700;margin-bottom:8px">این پیکره چیست؟</div>
  <div style="font-size:14px;line-height:2;margin-bottom:20px;color:#1a3040">
    این مجموعه تمام محتوای منتشرشده در سایت رسمی
    <strong>khamenei.ir</strong>
    را از آغاز فعالیت سایت تا اردیبهشت ۱۴۰۴ در بر می‌گیرد. اسناد شامل
    سخنرانی‌های کامل در دیدارها و جلسات، پیام‌های رسمی، احکام انتصاب،
    خطبه‌های نماز جمعه و عید، مصاحبه‌ها، و گزارش‌های روزنامه‌نگاران سایت
    از رویدادها هستند. پیکره به‌صورت خودکار از سایت crawl و پس از
    پردازش و دسته‌بندی در این ابزار بارگذاری شده است.
  </div>

  <!-- چطور جمع‌آوری شد -->
  <div style="font-size:16px;font-weight:700;margin-bottom:8px">چطور جمع‌آوری شد؟</div>
  <div style="font-size:14px;line-height:2;margin-bottom:20px;color:#1a3040">
    یک scraper اختصاصی تمام صفحات سایت رسمی را پردازش کرد و متون را استخراج،
    نرمال‌سازی و در یک پایگاه داده‌ی SQLite ذخیره کرد. هر سند با
    متادیتای کامل — تاریخ شمسی، مخاطب، مکان، نوع محتوا — همراه است.
    سپس یک مدل هوش مصنوعی هر سند را از نظر نوع محتوا و سطح تحلیلی
    (<em>analytical tier</em>) دسته‌بندی کرد تا محققان بتوانند
    بین کلام مستقیم خامنه‌ای و گزارش راوی تمایز قائل شوند.
  </div>

  <!-- ویژگی‌های منحصربه‌فرد -->
  <div style="font-size:16px;font-weight:700;margin-bottom:10px">ویژگی‌های منحصربه‌فرد</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px">

    <div style="background:#f8f9fa;border-radius:8px;padding:12px 14px;
                border-right:3px solid #1091EC">
      <div style="font-weight:700;font-size:13px;color:#1091EC;margin-bottom:4px">
        🎤 تفکیک گوینده
      </div>
      <div style="font-size:12px;color:#033246;line-height:1.8">
        تنها پیکره‌ای که کلام مستقیم خامنه‌ای (Tier 1) را از متن راوی
        (Tier 4 — ۸۱٪ اسناد) جدا می‌کند. این تمایز برای تحلیل گفتمان ضروری است.
      </div>
    </div>

    <div style="background:#f8f9fa;border-radius:8px;padding:12px 14px;
                border-right:3px solid #27ae60">
      <div style="font-weight:700;font-size:13px;color:#27ae60;margin-bottom:4px">
        📅 پوشش تاریخی کامل
      </div>
      <div style="font-size:12px;color:#033246;line-height:1.8">
        از قبل از انقلاب (۱۳۵۶) تا امروز — شامل دوره‌ی روحانی انقلابی،
        ریاست جمهوری، و ۳۵ سال رهبری. هیچ پیکره‌ی مشابهی این بازه را
        پوشش نمی‌دهد.
      </div>
    </div>

    <div style="background:#f8f9fa;border-radius:8px;padding:12px 14px;
                border-right:3px solid #e67e22">
      <div style="font-weight:700;font-size:13px;color:#e67e22;margin-bottom:4px">
        🔬 ابزار تحلیل یکپارچه
      </div>
      <div style="font-size:12px;color:#033246;line-height:1.8">
        جستجو، KWIC، هم‌نشینی، کلیدواژگی، تحلیل مضامین و روند زمانی —
        همه در یک محیط یکپارچه، بدون نیاز به دانش برنامه‌نویسی.
      </div>
    </div>

    <div style="background:#f8f9fa;border-radius:8px;padding:12px 14px;
                border-right:3px solid #8e44ad">
      <div style="font-weight:700;font-size:13px;color:#8e44ad;margin-bottom:4px">
        🇮🇷 نرمال‌سازی فارسی عمیق
      </div>
      <div style="font-size:12px;color:#033246;line-height:1.8">
        پیکره از ۵+ نوع کدگذاری مختلف برای نیم‌فاصله و اشکال گوناگون
        حروف عربی استفاده می‌کند. این اپ همه را یکسان می‌کند تا
        جستجو و تحلیل دقیق باشد.
      </div>
    </div>

  </div>

</div>
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🗂 ساختار پیکره — چهار سطح تحلیلی")

st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:13px;
     color:#5a7a8a;line-height:1.8;margin-bottom:12px">
پیکره به چهار سطح (<strong>analytical_tier</strong>) تقسیم شده است.
انتخاب سطح مناسب برای پژوهش بسیار مهم است — نتایج تحلیل بسته به سطح انتخابی
می‌توانند کاملاً متفاوت باشند.
</div>
""")

tier_data = [
    {
        "tier": "Tier 1",
        "icon": "🎤",
        "color": "#1091EC",
        "label": "سخنرانی مستقیم",
        "count": "۲,۵۳۱ سند",
        "pct": "۵.۹٪",
        "avg_words": "۲,۷۶۷ کلمه",
        "sources": "سخنرانی در دیدارها، پیام‌های مهم، مصاحبه‌ها، احکام سیاسی",
        "best_for": "تحلیل ایدئولوژی، موضع‌گیری سیاسی، استدلال — اینجا خامنه‌ای <em>چیزی می‌گوید</em>",
        "note": "کلمات کلیدی مثل «انرژی هسته‌ای» عمدتاً اینجا هستند",
    },
    {
        "tier": "Tier 2",
        "icon": "📋",
        "color": "#27ae60",
        "label": "پیام‌های تشریفاتی",
        "count": "۹۱۴ سند",
        "pct": "۲.۱٪",
        "avg_words": "۱۸۷ کلمه",
        "sources": "تسلیت (۴۷۹)، انتصاب روتین (۲۹۸)، احکام عفو (۱۳۷)",
        "best_for": "مطالعه‌ی شبکه‌های قدرت و نهادی — چه کسانی منصوب یا مورد تقدیر قرار می‌گیرند",
        "note": "محتوای تحلیلی ندارد — مناسب تحلیل گفتمانی نیست",
    },
    {
        "tier": "Tier 3",
        "icon": "📝",
        "color": "#e67e22",
        "label": "گزیده و خلاصه",
        "count": "۳۵۸ سند",
        "pct": "۰.۸٪",
        "avg_words": "۷۹۱ کلمه",
        "sources": "پیام‌های عمومی، سخنرانی‌های انتخاباتی",
        "best_for": "بررسی خطاب‌های عمومی — وقتی مخاطب عموم مردم است نه نخبگان",
        "note": "حجم کم — نمونه‌ی محدود",
    },
    {
        "tier": "Tier 4",
        "icon": "📰",
        "color": "#8e44ad",
        "label": "متن راوی / گزارش سایت",
        "count": "۳۴,۷۱۲ سند",
        "pct": "۸۱.۲٪",
        "avg_words": "۶۴۲ کلمه",
        "sources": "گزارش‌های روزنامه‌نگاران سایت رسمی از جلسات و دیدارها",
        "best_for": "پوشش زمانی کامل، تحلیل روند بلندمدت، آمار کلی پیکره",
        "note": "اینها کلمات <em>راوی</em> هستند، نه خامنه‌ای — با احتیاط استفاده شود",
    },
]

for d in tier_data:
    st.html(f"""
<div style="
    border: 1px solid {d['color']}44;
    border-right: 5px solid {d['color']};
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-family: Vazirmatn, sans-serif;
    direction: rtl;
    background: #fff;
">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
    <div style="font-weight:700;font-size:16px;color:{d['color']}">
      {d['icon']} {d['tier']} — {d['label']}
    </div>
    <div style="display:flex;gap:16px;font-size:12px;color:#5a7a8a">
      <span>📄 {d['count']}</span>
      <span>📊 {d['pct']} پیکره</span>
      <span>📏 میانگین {d['avg_words']}</span>
    </div>
  </div>
  <div style="font-size:12px;color:#5a7a8a;margin:6px 0 4px">
    <strong>محتوا:</strong> {d['sources']}
  </div>
  <div style="font-size:13px;color:#033246;margin-bottom:4px">
    ✅ <strong>بهترین کاربرد:</strong> {d['best_for']}
  </div>
  <div style="font-size:12px;color:#888">
    ℹ️ {d['note']}
  </div>
</div>
""")

st.html("""
<div dir="rtl" style="
    font-family:Vazirmatn,sans-serif;
    background:#f0f7ff;border-radius:8px;
    padding:12px 16px;font-size:13px;color:#033246;
    line-height:1.8;margin-top:4px
">
💡 <strong>توصیه‌ی پژوهشی:</strong>
برای تحلیل ایدئولوژی و گفتمان، از <strong>Tier 1</strong> شروع کنید.
برای پوشش زمانی کامل و روند بلندمدت، <strong>همه</strong> (بدون فیلتر tier) را انتخاب کنید
اما نتایج را با احتیاط تفسیر کنید — ۸۱٪ پیکره گفتار راوی است.
</div>
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📅 پوشش زمانی — دوره‌های تاریخی")

st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:13px;line-height:1.9">
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <thead>
    <tr style="background:#033246;color:white">
      <th style="padding:8px 12px;text-align:right">دوره</th>
      <th style="padding:8px 12px;text-align:right">بازه‌ی زمانی</th>
      <th style="padding:8px 12px;text-align:right">نقش خامنه‌ای</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background:#f9f9f9">
      <td style="padding:7px 12px">قبل از انقلاب</td>
      <td style="padding:7px 12px">تا ۱۳۵۷</td>
      <td style="padding:7px 12px">روحانی انقلابی، فعال سیاسی</td>
    </tr>
    <tr>
      <td style="padding:7px 12px">اوایل انقلاب</td>
      <td style="padding:7px 12px">۱۳۵۷–۱۳۶۰</td>
      <td style="padding:7px 12px">مقام‌های اولیه‌ی جمهوری اسلامی</td>
    </tr>
    <tr style="background:#f9f9f9">
      <td style="padding:7px 12px">دوران ریاست جمهوری</td>
      <td style="padding:7px 12px">۱۳۶۰–۱۳۶۸</td>
      <td style="padding:7px 12px">رئیس‌جمهور (دوره‌ی جنگ)</td>
    </tr>
    <tr>
      <td style="padding:7px 12px">رفسنجانی</td>
      <td style="padding:7px 12px">۱۳۶۸–۱۳۷۶</td>
      <td style="padding:7px 12px">رهبر — دوره‌ی سازندگی</td>
    </tr>
    <tr style="background:#f9f9f9">
      <td style="padding:7px 12px">خاتمی</td>
      <td style="padding:7px 12px">۱۳۷۶–۱۳۸۴</td>
      <td style="padding:7px 12px">رهبر — دوره‌ی اصلاحات</td>
    </tr>
    <tr>
      <td style="padding:7px 12px">احمدی‌نژاد</td>
      <td style="padding:7px 12px">۱۳۸۴–۱۳۹۲</td>
      <td style="padding:7px 12px">رهبر — دوره‌ی تنش هسته‌ای</td>
    </tr>
    <tr style="background:#f9f9f9">
      <td style="padding:7px 12px">روحانی</td>
      <td style="padding:7px 12px">۱۳۹۲–۱۴۰۰</td>
      <td style="padding:7px 12px">رهبر — دوره‌ی برجام</td>
    </tr>
    <tr>
      <td style="padding:7px 12px">رئیسی تا مرگ</td>
      <td style="padding:7px 12px">۱۴۰۰–۱۴۰۴</td>
      <td style="padding:7px 12px">رهبر — دوره‌ی اخیر</td>
    </tr>
  </tbody>
</table>
</div>
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🔧 ابزارهای تحلیلی")

col1, col2 = st.columns(2)

with col1:
    _card("جستجو", "🔎", "#1091EC",
          "جستجوی متنی در کل پیکره با فیلتر دوره، tier، و نوع سند. "
          "نتایج قابل دانلود هستند.")
    _card("نمودارها", "📊", "#1091EC",
          "نمودارهای آماری کلی پیکره — توزیع زمانی، موضوعی و ساختاری اسناد.")
    _card("KWIC — کلیدواژه در بافت", "🔍", "#27ae60",
          "هر بار که یک کلمه در پیکره ظاهر می‌شود را با متن قبل و بعد نشان می‌دهد. "
          "برای مطالعه‌ی معنا و تحول مفهومی واژه‌ها.")
    _card("هم‌نشینی آماری", "🔗", "#27ae60",
          "واژه‌هایی که به‌طور آماری معنادار در کنار یک کلیدواژه ظاهر می‌شوند. "
          "سه معیار: MI (منحصربه‌فردترین)، LL (علمی‌ترین)، t-score (پربسامدترین).")

with col2:
    _card("کلیدواژگی (Keyness)", "🔑", "#e67e22",
          "مقایسه‌ی دو زیرپیکره — کدام واژه‌ها در یک دوره بیشتر از دوره‌ی دیگر "
          "ظاهر می‌شوند؟ معیار G² (لگاریتم درستنمایی).")
    _card("کلیدواژه‌های مفهومی", "🧠", "#e67e22",
          "تحلیل عمیق ۲۷ مضمون اصلی، مقایسه‌ی کلیدواژه‌ها، روند زمانی، "
          "و مفاهیم مرکب. مناسب برای پژوهش‌های ایدئولوژیک.")
    _card("صادرات داده", "⬇️", "#8e44ad",
          "دانلود انبوه اسناد پیکره در فرمت CSV یا Excel با فیلترهای دلخواه.")
    _card("کتابخانه‌ی نقل‌قول", "📚", "#8e44ad",
          "ذخیره، مدیریت و صادرات نقل‌قول‌های مورد نظر از پیکره.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📐 معیارهای آماری")

st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif">
<table style="width:100%;border-collapse:collapse;font-size:13px">
  <thead>
    <tr style="background:#033246;color:white">
      <th style="padding:8px 12px;text-align:right">معیار</th>
      <th style="padding:8px 12px;text-align:right">سوالی که می‌پرسد</th>
      <th style="padding:8px 12px;text-align:right">بهترین کاربرد</th>
      <th style="padding:8px 12px;text-align:right">محدودیت</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background:#f9f9f9">
      <td style="padding:8px 12px;font-weight:700;color:#1091EC">MI</td>
      <td style="padding:8px 12px">این دو واژه چقدر <em>منحصراً</em> با هم ظاهر می‌شوند؟</td>
      <td style="padding:8px 12px">عبارات ثابت و اصطلاحی کم‌بسامد</td>
      <td style="padding:8px 12px">به واژه‌های نادر حساس است</td>
    </tr>
    <tr>
      <td style="padding:8px 12px;font-weight:700;color:#27ae60">LL / G²</td>
      <td style="padding:8px 12px">آیا همرخدادی فراتر از شانس است؟</td>
      <td style="padding:8px 12px">گزارش علمی، استناد پژوهشی</td>
      <td style="padding:8px 12px">واژه‌های پربسامد را بالا می‌برد</td>
    </tr>
    <tr style="background:#f9f9f9">
      <td style="padding:8px 12px;font-weight:700;color:#e67e22">t-score</td>
      <td style="padding:8px 12px">این دو واژه چقدر <em>پیوسته</em> با هم می‌آیند؟</td>
      <td style="padding:8px 12px">هم‌نشین‌های روزمره و پربسامد</td>
      <td style="padding:8px 12px">نتایج ممکن است بدیهی باشند</td>
    </tr>
    <tr>
      <td style="padding:8px 12px;font-weight:700;color:#8e44ad">TF-IDF</td>
      <td style="padding:8px 12px">این واژه چقدر در این سند <em>خاص</em> است؟</td>
      <td style="padding:8px 12px">یافتن کلمات شاخص هر دوره یا موضوع</td>
      <td style="padding:8px 12px">نیاز به مقایسه‌ی چند سند دارد</td>
    </tr>
  </tbody>
</table>
</div>
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("⚠️ محدودیت‌های پیکره")

st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:13px;line-height:1.9;color:#033246">

<div style="background:#fff3cd;border-right:4px solid #ffc107;border-radius:6px;padding:12px 16px;margin-bottom:10px">
  <strong>۱. عدم تعادل زمانی</strong><br>
  ۴۷٪ اسناد از دهه‌ی ۱۳۹۰ هستند — سال‌های اولیه (۱۳۵۶–۱۳۶۸) پوشش بسیار کمتری دارند.
  در نمودارهای روند، همیشه از «درصد نرمال‌شده» استفاده کنید، نه بسامد مطلق.
</div>

<div style="background:#fff3cd;border-right:4px solid #ffc107;border-radius:6px;padding:12px 16px;margin-bottom:10px">
  <strong>۲. ۸۱٪ پیکره متن راوی است</strong><br>
  Tier 4 گزارش خبرنگاران سایت رسمی است — نه کلمات خود خامنه‌ای.
  برای تحلیل گفتمانی، tier1 را انتخاب کنید.
</div>

<div style="background:#fff3cd;border-right:4px solid #ffc107;border-radius:6px;padding:12px 16px;margin-bottom:10px">
  <strong>۳. منبع واحد</strong><br>
  همه‌ی اسناد از سایت رسمی khamenei.ir هستند — ویرایش‌شده و گزینش‌شده توسط دفتر رهبری.
  سخنرانی‌های ویرایش‌نشده یا حذف‌شده در این پیکره نیستند.
</div>

<div style="background:#fff3cd;border-right:4px solid #ffc107;border-radius:6px;padding:12px 16px">
  <strong>۴. نرمال‌سازی متن</strong><br>
  پیکره از فرم‌های مختلف Unicode برای نیم‌فاصله استفاده می‌کند (U+200C، U+200F، U+00AD).
  این اپ همه را یکسان می‌کند، اما جستجوی دستی ممکن است نتایج ناقص بدهد.
</div>

</div>
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📬 درباره‌ی پروژه")
st.html("""
<div dir="rtl" style="font-family:Vazirmatn,sans-serif;font-size:13px;
     line-height:1.9;color:#5a7a8a">
این ابزار توسط <a href="https://www.volantmedia.net" target="_blank"
style="color:#1091EC">Volant Media</a> و
<a href="https://www.iranintl.com" target="_blank"
style="color:#1091EC">ایران اینترنشنال</a> ساخته شده است
برای پژوهش در گفتمان سیاسی جمهوری اسلامی ایران.
</div>
""")

render_footer()
