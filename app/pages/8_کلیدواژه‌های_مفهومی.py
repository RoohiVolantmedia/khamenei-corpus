"""کلیدواژه‌های مفهومی — ۳۷ سال رهبری خامنه‌ای"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.db import get_conn
from utils.corpus_index import is_built, FA_STOP, normalize_fa
from utils.theme import render_header, render_footer, BRAND_DARK, BRAND_BLUE, BRAND_RED

# ─── پیکربندی صفحه ──────────────────────────────────────────────────────────
render_header("کلیدواژه‌های مفهومی — ۳۷ سال رهبری")

# ─── ثابت‌های محتوایی ────────────────────────────────────────────────────────
EXTRA_STOP = {
    # افعال
    'است', 'بود', 'شد', 'کرد', 'دارد', 'دارند', 'شدند', 'کردند', 'گفت', 'گفتند',
    'داشت', 'داشتند', 'شده', 'کرده', 'نیست', 'نبود', 'شوند', 'کنند', 'دهند',
    'باید', 'شاید', 'توانست', 'بتوان', 'می‌توان', 'کنید', 'بگویید', 'می‌گوید',
    'آمد', 'رفت', 'آمدند', 'رفتند', 'بود', 'هستند', 'می‌شود', 'می‌کند',
    'می‌کنند', 'می‌دهد', 'می‌دهند', 'می‌خواهد', 'می‌خواهند', 'گردد', 'گردند',
    'شوید', 'باشید', 'باشند', 'نداشت', 'ندارد', 'نشود', 'نکند', 'نگفت',
    # ضمایر و اشاره
    'ایشان', 'وی', 'خود', 'همه', 'هیچ', 'هر', 'این', 'آن', 'همین', 'همان',
    'من', 'تو', 'او', 'ما', 'شما', 'آنها', 'آن‌ها', 'خویش', 'خویشتن',
    # زمان و مکان عمومی
    'وقت', 'زمان', 'روز', 'سال', 'ماه', 'امروز', 'فردا', 'دیروز',
    'جا', 'جای', 'مکان', 'محل',
    # قیود و حروف
    'خیلی', 'بسیار', 'زیاد', 'کم', 'چند', 'بعضی', 'برخی', 'حتی',
    'همچنین', 'نیز', 'هم', 'البته', 'حال', 'پس', 'اما', 'ولی',
    'چون', 'اگر', 'تنها', 'فقط', 'هنوز', 'دیگر', 'هرگز',
    # اعداد
    'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه', 'ده',
    'صد', 'هزار', 'میلیون',
    # کلمات رسانه‌ای/وب
    'عکس', 'صوت', 'فیلم', 'ویدئو', 'ویدیو', 'تصویر', 'متن', 'نوشته',
    'دریافت', 'دانلود', 'بارگذاری', 'سایت', 'لینک', 'کلیک',
    # عناوین و خطاب
    'آقای', 'خانم', 'جناب', 'حضرت', 'دکتر', 'مهندس', 'استاد',
    # اجزاء بدن و اشیاء عمومی بی‌معنی در تحلیل
    'چیز', 'دست', 'پای', 'سر', 'راه', 'کار', 'بار', 'جای',
    # حروف ربط/اضافه کوتاه که در word_freq می‌آیند
    'ای', 'می', 'ها', 'های',
}

# ─── مفاهیم مرکب — دسته‌بندی موضوعی ────────────────────────────────────────
# هر دسته یک رنگ و آیکون دارد؛ عبارات بر اساس احتمال ظهور در پیکره انتخاب شده‌اند
COMPOUND_CATEGORIES = {
    "نظام سیاسی و انقلاب": {
        "icon": "🏛️", "color": "#1091EC",
        "phrases": [
            "انقلاب اسلامی", "جمهوری اسلامی", "ولایت فقیه", "نظام اسلامی",
            "انقلاب فرهنگی", "مردم‌سالاری دینی", "حکومت اسلامی",
            "دولت اسلامی", "امام خمینی", "رهبر انقلاب", "نهضت اسلامی",
            "قانون اساسی", "ولی‌امر مسلمین", "نظام ولایی",
        ],
    },
    "دفاع، مقاومت و امنیت": {
        "icon": "⚔️", "color": "#EC1010",
        "phrases": [
            "دفاع مقدس", "جنگ تحمیلی", "مقاومت اسلامی", "جبهه مقاومت",
            "فرهنگ مقاومت", "مکتب شهادت", "فرهنگ ایثار", "فرهنگ شهادت",
            "مقاومت ملی", "امنیت ملی", "استقلال ملی", "اقتدار ملی",
            "نیروهای مسلح", "بسیج مستضعفین",
        ],
    },
    "دشمن، استکبار و جنگ نرم": {
        "icon": "🌐", "color": "#9c27b0",
        "phrases": [
            "استکبار جهانی", "رژیم صهیونیستی", "شیطان بزرگ", "جنگ نرم",
            "تهاجم فرهنگی", "ناتوی فرهنگی", "نفوذ دشمن", "جبهه استکبار",
            "نظام سلطه", "جنگ اقتصادی", "آمریکای جهانخوار",
            "توطئه دشمنان", "براندازی نرم", "جنگ ترکیبی",
        ],
    },
    "اقتصاد و تولید": {
        "icon": "💰", "color": "#f99400",
        "phrases": [
            "اقتصاد مقاومتی", "تولید داخلی", "اقتصاد اسلامی",
            "اقتصاد دانش‌بنیان", "جهش تولید", "رونق تولید",
            "خودکفایی اقتصادی", "عدالت اقتصادی", "اشتغال‌زایی",
            "سرمایه‌گذاری داخلی", "صنایع داخلی", "کشاورزی پایدار",
        ],
    },
    "علم، فناوری و پیشرفت": {
        "icon": "🔬", "color": "#00bcd4",
        "phrases": [
            "پیشرفت علمی", "جهاد علمی", "نهضت علمی", "دانش‌بنیان",
            "انرژی هسته‌ای", "برنامه هسته‌ای", "فناوری هسته‌ای",
            "علوم انسانی اسلامی", "فناوری پیشرفته", "جهاد دانشگاهی",
            "نخبگان علمی", "پژوهش علمی",
        ],
    },
    "فرهنگ، هنر و تمدن": {
        "icon": "🎭", "color": "#ff5722",
        "phrases": [
            "تمدن نوین اسلامی", "سبک زندگی اسلامی", "فرهنگ اسلامی",
            "هنر اسلامی", "ادبیات انقلاب", "تمدن اسلامی ایرانی",
            "هویت اسلامی", "ارزش‌های اسلامی", "معماری اسلامی",
            "موسیقی سنتی", "ادبیات فارسی", "شعر انقلابی",
        ],
    },
    "جامعه، خانواده و جوانان": {
        "icon": "👨‍👩‍👧", "color": "#4caf50",
        "phrases": [
            "جوانان مؤمن انقلابی", "نسل انقلاب", "عدالت اجتماعی",
            "حقوق بشر", "کرامت انسانی", "مسئولیت اجتماعی",
            "نقش زنان", "حقوق زنان", "خانواده اسلامی",
            "تربیت اسلامی", "آموزش و پرورش", "عدالت علوی",
        ],
    },
    "وحدت اسلامی و فلسطین": {
        "icon": "🕊️", "color": "#607d8b",
        "phrases": [
            "امت اسلامی", "وحدت اسلامی", "بیداری اسلامی", "اتحاد اسلامی",
            "جهان اسلام", "وحدت ملی", "وحدت امت",
            "آزادسازی قدس", "مسجد الاقصی", "حزب‌الله",
            "ملت فلسطین", "مقاومت فلسطین", "حق بازگشت",
            "انتفاضه فلسطین", "محاصره غزه",
        ],
    },
}

# لیست مسطح برای backward compatibility
COMPOUND_CONCEPTS = [
    p for cat in COMPOUND_CATEGORIES.values() for p in cat["phrases"]
]

THEMES = {
    # ── گروه الف: اسلام، دین، هویت دینی ──────────────────────────────────────
    "اسلام — عقیده، فقه و ایدئولوژی": {
        "icon": "☪️", "color": "#0e8a16",
        "words": ["اسلام", "دین", "شریعت", "فقه", "احکام", "حلال", "حرام",
                  "مسلمانان", "مسلمین", "اسلامی", "دینی", "خداوند", "الله", "پروردگار"],
        "note": "مرجع مقایسه: مفاهیم دینی اسلامی خامنه‌ای در برابر مفاهیم ملی ایرانی",
    },
    "قرآن، معنویت و عبادت": {
        "icon": "📖", "color": "#2e7d32",
        "words": ["قرآن", "ایمان", "خدا", "پیامبر", "نماز", "روزه",
                  "حج", "معنویت", "تقوا", "عبادت", "دعا", "توسل", "ذکر"],
        "note": "ارتباط معنوی فردی و جمعی با دین",
    },
    "تشیع، اهل‌بیت و عزاداری": {
        "icon": "🕌", "color": "#1b5e20",
        "words": ["شیعه", "تشیع", "امام", "اهل‌بیت", "علی", "حسین",
                  "کربلا", "عاشورا", "محرم", "عزاداری", "زیارت", "حضرت",
                  "فاطمه", "زهرا", "مهدی", "موعود"],
        "note": "گفتمان خاص شیعی — قابل مقایسه با اسلام عمومی",
    },
    # ── گروه ب: «ایران در گفتار خامنه‌ای» — ۷ مضمون برای تحلیل هویت ایرانی ──
    # این گروه طراحی شده تا پاسخ دهد: خامنه‌ای از چه «ایرانی» سخن می‌گوید؟
    "ایران — هویت ملی و میهن‌دوستی": {
        "icon": "🇮🇷", "color": "#c62828",
        "words": ["ملت", "مردم", "ایران", "ایرانی", "ایرانیان", "میهن",
                  "وطن", "ملی", "کشور", "استقلال", "حاکمیت", "افتخار",
                  "سرزمین", "خاک"],
        "note": "گفتمان شهروندی-ملی: وقتی خامنه‌ای از «ایران» به‌عنوان وطن سخن می‌گوید — نه در چارچوب اسلامی",
    },
    "ایران باستان و تمدن پیش از اسلام": {
        "icon": "🏛️", "color": "#8d6e63",
        "words": ["کوروش", "داریوش", "هخامنشی", "ساسانی", "اشکانی",
                  "باستان", "تخت‌جمشید", "پارس", "ماد", "آریا",
                  "ایران‌باستان", "پارسیان", "مادها", "هخامنش",
                  "اردشیر", "خشایارشا", "انوشیروان", "نوشیروان"],
        "note": "آیا خامنه‌ای از ایران پیش از اسلام یاد می‌کند؟ کوروش چه جایگاهی دارد؟ این یکی از مهم‌ترین شاخص‌های هویت ملی در گفتمان اوست",
    },
    "ادبیات و میراث فرهنگی کلاسیک ایران": {
        "icon": "📜", "color": "#5d4037",
        "words": ["فردوسی", "حافظ", "سعدی", "مولانا", "رومی", "نظامی",
                  "خیام", "شاهنامه", "دیوان", "غزل", "مثنوی", "رودکی",
                  "ابن‌سینا", "بیرونی", "خوارزمی", "ادبیات‌فارسی",
                  "شعر‌فارسی", "حماسه"],
        "note": "خامنه‌ای شخصاً شاعر است — از کدام ادبا و دانشمندان کلاسیک ایران نام می‌برد؟",
    },
    "تاریخ سیاسی ایران — صفوی تا پهلوی": {
        "icon": "⚜️", "color": "#4e342e",
        "words": ["صفوی", "صفویه", "قاجار", "پهلوی", "مشروطه",
                  "رضاشاه", "محمدرضا", "مصدق", "کودتا", "ملی‌شدن",
                  "انگلیس", "روسیه", "استعمار", "قرارداد", "عثمانی",
                  "افشار", "زند", "نادرشاه", "کریم‌خان"],
        "note": "خامنه‌ای تاریخ سیاسی ایران را چگونه روایت می‌کند؟ کدام دوران را مثبت و کدام را منفی می‌بیند؟",
    },
    "هنر و فرهنگ معاصر — خارج از چارچوب نظام": {
        "icon": "🎨", "color": "#546e7a",
        "words": ["هدایت", "شاملو", "فروغ", "نیما", "صادق‌هدایت",
                  "روشنفکر", "روشنفکری", "سکولار", "لائیک",
                  "غرب‌زده", "غرب‌زدگی", "تجددطلب"],
        "note": "فرهنگیان و روشنفکران غیرانقلابی — خامنه‌ای از آن‌ها یاد می‌کند؟ با چه لحنی؟ (تعداد کم = یافته معنادار)",
    },
    "هنر، ادبیات و فرهنگ مورد تأیید نظام": {
        "icon": "🎭", "color": "#37474f",
        "words": ["هنر", "هنرمند", "هنر‌اسلامی", "ادبیات", "شاعر",
                  "شعر‌انقلاب", "سینما", "موسیقی", "معماری",
                  "نقاشی", "تئاتر", "خوشنویسی", "ادیب",
                  "هنر‌انقلابی", "فرهنگ‌اسلامی"],
        "note": "هنر و ادبیاتی که خامنه‌ای می‌پذیرد و ترویج می‌کند — معیار پذیرش چیست؟",
    },
    "ایران اسلامی — پیوند ایران و تشیع": {
        "icon": "🔷", "color": "#6a1b9a",
        "words": ["ایران‌اسلامی", "تشیع‌ایرانی", "اسلامی‌ایرانی",
                  "فرهنگ‌ایرانی‌اسلامی", "هویت‌اسلامی", "ارزش‌های‌اسلامی",
                  "تمدن‌نوین", "اسلام‌ناب", "نوروز"],
        "note": "ترکیب هویت ایرانی و اسلامی در گفتمان خامنه‌ای — آیا این دو را یکی می‌داند یا متمایز؟",
    },
    # ── گروه ج: نظام سیاسی ────────────────────────────────────────────────────
    "جمهوری اسلامی — نظام و حکومت": {
        "icon": "🏛️", "color": "#1091EC",
        "words": ["جمهوری", "نظام", "حکومت", "دولت", "مجلس", "قوه",
                  "قانون‌اساسی", "مسئولان", "مدیریت", "اداره",
                  "انتخابات", "رأی", "مردم‌سالاری", "دموکراسی"],
        "note": "جمهوری اسلامی به‌عنوان یک نهاد سیاسی",
    },
    "رهبری و ولایت فقیه": {
        "icon": "👑", "color": "#ff9800",
        "words": ["رهبر", "ولایت", "ولی‌فقیه", "اطاعت", "تبعیت", "بیعت",
                  "امام", "خمینی", "امام‌خمینی", "رهبری"],
        "note": "مشروعیت دینی-سیاسی رهبری",
    },
    "انقلاب اسلامی — روایت تاریخی": {
        "icon": "🔥", "color": "#e65100",
        "words": ["انقلاب", "انقلابی", "پیروزی‌انقلاب", "انقلاب‌اسلامی",
                  "مبارزه", "نهضت", "قیام", "شاه", "رژیم‌سابق",
                  "مبارزان", "زندان", "تبعید"],
        "note": "روایت خامنه‌ای از تاریخ انقلاب",
    },
    # ── گروه د: تهدید و دفاع ─────────────────────────────────────────────────
    "دشمن — آمریکا، استکبار، غرب": {
        "icon": "🌐", "color": "#9c27b0",
        "words": ["آمریکا", "استکبار", "غرب", "غربی", "سلطه",
                  "تحریم", "نفوذ", "توطئه", "دشمن", "ابرقدرت",
                  "امپریالیسم", "استعمار"],
        "note": "گفتمان ضد استکباری",
    },
    "رژیم صهیونیستی و فلسطین": {
        "icon": "🕊️", "color": "#880e4f",
        "words": ["صهیونیسم", "صهیونیست", "اسرائیل", "فلسطین", "غزه",
                  "قدس", "اقصی", "مسجدالاقصی", "آزادسازی", "مقاومت"],
        "note": "موضع خامنه‌ای درباره فلسطین و اسرائیل",
    },
    "مقاومت، جهاد و شهادت": {
        "icon": "⚔️", "color": "#EC1010",
        "words": ["مقاومت", "جهاد", "شهادت", "شهید", "ایثار",
                  "فداکاری", "رزمنده", "بسیج", "سپاه", "دفاع"],
        "note": "فرهنگ مقاومت و شهادت‌طلبی",
    },
    "جنگ تحمیلی و دفاع مقدس": {
        "icon": "🏅", "color": "#f44336",
        "words": ["جنگ", "دفاع‌مقدس", "جانباز", "آزاده", "خرمشهر",
                  "اروندرود", "فتح", "عملیات", "هشت‌سال", "صدام"],
        "note": "حافظه جنگ ۸ ساله در گفتار خامنه‌ای",
    },
    # ── گروه ه: اقتصاد و علم ─────────────────────────────────────────────────
    "اقتصاد، تولید و معیشت": {
        "icon": "💰", "color": "#f99400",
        "words": ["اقتصاد", "تولید", "اشتغال", "فقر", "بیکاری",
                  "سرمایه‌گذاری", "صنعت", "کشاورزی", "معیشت", "تورم",
                  "بازار", "صادرات", "واردات", "خودکفایی"],
        "note": "اقتصاد مقاومتی و تولید داخلی",
    },
    "علم، فناوری و دانشگاه": {
        "icon": "🔬", "color": "#00bcd4",
        "words": ["علم", "دانش", "فناوری", "دانشگاه", "پژوهش",
                  "دانشجو", "نوآوری", "اختراع", "هسته‌ای", "فضا",
                  "دانش‌بنیان", "محقق", "استاد"],
        "note": "جهاد علمی و پیشرفت فناوری",
    },
    # ── گروه و: اجتماع و فرهنگ ───────────────────────────────────────────────
    "فرهنگ، رسانه و تهاجم فرهنگی": {
        "icon": "🎭", "color": "#ff5722",
        "words": ["فرهنگ", "رسانه", "تبلیغات", "هجمه", "تهاجم",
                  "جنگ‌نرم", "ناتوی‌فرهنگی", "ماهواره", "اینترنت",
                  "سینما", "هنر", "موسیقی"],
        "note": "نگرانی خامنه‌ای از جنگ نرم فرهنگی",
    },
    "خانواده، زنان و تربیت": {
        "icon": "👨‍👩‍👧", "color": "#ad1457",
        "words": ["خانواده", "زنان", "مادر", "پدر", "فرزند",
                  "تربیت", "حجاب", "عفاف", "ازدواج", "نسل"],
        "note": "گفتمان خانوادگی و جنسیتی",
    },
    "جوانان، دانشجو و نسل آینده": {
        "icon": "🌱", "color": "#4caf50",
        "words": ["جوان", "جوانان", "نسل", "آینده", "امید",
                  "دانشجو", "طلبه", "تحصیل", "انرژی", "خلاقیت"],
        "note": "خطاب مستقیم به نسل جوان",
    },
    # ── گروه ز: عدالت و حقوق ─────────────────────────────────────────────────
    "عدالت، حقوق و مظلومیت": {
        "icon": "⚖️", "color": "#795548",
        "words": ["عدالت", "حق", "مسئولیت", "تکلیف",
                  "مظلوم", "ظلم", "محروم", "برابری", "انصاف",
                  "فساد", "رشوه", "تبعیض"],
        "note": "مفاهیم عدالت‌خواهانه در گفتار خامنه‌ای",
    },
    # ── گروه ح: جهان اسلام و امت ─────────────────────────────────────────────
    "امت اسلامی، وحدت و بیداری": {
        "icon": "🤝", "color": "#607d8b",
        "words": ["وحدت", "امت", "مسلمین", "برادری",
                  "اتحاد", "بیداری‌اسلامی", "اتحاد‌اسلامی",
                  "جهان‌اسلام", "کشورهای‌اسلامی"],
        "note": "پروژه وحدت امت اسلامی",
    },
    # ── گروه ط: امنیت و سیاست ────────────────────────────────────────────────
    "امنیت ملی و استقلال": {
        "icon": "🛡️", "color": "#37474f",
        "words": ["امنیت", "استقلال", "حاکمیت", "تمامیت",
                  "دفاع", "ارتش", "نیروهای‌مسلح", "اقتدار"],
        "note": "گفتمان امنیت ملی",
    },
    "سیاست خارجی و دیپلماسی": {
        "icon": "🌍", "color": "#3f51b5",
        "words": ["دیپلماسی", "مذاکره", "برجام", "توافق",
                  "تعامل", "منطقه", "روابط", "سازمان‌ملل",
                  "بین‌الملل", "همسایه"],
        "note": "روابط بین‌الملل در گفتار خامنه‌ای",
    },
    "پیشرفت، آبادانی و سازندگی": {
        "icon": "🚀", "color": "#009688",
        "words": ["پیشرفت", "توسعه", "آبادانی", "سازندگی",
                  "عمران", "رفاه", "ساخت", "بازسازی", "اشتغال"],
        "note": "گفتمان توسعه و سازندگی",
    },
}

# ─── پیکربندی خروجی نمودار ──────────────────────────────────────────────────
CHART_CONFIG = {
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'chart',
        'height': 600,
        'width': 1200,
        'scale': 2,
    },
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
}

# ─── تابع ناوبری ─────────────────────────────────────────────────────────────
def go_to_search(keyword: str):
    st.session_state['kw'] = keyword
    st.switch_page("pages/1_جستجو.py")


# ─── اتصال به پایگاه داده ───────────────────────────────────────────────────
conn = get_conn()
if not is_built():
    st.warning("فهرست واژگانی هنوز ساخته نشده است. ابتدا صفحه هم‌نشینی را باز کنید.")
    st.page_link("pages/6_هم‌نشینی.py", label="ساخت فهرست واژگانی ←")
    st.stop()

# ─── سایدبار ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="color:#fff;font-size:15px;font-weight:700;margin-bottom:12px">⚙️ فیلترها</div>',
        unsafe_allow_html=True,
    )
    yr1, yr2 = st.slider("بازه سال‌های هجری شمسی", 1355, 1404, (1355, 1404))
    top_n = st.slider(
        "تعداد کلیدواژه در ابر کلمات و رتبه‌بندی",
        30, 300, 100,
        help="تعداد پرتکرارترین کلمات که در تب‌های «ابر کلمات» و «رتبه‌بندی» نمایش داده می‌شود. روی تب «مضامین» و «مقایسه» تأثیر ندارد.",
    )
    min_docs = st.slider(
        "حداقل اسناد (فیلتر فهرست)",
        5, 500, 50,
        help="کلمه‌هایی که در کمتر از این تعداد سند ظاهر شده‌اند از فهرست ابر کلمات و رتبه‌بندی حذف می‌شوند.",
    )

    st.markdown("---")
    st.markdown('<div style="color:#aaccdd;font-size:12px;font-weight:600;margin-bottom:4px">نوع محتوا</div>', unsafe_allow_html=True)
    tier_option = st.radio(
        "نوع محتوا",
        ["بیانات مستقیم (tier1)", "سخنرانی‌ها (tier1+2)", "همه محتوا"],
        index=0,
        label_visibility="collapsed",
        key="tier_filter"
    )
    if tier_option == "بیانات مستقیم (tier1)":
        sel_tiers = ("tier1",)
    elif tier_option == "سخنرانی‌ها (tier1+2)":
        sel_tiers = ("tier1", "tier2")
    else:
        sel_tiers = ()   # empty = no filter = all tiers

    tier_labels = {
        "tier1": "فقط بیانات مستقیم خامنه‌ای",
        "tier1+tier2": "سخنرانی‌ها (مستقیم + ویرایش‌شده)",
        "all": "همه محتوا (شامل گزارش راویان)",
    }
    if sel_tiers == ("tier1",):
        _tier_desc = tier_labels["tier1"]
    elif sel_tiers == ("tier1", "tier2"):
        _tier_desc = tier_labels["tier1+tier2"]
    else:
        _tier_desc = tier_labels["all"]
    st.markdown(
        f'<div style="color:#88aacc;font-size:11px;margin-top:4px">📌 {_tier_desc}</div>',
        unsafe_allow_html=True,
    )

date_from = f"{yr1}0101"
date_to   = f"{yr2}1299"

# ─── توابع کمکی فیلتر tier ───────────────────────────────────────────────────

def _tier_clause(tiers: tuple) -> tuple:
    """SQL WHERE fragment + params for tier filter (uses d. alias)"""
    if not tiers:
        return "", []
    ph = ",".join("?" * len(tiers))
    return f" AND d.analytical_tier IN ({ph})", list(tiers)


def _tier_clause_simple(tiers: tuple) -> tuple:
    """SQL WHERE fragment + params for tier filter (no table alias)"""
    if not tiers:
        return "", []
    ph = ",".join("?" * len(tiers))
    return f" AND analytical_tier IN ({ph})", list(tiers)


# ─── توابع داده ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_top_keywords(_conn, date_from: str, date_to: str, top_n: int, min_docs: int, tiers: tuple = ()):
    """بارگذاری کلیدواژه‌های برتر از word_freq با فیلترهای محتوایی
    توجه: word_freq یک ایندکس از پیش‌ساخته است و اطلاعات tier ندارد؛
    فیلتر tier برای این تابع اعمال نمی‌شود.
    """
    total_docs_all = _conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    rows = _conn.execute(
        "SELECT word, total_freq, doc_freq FROM word_freq ORDER BY total_freq DESC LIMIT 10000"
    ).fetchall()

    result = []
    for row in rows:
        word, total_freq, doc_freq = row[0], row[1], row[2]
        # فیلتر حداقل طول (۳ کاراکتر)
        if len(word) < 3:
            continue
        # فیلتر stop words
        if normalize_fa(word) in FA_STOP:
            continue
        if word in EXTRA_STOP:
            continue
        # فیلتر عددی
        if any(c.isdigit() for c in word):
            continue
        # فیلتر لاتین
        if any(ord(c) < 128 and c.isalpha() for c in word):
            continue
        # فیلتر حداقل اسناد
        if doc_freq < min_docs:
            continue
        result.append({
            "word": word,
            "total_freq": total_freq,
            "doc_freq": doc_freq,
            "pct_docs": round(100.0 * doc_freq / total_docs_all, 2) if total_docs_all else 0,
        })
        if len(result) >= top_n:
            break

    return result


@st.cache_data(ttl=600)
def get_total_docs(_conn):
    return _conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


@st.cache_data(ttl=300)
def get_keyword_stats(_conn, keyword: str, tiers: tuple = ()):
    """آمار کلی یک کلیدواژه"""
    tier_sql, tier_params = _tier_clause_simple(tiers)

    # کل اسناد در این فیلتر
    total_docs = _conn.execute(
        f"SELECT COUNT(*) FROM documents WHERE 1=1{tier_sql}",
        tier_params,
    ).fetchone()[0]

    # تعداد اسناد حاوی کلیدواژه
    doc_count = _conn.execute(
        f"SELECT COUNT(*) FROM documents WHERE full_text LIKE ?{tier_sql}",
        [f"%{keyword}%"] + tier_params,
    ).fetchone()[0]

    # فراوانی کل = چند بار عبارت در کل متون تکرار شده
    # برای کلمات تکی از word_freq، برای عبارات چندکلمه‌ای محاسبه مستقیم
    freq_row = _conn.execute(
        "SELECT total_freq FROM word_freq WHERE word = ?", (keyword,)
    ).fetchone()

    if freq_row:
        # کلمه تکی — از ایندکس آماده
        total_occurrences = freq_row[0]
    else:
        # عبارت چندکلمه‌ای — شمارش دستی با تقسیم طول رشته
        kw_len = len(keyword)
        row = _conn.execute(
            f"""
            SELECT SUM(
                (length(full_text) - length(replace(full_text, ?, ''))) / {kw_len}
            )
            FROM documents
            WHERE full_text LIKE ?{tier_sql}
            """,
            [keyword, f"%{keyword}%"] + tier_params,
        ).fetchone()
        total_occurrences = row[0] or doc_count

    return {
        "total_occurrences": total_occurrences,   # دفعات تکرار در متون
        "doc_count":         doc_count,            # تعداد اسناد منحصر
        "pct_docs":          round(100.0 * doc_count / total_docs, 2) if total_docs else 0,
        "total_docs":        total_docs,
    }


@st.cache_data(ttl=300)
def get_keyword_rank(_conn, keyword: str):
    """رتبه کلیدواژه در جدول word_freq"""
    rows = _conn.execute(
        "SELECT word FROM word_freq ORDER BY total_freq DESC LIMIT 1000"
    ).fetchall()
    for i, row in enumerate(rows, 1):
        if row[0] == keyword:
            return i
    return None


@st.cache_data(ttl=600)
def get_yearly_total_counts(_conn, tiers: tuple = ()):
    """تعداد کل اسناد به ازای هر سال — برای نرمال‌سازی"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT substr(date_persian, 1, 4) AS y, COUNT(*) AS cnt
        FROM documents
        WHERE date_persian GLOB '1[3-4][0-9][0-9]*'
        {tier_sql}
        GROUP BY y ORDER BY y
        """,
        tier_params,
    ).fetchall()
    return {r[0]: r[1] for r in rows}


@st.cache_data(ttl=300)
def get_keyword_trend(_conn, keyword: str, tiers: tuple = ()):
    """روند سالانه — هم عدد مطلق هم درصد نرمال‌شده"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT substr(date_persian, 1, 4) AS y, COUNT(*) AS cnt
        FROM documents
        WHERE full_text LIKE ?
        {tier_sql}
        GROUP BY y
        ORDER BY y
        """,
        [f"%{keyword}%"] + tier_params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


@st.cache_data(ttl=300)
def get_keyword_trend_ranged(_conn, keyword: str, date_from: str, date_to: str, tiers: tuple = ()):
    """روند سالانه در بازه زمانی"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT substr(date_persian, 1, 4) AS y, COUNT(*) AS cnt
        FROM documents
        WHERE full_text LIKE ?
          AND date_persian BETWEEN ? AND ?
        {tier_sql}
        GROUP BY y
        ORDER BY y
        """,
        [f"%{keyword}%", date_from, date_to] + tier_params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


@st.cache_data(ttl=300)
def get_keyword_tone(_conn, keyword: str, tiers: tuple = ()):
    """توزیع لحن اسناد حاوی کلیدواژه"""
    tier_sql, tier_params = _tier_clause(tiers)
    rows = _conn.execute(
        f"""
        SELECT value, COUNT(*) AS cnt
        FROM documents d
        JOIN doc_tags t ON d.doc_id = t.doc_id,
        json_each(t.tag_tone)
        WHERE d.full_text LIKE ?
        {tier_sql}
        GROUP BY value
        ORDER BY cnt DESC
        """,
        [f"%{keyword}%"] + tier_params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows if r[0]]


@st.cache_data(ttl=300)
def get_keyword_genre(_conn, keyword: str, tiers: tuple = ()):
    """توزیع ژانر اسناد حاوی کلیدواژه"""
    tier_sql, tier_params = _tier_clause(tiers)
    rows = _conn.execute(
        f"""
        SELECT tag_form_genre, COUNT(*) AS cnt
        FROM documents d
        JOIN doc_tags t ON d.doc_id = t.doc_id
        WHERE d.full_text LIKE ?
          AND tag_form_genre IS NOT NULL
        {tier_sql}
        GROUP BY tag_form_genre
        ORDER BY cnt DESC
        """,
        [f"%{keyword}%"] + tier_params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows if r[0]]


@st.cache_data(ttl=300)
def get_keyword_period(_conn, keyword: str, tiers: tuple = ()):
    """توزیع دوره‌ای اسناد حاوی کلیدواژه"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT period_label, COUNT(*) AS cnt
        FROM documents
        WHERE full_text LIKE ?
          AND period_label IS NOT NULL
        {tier_sql}
        GROUP BY period_label
        ORDER BY cnt DESC
        """,
        [f"%{keyword}%"] + tier_params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows if r[0]]


@st.cache_data(ttl=300)
def get_keyword_snippets(_conn, keyword: str, tiers: tuple = ()):
    """قطعات متنی حاوی کلیدواژه"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT doc_id, title, date_persian,
               substr(full_text, MAX(1, instr(full_text, ?)-100), 300) AS snippet
        FROM documents
        WHERE full_text LIKE ?
        {tier_sql}
        LIMIT 5
        """,
        [keyword, f"%{keyword}%"] + tier_params,
    ).fetchall()
    return [dict(r) for r in rows]


@st.cache_data(ttl=300)
def get_keyword_docs_csv(_conn, keyword: str, tiers: tuple = ()):
    """دانلود اسناد حاوی کلیدواژه به CSV"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    rows = _conn.execute(
        f"""
        SELECT doc_id, title, date_persian, period_label, word_count
        FROM documents
        WHERE full_text LIKE ?
        {tier_sql}
        ORDER BY date_persian
        """,
        [f"%{keyword}%"] + tier_params,
    ).fetchall()
    df = pd.DataFrame(rows, columns=["doc_id", "عنوان", "تاریخ", "دوره", "تعداد کلمات"])
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_data(ttl=600)
def get_compound_counts(_conn, phrases: tuple, tiers: tuple = ()):
    """شمارش هر مفهوم مرکب در کل پیکره"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    results = {}
    for phrase in phrases:
        cnt = _conn.execute(
            f"SELECT COUNT(*) FROM documents WHERE full_text LIKE ?{tier_sql}",
            [f"%{phrase}%"] + tier_params,
        ).fetchone()[0]
        results[phrase] = cnt
    return results


@st.cache_data(ttl=600)
def get_theme_scores(_conn, themes_data: tuple):
    """جمع بسامد کلمات هر مضمون از word_freq"""
    results = {}
    for theme_name, words_tuple in themes_data:
        if not words_tuple:
            results[theme_name] = 0
            continue
        placeholders = ",".join("?" * len(words_tuple))
        total = _conn.execute(
            f"SELECT COALESCE(SUM(total_freq), 0) FROM word_freq WHERE word IN ({placeholders})",
            list(words_tuple),
        ).fetchone()[0]
        results[theme_name] = total
    return results


@st.cache_data(ttl=300)
def get_multi_keyword_trend(_conn, keywords: tuple, tiers: tuple = ()):
    """روند سالانه چند کلیدواژه — برمی‌گرداند: dict[kw -> dict[year -> count]]"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    result = {}
    for kw in keywords:
        rows = _conn.execute(
            f"""
            SELECT substr(date_persian, 1, 4) AS y, COUNT(*) AS cnt
            FROM documents
            WHERE full_text LIKE ?
              AND date_persian GLOB '1[3-4][0-9][0-9]*'
            {tier_sql}
            GROUP BY y ORDER BY y
            """,
            [f"%{kw}%"] + tier_params,
        ).fetchall()
        result[kw] = {r[0]: r[1] for r in rows}
    return result


@st.cache_data(ttl=300)
def get_keyword_period_normalized(_conn, keywords: tuple, tiers: tuple = ()):
    """مقایسه دوره‌ای نرمال‌شده — count / total_in_period"""
    tier_sql, tier_params = _tier_clause_simple(tiers)
    # تعداد کل اسناد هر دوره
    period_totals_rows = _conn.execute(
        f"""
        SELECT period_label, COUNT(*) AS cnt
        FROM documents
        WHERE period_label IS NOT NULL
        {tier_sql}
        GROUP BY period_label
        """,
        tier_params,
    ).fetchall()
    period_totals = {r[0]: r[1] for r in period_totals_rows}

    from utils.charts import PERIOD_FA
    result = {}  # dict[kw -> dict[period_label -> pct]]
    for kw in keywords:
        rows = _conn.execute(
            f"""
            SELECT period_label, COUNT(*) AS cnt
            FROM documents
            WHERE full_text LIKE ?
              AND period_label IS NOT NULL
            {tier_sql}
            GROUP BY period_label
            """,
            [f"%{kw}%"] + tier_params,
        ).fetchall()
        kw_dict = {}
        for r in rows:
            p, c = r[0], r[1]
            total = period_totals.get(p, 1) or 1
            kw_dict[PERIOD_FA.get(p, p)] = round(100.0 * c / total, 2)
        result[kw] = kw_dict
    return result


@st.cache_data(ttl=300)
def get_keywords_tone_compare(_conn, keywords: tuple, tiers: tuple = ()):
    """توزیع لحن برای هر کلیدواژه — dict[kw -> list[(tone, count)]]"""
    tier_sql, tier_params = _tier_clause(tiers)
    result = {}
    for kw in keywords:
        rows = _conn.execute(
            f"""
            SELECT value, COUNT(*) AS cnt
            FROM documents d
            JOIN doc_tags t ON d.doc_id = t.doc_id,
            json_each(t.tag_tone)
            WHERE d.full_text LIKE ?
            {tier_sql}
            GROUP BY value ORDER BY cnt DESC LIMIT 8
            """,
            [f"%{kw}%"] + tier_params,
        ).fetchall()
        result[kw] = [(r[0], r[1]) for r in rows if r[0]]
    return result


@st.cache_data(ttl=300)
def get_keywords_topics_compare(_conn, keywords: tuple, tiers: tuple = ()):
    """همرخداد موضوعات برای هر کلیدواژه — dict[kw -> list[(topic, count)]]"""
    tier_sql, tier_params = _tier_clause(tiers)
    result = {}
    for kw in keywords:
        rows = _conn.execute(
            f"""
            SELECT value, COUNT(*) AS cnt
            FROM documents d
            JOIN doc_tags t ON d.doc_id = t.doc_id,
            json_each(t.tag_topics)
            WHERE d.full_text LIKE ?
            {tier_sql}
            GROUP BY value ORDER BY cnt DESC LIMIT 12
            """,
            [f"%{kw}%"] + tier_params,
        ).fetchall()
        result[kw] = [(r[0], r[1]) for r in rows if r[0]]
    return result


# ─── بارگذاری اولیه داده ────────────────────────────────────────────────────
keywords_data = get_top_keywords(conn, date_from, date_to, top_n, min_docs, sel_tiers)

if not keywords_data:
    st.warning("کلیدواژه‌ای با این معیارها یافت نشد. فیلترها را تغییر دهید.")
    st.stop()

words_list = [d["word"] for d in keywords_data]
freqs      = [d["total_freq"] for d in keywords_data]

# ─── تب‌ها ───────────────────────────────────────────────────────────────────
tab_compare, tab_cloud, tab_rank, tab_trend, tab_compound, tab_themes = st.tabs([
    "📊 مقایسه‌ی کلیدواژه‌ها",
    "☁️ ابر کلمات",
    "📋 رتبه‌بندی",
    "📈 روند زمانی",
    "🔗 مفاهیم مرکب",
    "🎯 مضامین اصلی",
])

# ════════════════════════════════════════════════════════════════════════════
# Tab 1: مقایسه‌ی کلیدواژه‌ها
# ════════════════════════════════════════════════════════════════════════════

# ─ تبدیل رنگ hex به rgba (برای fillcolor Plotly) ─────────────────────────
def _hex_rgba(hex_color: str, alpha: float = 0.13) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


with tab_compare:
    st.markdown(
        f'<div style="direction:rtl;font-size:15px;font-weight:700;color:{BRAND_DARK};'
        f'margin-bottom:4px">📊 مقایسه‌ی کلیدواژه‌ها در طول زمان</div>'
        f'<div style="direction:rtl;font-size:13px;color:#6a8a9a;margin-bottom:16px">'
        f'تا ۵ کلیدواژه یا عبارت وارد کنید و روند، دوره‌ها، لحن و موضوعات همراه را مقایسه کنید.</div>',
        unsafe_allow_html=True,
    )

    # ─ ورودی کلیدواژه‌ها ────────────────────────────────────────────────────
    _COLORS = ['#E91E63', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0']

    # ── مدیریت preset از دکمه‌های تب‌های دیگر ──────────────────────────────
    # وقتی دکمه از themes/rank پرسد، یک کلید _cmp_preset می‌گذارد (نه کلید widget)
    # اینجا قبل از ساخت widget ها آن را می‌خوانیم
    _just_loaded = False
    if "_cmp_preset" in st.session_state:
        _preset_vals = st.session_state.pop("_cmp_preset")
        # شماره نسخه را بالا می‌بریم تا widget های جدید با value تازه بسازیم
        st.session_state["_cmp_v"] = st.session_state.get("_cmp_v", 0) + 1
        st.session_state["_cmp_values"] = _preset_vals
        _just_loaded = True

    _cmp_v      = st.session_state.get("_cmp_v", 0)
    _cmp_values = st.session_state.get("_cmp_values", ["انقلاب اسلامی", "مقاومت", "", "", ""])

    if _just_loaded:
        loaded_kws = [w for w in _cmp_values if w]
        st.success(f"✅ کلیدواژه‌های مضمون بارگذاری شدند: **{' | '.join(loaded_kws)}**")

    inp_cols = st.columns(5)
    cmp_kws_raw = []
    for i, col in enumerate(inp_cols):
        _default_i = _cmp_values[i] if i < len(_cmp_values) else ""
        with col:
            v = st.text_input(
                f"کلیدواژه {i+1}",
                value=_default_i,
                placeholder="کلیدواژه...",
                key=f"cmp_kw_{i}_{_cmp_v}",   # نسخه‌دار → بدون تداخل
                label_visibility="visible",
            )
            if v and v.strip():
                cmp_kws_raw.append(v.strip())

    cmp_kws = tuple(dict.fromkeys(cmp_kws_raw))  # حذف تکراری، حفظ ترتیب

    if not cmp_kws:
        st.info("حداقل یک کلیدواژه وارد کنید.")
        st.stop()

    # ─ بارگذاری داده ────────────────────────────────────────────────────────
    with st.spinner("در حال بارگذاری داده‌ها..."):
        yearly_totals   = get_yearly_total_counts(conn, sel_tiers)
        trend_data      = get_multi_keyword_trend(conn, cmp_kws, sel_tiers)
        period_norm     = get_keyword_period_normalized(conn, cmp_kws, sel_tiers)
        tone_data_all   = get_keywords_tone_compare(conn, cmp_kws, sel_tiers)
        topics_data_all = get_keywords_topics_compare(conn, cmp_kws, sel_tiers)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # بخش ۱: روند نرمال‌شده
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:4px">'
        f'📈 روند زمانی نرمال‌شده</div>'
        f'<div style="direction:rtl;font-size:12px;color:#888;margin-bottom:8px">'
        f'محور عمودی: درصد اسناد هر سال که حاوی این کلیدواژه هستند (نرمال‌شده برای جبران نابرابری حجم پیکره)</div>',
        unsafe_allow_html=True,
    )

    cmp_mode = st.radio(
        "نوع نمایش",
        ["درصد نرمال‌شده (پیشنهادی)", "تعداد مطلق اسناد"],
        horizontal=True, key="cmp_trend_mode",
    )
    use_pct_cmp = cmp_mode.startswith("درصد")

    # حداقل تعداد سند لازم در هر سال تا نقطه‌ای در نمودار نمایش داده شود
    # سال‌هایی با کمتر از این تعداد سند گمراه‌کننده‌اند (مثلاً ۱ سند = ۱۰۰٪)
    _MIN_DOCS_PER_YEAR = 10

    fig_cmp = go.Figure()
    for i, kw in enumerate(cmp_kws):
        yd = trend_data.get(kw, {})
        # فقط سال‌هایی که حداقل _MIN_DOCS_PER_YEAR سند در کل پیکره دارند
        years = sorted(
            y for y in yd
            if y and len(y) == 4
            and yearly_totals.get(y, 0) >= _MIN_DOCS_PER_YEAR
        )
        counts = [yd[y] for y in years]
        if use_pct_cmp:
            y_vals = [
                round(100.0 * yd[y] / yearly_totals[y], 2)
                for y in years
            ]
            hover_tmpl = f"<b>{kw}</b><br>سال: %{{x}}<br>درصد: %{{y:.2f}}٪<extra></extra>"
            y_axis_lbl = "درصد اسناد آن سال (%)"
        else:
            y_vals = counts
            hover_tmpl = f"<b>{kw}</b><br>سال: %{{x}}<br>اسناد: %{{y:,}}<extra></extra>"
            y_axis_lbl = "تعداد اسناد"

        fig_cmp.add_trace(go.Scatter(
            x=years, y=y_vals,
            mode="lines+markers",
            name=kw,
            line=dict(color=_COLORS[i % len(_COLORS)], width=2.5),
            marker=dict(size=6),
            hovertemplate=hover_tmpl,
        ))

    fig_cmp.update_layout(
        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
        xaxis=dict(title="سال هجری شمسی", showgrid=True, gridcolor="#e0e8ee"),
        yaxis=dict(title=y_axis_lbl, showgrid=True, gridcolor="#e0e8ee"),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
                    font=dict(family="Vazirmatn", size=12)),
        margin=dict(l=50, r=20, t=20, b=60),
        height=380,
        hovermode="x unified",
        font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(fig_cmp, use_container_width=True,
                    config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'compare_trend'}})

    if use_pct_cmp:
        st.caption("ℹ️ ۴۷٪ از اسناد پیکره متعلق به دهه ۱۳۹۰ است. نمودار نرمال‌شده این تفاوت را جبران می‌کند و مقایسه منصفانه‌تری ارائه می‌دهد.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # بخش ۲: مقایسه دوره‌ای نرمال‌شده
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:4px">'
        f'🗓️ مقایسه دوره‌ای (نرمال‌شده)</div>'
        f'<div style="direction:rtl;font-size:12px;color:#888;margin-bottom:8px">'
        f'در هر دوره سیاسی، چند درصد از اسناد آن دوره حاوی این کلیدواژه است؟</div>',
        unsafe_allow_html=True,
    )

    from utils.charts import PERIOD_FA
    all_periods_ordered = list(PERIOD_FA.values())

    fig_period_cmp = go.Figure()
    for i, kw in enumerate(cmp_kws):
        kw_periods = period_norm.get(kw, {})
        x_vals = [p for p in all_periods_ordered if p in kw_periods]
        y_vals = [kw_periods[p] for p in x_vals]
        fig_period_cmp.add_trace(go.Bar(
            name=kw,
            x=x_vals,
            y=y_vals,
            marker_color=_COLORS[i % len(_COLORS)],
            hovertemplate=f"<b>{kw}</b><br>دوره: %{{x}}<br>درصد: %{{y:.2f}}٪<extra></extra>",
            text=[f"{v:.1f}٪" for v in y_vals],
            textposition="outside",
        ))

    fig_period_cmp.update_layout(
        barmode="group",
        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
        xaxis=dict(
            title="دوره سیاسی",
            tickangle=-35,
            tickfont=dict(family="Vazirmatn", size=10),
            showgrid=False,
        ),
        yaxis=dict(title="درصد اسناد دوره (%)", showgrid=True, gridcolor="#e0e8ee"),
        legend=dict(orientation="h", y=-0.35, x=0.5, xanchor="center",
                    font=dict(family="Vazirmatn", size=12)),
        margin=dict(l=50, r=20, t=20, b=120),
        height=420,
        font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(fig_period_cmp, use_container_width=True,
                    config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'compare_period'}})

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # بخش ۳: توزیع لحن
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:4px">'
        f'🎭 توزیع لحن برای هر کلیدواژه</div>'
        f'<div style="direction:rtl;font-size:12px;color:#888;margin-bottom:8px">'
        f'اسنادی که حاوی این کلیدواژه هستند، چه لحنی دارند؟</div>',
        unsafe_allow_html=True,
    )

    tone_cols = st.columns(min(len(cmp_kws), 3))
    for i, kw in enumerate(cmp_kws):
        col_idx = i % len(tone_cols)
        with tone_cols[col_idx]:
            st.markdown(
                f'<div style="direction:rtl;font-weight:700;color:{_COLORS[i % len(_COLORS)]};'
                f'font-size:13px;margin-bottom:6px;text-align:center">«{kw}»</div>',
                unsafe_allow_html=True,
            )
            td = tone_data_all.get(kw, [])
            if td:
                tones  = [t[0] for t in td]
                tcnts  = [t[1] for t in td]
                total_t = sum(tcnts) or 1
                fig_t = go.Figure(go.Bar(
                    x=[round(100.0 * c / total_t, 1) for c in tcnts],
                    y=tones,
                    orientation="h",
                    marker_color=_COLORS[i % len(_COLORS)],
                    hovertemplate="<b>%{y}</b>: %{x:.1f}٪<extra></extra>",
                    text=[f"{round(100.0*c/total_t,1)}٪" for c in tcnts],
                    textposition="outside",
                ))
                fig_t.update_layout(
                    plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
                    xaxis=dict(title="درصد", showgrid=True, gridcolor="#e0e8ee", range=[0, 110]),
                    yaxis=dict(autorange="reversed", tickfont=dict(family="Vazirmatn", size=10)),
                    margin=dict(l=90, r=40, t=10, b=30),
                    height=260, font=dict(family="Vazirmatn"),
                )
                st.plotly_chart(fig_t, use_container_width=True, config=CHART_CONFIG)
            else:
                st.caption("اطلاعات لحن موجود نیست.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # بخش ۴: موضوعات همراه
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:4px">'
        f'🏷️ موضوعات همرخداد</div>'
        f'<div style="direction:rtl;font-size:12px;color:#888;margin-bottom:8px">'
        f'وقتی این کلیدواژه در سند ظاهر می‌شود، بیشتر با کدام موضوعات همراه است؟</div>',
        unsafe_allow_html=True,
    )

    if len(cmp_kws) == 1:
        # تک‌کلیدواژه — نمودار افقی کامل
        kw = cmp_kws[0]
        topics = topics_data_all.get(kw, [])
        if topics:
            tlabels = [t[0] for t in topics]
            tvals   = [t[1] for t in topics]
            fig_top = go.Figure(go.Bar(
                x=tvals, y=tlabels, orientation="h",
                marker_color=_COLORS[0],
                hovertemplate="<b>%{y}</b>: %{x:,} سند<extra></extra>",
                text=tvals, textposition="outside",
            ))
            fig_top.update_layout(
                plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
                xaxis=dict(showgrid=True, gridcolor="#e0e8ee"),
                yaxis=dict(autorange="reversed", tickfont=dict(family="Vazirmatn", size=11)),
                margin=dict(l=160, r=60, t=10, b=30),
                height=360, font=dict(family="Vazirmatn"),
            )
            st.plotly_chart(fig_top, use_container_width=True,
                            config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'topics_compare'}})
        else:
            st.caption("اطلاعات موضوعی موجود نیست.")
    else:
        # چند کلیدواژه — heatmap: موضوع × کلیدواژه
        all_topics_set = []
        for kw in cmp_kws:
            for t, _ in topics_data_all.get(kw, []):
                if t not in all_topics_set:
                    all_topics_set.append(t)
        all_topics_set = all_topics_set[:15]  # حداکثر ۱۵ موضوع

        if all_topics_set:
            z_matrix = []
            for kw in cmp_kws:
                td_dict = {t: c for t, c in topics_data_all.get(kw, [])}
                z_matrix.append([td_dict.get(t, 0) for t in all_topics_set])

            fig_heat = go.Figure(go.Heatmap(
                z=z_matrix,
                x=all_topics_set,
                y=list(cmp_kws),
                colorscale="Blues",
                hovertemplate="کلیدواژه: %{y}<br>موضوع: %{x}<br>تعداد سند: %{z:,}<extra></extra>",
                text=z_matrix,
                texttemplate="%{text}",
            ))
            fig_heat.update_layout(
                plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
                xaxis=dict(tickangle=-40, tickfont=dict(family="Vazirmatn", size=10)),
                yaxis=dict(tickfont=dict(family="Vazirmatn", size=11)),
                margin=dict(l=120, r=40, t=20, b=120),
                height=300,
                font=dict(family="Vazirmatn"),
            )
            st.plotly_chart(fig_heat, use_container_width=True,
                            config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'topics_heatmap'}})
        else:
            st.caption("اطلاعات موضوعی موجود نیست.")

    st.divider()

    # ─ دکمه‌های جستجو برای هر کلیدواژه ──────────────────────────────────
    st.markdown(
        f'<div style="direction:rtl;font-size:13px;font-weight:700;color:{BRAND_DARK};margin-bottom:8px">'
        f'🔍 مشاهده نتایج در جستجو</div>',
        unsafe_allow_html=True,
    )
    search_btns = st.columns(len(cmp_kws))
    for i, kw in enumerate(cmp_kws):
        with search_btns[i]:
            if st.button(f"جستجوی «{kw}»", key=f"cmp_search_{i}",
                         type="primary" if i == 0 else "secondary"):
                go_to_search(kw)


# ════════════════════════════════════════════════════════════════════════════
# Tab 2: ابر کلمات
# ════════════════════════════════════════════════════════════════════════════
with tab_cloud:
    st.markdown(
        f'<div style="direction:rtl;color:{BRAND_DARK};font-size:14px;margin-bottom:8px">'
        f'ابر کلمات بر اساس فراوانی در پیکره — {len(words_list)} کلیدواژه برتر</div>',
        unsafe_allow_html=True,
    )

    rng = random.Random(42)
    min_freq  = min(freqs)
    max_freq  = max(freqs)
    freq_range = max_freq - min_freq if max_freq != min_freq else 1

    font_sizes = [11 + int(33 * (f - min_freq) / freq_range) for f in freqs]

    n      = len(words_list)
    colors = [
        f"rgb({int(3 + (16-3)*i/max(n-1,1))}, "
        f"{int(50 + (145-50)*i/max(n-1,1))}, "
        f"{int(70 + (236-70)*i/max(n-1,1))})"
        for i in range(n)
    ]

    x_pos = [rng.uniform(0.02, 0.98) for _ in words_list]
    y_pos = [rng.uniform(0.05, 0.95) for _ in words_list]

    fig_cloud = go.Figure()
    fig_cloud.add_trace(go.Scatter(
        x=x_pos, y=y_pos,
        mode="text",
        text=words_list,
        textfont=dict(size=font_sizes, color=colors, family="Vazirmatn"),
        hovertemplate=[
            f"<b>{w}</b><br>فراوانی: {freqs[i]:,}<extra></extra>"
            for i, w in enumerate(words_list)
        ],
        customdata=words_list,
    ))
    fig_cloud.update_layout(
        plot_bgcolor="#f4f7fa",
        paper_bgcolor="#f4f7fa",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=550,
        font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(
        fig_cloud, use_container_width=True,
        config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'wordcloud'}},
    )

    # دانلود CSV
    cloud_df = pd.DataFrame({"کلیدواژه": words_list, "فراوانی": freqs})
    st.download_button(
        label="📥 دانلود CSV ابر کلمات",
        data=cloud_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="wordcloud_data.csv",
        mime="text/csv",
    )


# ════════════════════════════════════════════════════════════════════════════
# Tab 3: رتبه‌بندی
# ════════════════════════════════════════════════════════════════════════════
with tab_rank:
    st.markdown(
        f'<div style="direction:rtl;font-size:15px;font-weight:700;color:{BRAND_DARK};'
        f'margin-bottom:12px">📋 فهرست رتبه‌بندی کلیدواژه‌ها</div>',
        unsafe_allow_html=True,
    )

    # جستجو/فیلتر
    filter_text = st.text_input(
        "فیلتر کلیدواژه‌ها:",
        placeholder="جستجو در فهرست...",
        key="rank_filter",
    )

    df_all = pd.DataFrame(keywords_data)
    df_all.insert(0, "رتبه", range(1, len(df_all) + 1))
    df_all = df_all.rename(columns={
        "word":       "کلیدواژه",
        "total_freq": "فراوانی کل",
        "doc_freq":   "اسناد",
        "pct_docs":   "درصد اسناد",
    })

    if filter_text.strip():
        df_show = df_all[df_all["کلیدواژه"].str.contains(filter_text.strip(), na=False)]
    else:
        df_show = df_all

    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # دکمه رفتن به تحلیل
    if not df_show.empty:
        col_kw_sel, col_kw_go = st.columns([3, 1])
        with col_kw_sel:
            selected_from_rank = st.selectbox(
                "انتخاب کلیدواژه برای تحلیل عمیق:",
                options=df_show["کلیدواژه"].tolist(),
                key="rank_select",
            )
        with col_kw_go:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("📊 مقایسه", key="rank_analysis_btn"):
                st.session_state["_cmp_preset"] = [selected_from_rank, "", "", "", ""]
                st.info(f"✅ «{selected_from_rank}» آماده شد — روی تب **«📊 مقایسه‌ی کلیدواژه‌ها»** کلیک کنید.", icon="👆")
            if st.button("🔎 جستجو", key="rank_search_btn"):
                go_to_search(selected_from_rank)

    st.divider()

    # نمودار افقی ۳۰ کلیدواژه برتر
    st.markdown(
        f'<div style="direction:rtl;font-weight:700;color:{BRAND_DARK};margin-bottom:6px">'
        f'نمودار ۳۰ کلیدواژه برتر</div>',
        unsafe_allow_html=True,
    )
    top30 = df_all.head(30)
    fig_bar = go.Figure(go.Bar(
        x=top30["فراوانی کل"].tolist(),
        y=top30["کلیدواژه"].tolist(),
        orientation="h",
        marker_color=BRAND_BLUE,
        hovertemplate="<b>%{y}</b><br>فراوانی: %{x:,}<extra></extra>",
        text=top30["فراوانی کل"].tolist(),
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_bar.update_layout(
        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
        xaxis=dict(title="فراوانی کل", showgrid=True, gridcolor="#e0e8ee"),
        yaxis=dict(autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
        margin=dict(l=120, r=80, t=20, b=40),
        height=650,
        font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(
        fig_bar, use_container_width=True,
        config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'top_keywords'}},
    )

    # دانلود CSV
    st.download_button(
        label="📥 دانلود CSV فهرست کامل",
        data=df_all.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"keywords_ranked_{yr1}_{yr2}.csv",
        mime="text/csv",
    )


# ════════════════════════════════════════════════════════════════════════════
# Tab 4: روند زمانی
# ════════════════════════════════════════════════════════════════════════════
with tab_trend:
    st.markdown(
        f'<div style="direction:rtl;font-size:15px;font-weight:700;color:{BRAND_DARK};'
        f'margin-bottom:12px">📈 مقایسه روند زمانی کلیدواژه‌ها</div>',
        unsafe_allow_html=True,
    )

    default_kws = words_list[:5] if len(words_list) >= 5 else words_list
    selected_kws = st.multiselect(
        "انتخاب کلیدواژه‌ها (حداکثر ۱۰):",
        options=words_list,
        default=default_kws,
        max_selections=10,
    )

    if selected_kws:
        palette = [
            BRAND_BLUE, BRAND_RED, "#0e8a16", "#f99400", "#9c27b0",
            "#00bcd4", "#ff5722", "#607d8b", "#795548", "#e91e63",
        ]

        yearly_totals_trend = get_yearly_total_counts(conn, sel_tiers)
        fig_trend = go.Figure()
        trend_export_data = {}
        for idx, kw in enumerate(selected_kws):
            trend = get_keyword_trend_ranged(conn, kw, date_from, date_to, sel_tiers)
            if not trend:
                continue
            years  = [t[0] for t in trend if yearly_totals_trend.get(t[0], 0) >= 10]
            counts = [t[1] for t in trend if yearly_totals_trend.get(t[0], 0) >= 10]
            color  = palette[idx % len(palette)]
            fig_trend.add_trace(go.Scatter(
                x=years, y=counts,
                mode="lines+markers",
                name=kw,
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color),
                hovertemplate=f"<b>{kw}</b><br>سال: %{{x}}<br>اسناد: %{{y:,}}<extra></extra>",
            ))
            trend_export_data[kw] = dict(zip(years, counts))

        fig_trend.update_layout(
            hovermode="x unified",
            plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
            xaxis=dict(title="سال هجری شمسی", showgrid=True, gridcolor="#e0e8ee"),
            yaxis=dict(title="تعداد اسناد", showgrid=True, gridcolor="#e0e8ee"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(family="Vazirmatn")),
            margin=dict(l=40, r=20, t=60, b=40),
            height=460,
            font=dict(family="Vazirmatn"),
        )
        st.plotly_chart(
            fig_trend, use_container_width=True,
            config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'trend_comparison'}},
        )

        # دانلود CSV روند
        if trend_export_data:
            trend_df = pd.DataFrame(trend_export_data).fillna(0).astype(int)
            trend_df.index.name = "سال"
            st.download_button(
                label="📥 دانلود CSV روند",
                data=trend_df.reset_index().to_csv(index=False).encode("utf-8-sig"),
                file_name="keyword_trend.csv",
                mime="text/csv",
            )
    else:
        st.info("حداقل یک کلیدواژه انتخاب کنید.")


# ════════════════════════════════════════════════════════════════════════════
# Tab 5: مفاهیم مرکب
# ════════════════════════════════════════════════════════════════════════════
with tab_compound:
    total_phrases = len(COMPOUND_CONCEPTS)
    st.markdown(
        f'<div style="direction:rtl;font-size:15px;font-weight:700;color:{BRAND_DARK};'
        f'margin-bottom:4px">🔗 مفاهیم مرکب — {total_phrases} عبارت در {len(COMPOUND_CATEGORIES)} دسته</div>',
        unsafe_allow_html=True,
    )

    # ─ توضیح منبع داده ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="direction:rtl;font-size:12px;color:#6a8a9a;margin-bottom:12px;'
        f'background:#f4f7fa;padding:8px 12px;border-radius:6px;border-right:3px solid {BRAND_BLUE}">'
        f'📌 <b>منبع داده:</b> تعداد <b>اسناد</b> حاوی این عبارت (نه تعداد تکرار) — '
        f'جستجوی متنی مستقیم در full_text با فیلتر فعلی: <b>{_tier_desc}</b><br>'
        f'⚠️ اگر عبارتی صفر نشان می‌دهد، احتمالاً در محتوای این tier وجود ندارد — '
        f'برای دیدن آن «همه محتوا» را انتخاب کنید.</div>',
        unsafe_allow_html=True,
    )

    with st.spinner("در حال محاسبه فراوانی مفاهیم مرکب..."):
        compound_counts = get_compound_counts(conn, tuple(COMPOUND_CONCEPTS), sel_tiers)

    # ─ بخش ۱: نمودار مقایسه دسته‌ها ─────────────────────────────────────────
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:6px">'
        f'📊 مقایسه دسته‌ها — جمع فراوانی هر گروه</div>',
        unsafe_allow_html=True,
    )
    cat_totals = {}
    cat_phrase_count = {}
    for cat_name, cat_info in COMPOUND_CATEGORIES.items():
        total = sum(compound_counts.get(p, 0) for p in cat_info["phrases"])
        cat_totals[cat_name] = total
        cat_phrase_count[cat_name] = len(cat_info["phrases"])

    cat_sorted = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    fig_cats = go.Figure(go.Bar(
        x=[v for _, v in cat_sorted],
        y=[f"{COMPOUND_CATEGORIES[k]['icon']} {k}" for k, _ in cat_sorted],
        orientation="h",
        marker_color=[COMPOUND_CATEGORIES[k]["color"] for k, _ in cat_sorted],
        hovertemplate="<b>%{y}</b><br>جمع اسناد: %{x:,}<extra></extra>",
        text=[f"{v:,}" for _, v in cat_sorted],
        textposition="outside",
    ))
    fig_cats.update_layout(
        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
        xaxis=dict(showgrid=True, gridcolor="#e0e8ee"),
        yaxis=dict(autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
        margin=dict(l=240, r=80, t=10, b=30),
        height=360, font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(fig_cats, use_container_width=True,
                    config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'compound_categories'}})

    # ─ بخش ۲: جدول ۲۰ عبارت برتر ───────────────────────────────────────────
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:6px">'
        f'🏆 ۲۰ عبارت مرکب پرکاربرد</div>',
        unsafe_allow_html=True,
    )
    top20 = sorted(compound_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    # نگاشت عبارت به دسته
    phrase_to_cat = {
        p: cat_name
        for cat_name, cat_info in COMPOUND_CATEGORIES.items()
        for p in cat_info["phrases"]
    }
    top20_df = pd.DataFrame([
        {
            "رتبه": i + 1,
            "عبارت مرکب": p,
            "دسته": phrase_to_cat.get(p, "—"),
            "تعداد اسناد": cnt,
        }
        for i, (p, cnt) in enumerate(top20)
    ])
    st.dataframe(top20_df, use_container_width=True, hide_index=True)

    # دانلود CSV کل
    comp_df = pd.DataFrame([
        {"عبارت مرکب": p, "دسته": phrase_to_cat.get(p, "—"), "تعداد اسناد": cnt}
        for p, cnt in sorted(compound_counts.items(), key=lambda x: x[1], reverse=True)
    ])
    st.download_button(
        label="📥 دانلود CSV همه مفاهیم مرکب",
        data=comp_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="compound_concepts.csv",
        mime="text/csv",
    )

    st.divider()

    # ─ بخش ۳: جزئیات — گروه‌بندی موضوعی ────────────────────────────────────
    st.markdown(
        f'<div style="direction:rtl;font-size:14px;font-weight:700;color:{BRAND_DARK};margin-bottom:10px">'
        f'📂 جزئیات بر اساس دسته‌بندی موضوعی</div>',
        unsafe_allow_html=True,
    )

    for cat_name, cat_info in COMPOUND_CATEGORIES.items():
        cat_icon  = cat_info["icon"]
        cat_color = cat_info["color"]
        cat_phrases = cat_info["phrases"]
        cat_total = cat_totals[cat_name]

        with st.expander(
            f"{cat_icon} **{cat_name}** — جمع: {cat_total:,} سند ({len(cat_phrases)} عبارت)",
            expanded=False,
        ):
            # جدول سریع همه عبارات این دسته
            rows = []
            for p in sorted(cat_phrases, key=lambda x: compound_counts.get(x, 0), reverse=True):
                cnt_p = compound_counts.get(p, 0)
                rows.append({"عبارت": p, "اسناد": cnt_p,
                             "وضعیت": "✅" if cnt_p > 0 else f"⚠️ صفر در {_tier_desc}"})
            cat_table_df = pd.DataFrame(rows)
            st.dataframe(cat_table_df, use_container_width=True, hide_index=True)

            # دکمه مقایسه در تب مقایسه
            top_phrases_cat = [r["عبارت"] for r in rows if r["اسناد"] > 0][:5]
            btn_cc1, btn_cc2 = st.columns(2)
            with btn_cc1:
                if top_phrases_cat and st.button(
                    f"📊 مقایسه روند این دسته",
                    key=f"cat_cmp_{cat_name}",
                    help=f"عبارات: {', '.join(top_phrases_cat)}",
                ):
                    st.session_state["_cmp_preset"] = (top_phrases_cat + [""] * 5)[:5]
                    st.info(f"✅ آماده شد — روی تب «📊 مقایسه‌ی کلیدواژه‌ها» کلیک کنید.", icon="👆")

            # نمودار روند برترین عبارت این دسته
            best_phrase = rows[0]["عبارت"] if rows and rows[0]["اسناد"] > 0 else None
            if best_phrase and st.button(
                f"📈 روند «{best_phrase}»",
                key=f"cat_trend_{cat_name}",
            ):
                st.session_state[f"show_cat_trend_{cat_name}"] = True

            if st.session_state.get(f"show_cat_trend_{cat_name}") and best_phrase:
                trend = get_keyword_trend(conn, best_phrase, sel_tiers)
                yearly_totals = get_yearly_total_counts(conn, sel_tiers)
                if trend:
                    years  = [t[0] for t in trend if t[0] and len(t[0]) == 4 and yearly_totals.get(t[0], 0) >= 10]
                    counts = [t[1] for t in trend if t[0] and len(t[0]) == 4 and yearly_totals.get(t[0], 0) >= 10]
                    pcts   = [round(100.0 * c / yearly_totals[y], 1)
                              if y in yearly_totals and yearly_totals[y] > 0 else 0
                              for y, c in zip(years, counts)]
                    fig_ct = go.Figure()
                    fig_ct.add_trace(go.Bar(
                        x=years, y=pcts,
                        marker_color=cat_color,
                        hovertemplate="سال: %{x}<br>درصد اسناد: %{y:.1f}٪<extra></extra>",
                    ))
                    fig_ct.update_layout(
                        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
                        xaxis=dict(title="سال", showgrid=True, gridcolor="#e0e8ee"),
                        yaxis=dict(title="درصد اسناد (%)", showgrid=True, gridcolor="#e0e8ee"),
                        margin=dict(l=40, r=10, t=10, b=30),
                        height=220,
                        font=dict(family="Vazirmatn", size=11),
                    )
                    st.plotly_chart(fig_ct, use_container_width=True, config=CHART_CONFIG)
                    st.caption("درصد نرمال‌شده: از هر ۱۰۰ سند آن سال، چند تا این عبارت را دارند")
                else:
                    st.info("داده روند یافت نشد.")


# ════════════════════════════════════════════════════════════════════════════
# Tab 6: مضامین اصلی
# ════════════════════════════════════════════════════════════════════════════
with tab_themes:
    st.markdown(
        f'<div style="direction:rtl;font-size:15px;font-weight:700;color:{BRAND_DARK};'
        f'margin-bottom:6px">🎯 مضامین اصلی — {len(THEMES)} مضمون</div>',
        unsafe_allow_html=True,
    )

    # ─ راهنمای تحقیقاتی ────────────────────────────────────────────────────
    with st.expander("📌 راهنمای تحقیق: هویت ایرانی در گفتار خامنه‌ای — از کدام ایران سخن می‌گوید؟", expanded=True):
        st.markdown("""
<div style="direction:rtl;line-height:2;font-size:13px">

این گروه از مضامین برای پاسخ به سؤال زیر طراحی شده است:

> **خامنه‌ای از چه «ایرانی» سخن می‌گوید؟ چه بخش‌هایی از تاریخ و فرهنگ ایران را می‌پذیرد و چه بخش‌هایی را رد می‌کند؟**

#### ۷ مضمون گروه «هویت ایرانی»

| مضمون | سؤال تحقیقاتی |
|-------|--------------|
| 🇮🇷 ایران — هویت ملی و میهن‌دوستی | آیا خامنه‌ای گفتمان ملی-شهروندی دارد؟ |
| 🏛️ ایران باستان و تمدن پیش از اسلام | از کوروش، هخامنشی، ساسانی یاد می‌کند؟ با چه لحنی؟ |
| 📜 ادبیات و میراث فرهنگی کلاسیک | فردوسی، حافظ، سعدی، ابن‌سینا — کدام‌ها را تأیید می‌کند؟ |
| ⚜️ تاریخ سیاسی — صفوی تا پهلوی | مشروطه، مصدق، پهلوی — روایتش چیست؟ |
| 🎨 هنر و فرهنگ معاصر (خارج از نظام) | شاملو، فروغ، روشنفکران — از آن‌ها یاد می‌کند؟ |
| 🎭 هنر و فرهنگ مورد تأیید نظام | چه هنری را می‌پذیرد و ترویج می‌دهد؟ |
| 🔷 ایران اسلامی — پیوند ایران و تشیع | آیا ایران و اسلام را یکی می‌داند؟ |

#### روش پیشنهادی تحلیل

**مقایسه سریع (تب مقایسه):**
- `کوروش` vs `اسلام` vs `ایران` — کدام بیشتر تکرار می‌شود؟
- `فردوسی` vs `امام` vs `شهید` — ارجاعات ادبی در برابر ارجاعات دینی
- `مشروطه` vs `انقلاب` — کدام انقلاب «اصیل» است؟
- `روشنفکر` vs `هنرمند` — لحن گفتار درباره روشنفکری

**روند زمانی:**
دکمه «📈 روند کل مضمون» را بزنید — در کدام دوره (احمدی‌نژاد، خاتمی، ...) هر مضمون بیشتر بوده است؟

**نکته تفسیری:**
اگر امتیاز مضمون «ایران باستان» یا «هنر و فرهنگ معاصر (خارج از نظام)» **بسیار پایین** باشد،
این خود یک **یافته معنادار** است — یعنی خامنه‌ای این بخش‌ها را در گفتمانش حذف کرده.

</div>
""", unsafe_allow_html=True)

    # آماده‌سازی داده برای cache
    themes_input = tuple(
        (name, tuple(info["words"]))
        for name, info in THEMES.items()
    )
    with st.spinner("در حال محاسبه امتیاز مضامین..."):
        theme_scores = get_theme_scores(conn, themes_input)

    sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
    th_labels = [f"{THEMES[t[0]]['icon']} {t[0]}" for t in sorted_themes]
    th_values = [t[1] for t in sorted_themes]
    th_colors = [THEMES[t[0]]["color"] for t in sorted_themes]

    fig_themes = go.Figure(go.Bar(
        x=th_values,
        y=th_labels,
        orientation="h",
        marker_color=th_colors,
        hovertemplate="<b>%{y}</b><br>جمع فراوانی: %{x:,}<extra></extra>",
        text=th_values,
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_themes.update_layout(
        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
        xaxis=dict(title="جمع فراوانی واژگان", showgrid=True, gridcolor="#e0e8ee"),
        yaxis=dict(autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
        margin=dict(l=230, r=80, t=20, b=40),
        height=max(420, len(th_labels) * 28 + 60),
        font=dict(family="Vazirmatn"),
    )
    st.plotly_chart(
        fig_themes, use_container_width=True,
        config={**CHART_CONFIG, 'toImageButtonOptions': {**CHART_CONFIG['toImageButtonOptions'], 'filename': 'themes'}},
    )

    # دانلود CSV مضامین
    themes_df = pd.DataFrame(
        [(t[0], THEMES[t[0]]["icon"], t[1], ", ".join(THEMES[t[0]]["words"]))
         for t in sorted_themes],
        columns=["مضمون", "آیکون", "جمع فراوانی", "کلیدواژه‌ها"],
    )
    st.download_button(
        label="📥 دانلود CSV مضامین",
        data=themes_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="themes_scores.csv",
        mime="text/csv",
    )

    st.divider()

    # اکسپندر برای هر مضمون
    st.markdown(
        f'<div style="direction:rtl;font-weight:700;color:{BRAND_DARK};margin-bottom:10px">'
        f'جزئیات هر مضمون:</div>',
        unsafe_allow_html=True,
    )

    for theme_name, score in sorted_themes:
        theme_info = THEMES[theme_name]
        icon  = theme_info["icon"]
        color = theme_info["color"]
        words = theme_info["words"]
        note  = theme_info.get("note", "")

        with st.expander(f"{icon} {theme_name}  —  جمع فراوانی: {score:,}"):
            if note:
                st.markdown(
                    f'<div style="direction:rtl;font-size:12px;color:#5a7a8a;'
                    f'background:#f0f7ff;border-right:3px solid {color};'
                    f'padding:6px 10px;border-radius:4px;margin-bottom:10px">'
                    f'💡 {note}</div>',
                    unsafe_allow_html=True,
                )
            # جدول فراوانی کلمات مضمون
            placeholders = ",".join("?" * len(words))
            word_rows = conn.execute(
                f"SELECT word, total_freq, doc_freq FROM word_freq "
                f"WHERE word IN ({placeholders}) ORDER BY total_freq DESC",
                words,
            ).fetchall()

            if word_rows:
                wd_df = pd.DataFrame(word_rows, columns=["کلیدواژه", "فراوانی کل", "اسناد"])
                st.dataframe(wd_df, use_container_width=True, hide_index=True)
            else:
                st.caption("داده‌ای در جدول word_freq یافت نشد.")

            # دکمه‌های عمل
            primary_word = words[0] if words else theme_name
            # مقایسه تا ۵ کلمه اول این مضمون در تب مقایسه
            compare_words = words[:5]

            btn_c1, btn_c2, btn_c3 = st.columns(3)
            with btn_c1:
                if st.button(
                    f"🔎 جستجوی «{primary_word}»",
                    key=f"theme_search_{theme_name}",
                ):
                    go_to_search(primary_word)
            with btn_c2:
                if st.button(
                    f"📊 مقایسه کلیدواژه‌های این مضمون",
                    key=f"theme_compare_{theme_name}",
                    help=f"کلیدواژه‌های این مضمون را در تب مقایسه باز می‌کند: {', '.join(compare_words)}",
                ):
                    preset = list(compare_words) + [""] * (5 - len(compare_words))
                    st.session_state["_cmp_preset"] = preset[:5]
                    # بدون rerun — کلیک روی تب مقایسه rerun را راه می‌اندازد
                    st.info(
                        f"✅ کلیدواژه‌های **{theme_name}** آماده شدند: "
                        f"**{' | '.join(compare_words)}**  \n"
                        f"→ حالا روی تب **«📊 مقایسه‌ی کلیدواژه‌ها»** در بالا کلیک کنید.",
                        icon="👆",
                    )
            with btn_c3:
                # نمایش نمودار روند همه کلمات مضمون در همین اکسپندر
                if st.button(
                    f"📈 روند کل مضمون",
                    key=f"theme_trend_{theme_name}",
                    help="نمودار روند زمانی این مضمون (جمع همه کلمات) را نشان می‌دهد",
                ):
                    st.session_state[f"show_trend_{theme_name}"] = True

            if st.session_state.get(f"show_trend_{theme_name}"):
                # روند سالانه برای کل کلمات مضمون
                # مهم: tier_sql باید با مخرج (yearly_totals_th) یکی باشد وگرنه درصد > 100 می‌شود
                _t_sql, _t_params = _tier_clause_simple(sel_tiers)
                trend_rows = conn.execute(
                    """
                    SELECT substr(date_persian,1,4) AS y, COUNT(*) AS cnt
                    FROM documents
                    WHERE ({conds})
                      AND date_persian GLOB '1[3-4][0-9][0-9]*'
                    {tier_filter}
                    GROUP BY y ORDER BY y
                    """.format(
                        conds=" OR ".join(
                            ["full_text LIKE ?" for _ in words]
                        ),
                        tier_filter=_t_sql,
                    ),
                    [f"%{w}%" for w in words] + _t_params,
                ).fetchall()
                if trend_rows:
                    yearly_totals_th = get_yearly_total_counts(conn, sel_tiers)
                    ys = [r[0] for r in trend_rows if r[0] and len(r[0]) == 4 and yearly_totals_th.get(r[0], 0) >= 10]
                    cs = [r[1] for r in trend_rows if r[0] and len(r[0]) == 4 and yearly_totals_th.get(r[0], 0) >= 10]
                    pcts_th = [
                        round(100.0 * c / yearly_totals_th[y], 2)
                        if y in yearly_totals_th and yearly_totals_th[y] > 0 else 0
                        for y, c in zip(ys, cs)
                    ]
                    fig_th_trend = go.Figure(go.Scatter(
                        x=ys, y=pcts_th,
                        mode="lines+markers",
                        fill="tozeroy",
                        fillcolor=_hex_rgba(color, 0.13),
                        line=dict(color=color, width=2.5),
                        marker=dict(size=6, color=color),
                        hovertemplate="سال: %{x}<br>درصد اسناد: %{y:.2f}٪<extra></extra>",
                    ))
                    fig_th_trend.update_layout(
                        plot_bgcolor="#f4f7fa", paper_bgcolor="#ffffff",
                        xaxis=dict(title="سال هجری شمسی", showgrid=True, gridcolor="#e0e8ee"),
                        yaxis=dict(title="درصد اسناد آن سال (%)", showgrid=True, gridcolor="#e0e8ee"),
                        margin=dict(l=50, r=20, t=10, b=40),
                        height=280, font=dict(family="Vazirmatn"),
                    )
                    st.plotly_chart(fig_th_trend, use_container_width=True, config=CHART_CONFIG)
                    st.caption("ℹ️ نرمال‌شده: درصد اسناد هر سال که حداقل یکی از کلمات این مضمون را دارند.")
                else:
                    st.caption("داده‌ای یافت نشد.")

# ─── فوتر ───────────────────────────────────────────────────────────────────
render_footer()
