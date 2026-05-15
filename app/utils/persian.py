"""نرمال‌سازی و ریشه‌یابی فارسی"""
import re
import unicodedata

_DIACRITICS = re.compile(r'[ً-ٰٟٱ]')
_ZWNJ = '‌'

def normalize(text: str) -> str:
    if not text:
        return text
    text = _DIACRITICS.sub('', text)
    text = text.replace('ی', 'ی')   # ی عربی → ی فارسی (U+06CC)
    text = text.replace('ي', 'ی')   # ي عربی → ی فارسی
    text = text.replace('ك', 'ک')   # ك عربی → ک فارسی
    text = text.replace('ة', 'ه')   # ة → ه
    text = text.replace('هٰ', 'ه')  # هٰ → ه
    text = text.replace('ـ', '')          # ـ (tatweel) حذف
    text = text.replace(_ZWNJ, ' ')           # نیم‌فاصله → فاصله
    text = re.sub(r' +', ' ', text)
    return text.strip()


def expand_stem(word: str) -> list[str]:
    """پسوندهای رایج فارسی برای جستجوی stem-based"""
    word = normalize(word)
    variants = {word}
    suffixes = ['ان', 'ها', 'ات', 'ی', 'های', 'هایی', 'هایم', 'هایت',
                'هایش', 'های', 'ام', 'ات', 'اش', 'یم', 'ید', 'ند',
                'م', 'ت', 'ش', 'تر', 'ترین']
    for s in suffixes:
        if word.endswith(s) and len(word) > len(s) + 2:
            variants.add(word[:-len(s)])
        else:
            variants.add(word + s)
    return list(variants)


def highlight(text: str, keywords: list[str], context: int = 150) -> str:
    """snippet با هایلایت کلیدواژه (HTML)"""
    if not text or not keywords:
        return text[:context * 2] if text else ''
    norm_text = normalize(text)
    best_pos = len(text)
    for kw in keywords:
        pos = norm_text.lower().find(normalize(kw).lower())
        if 0 <= pos < best_pos:
            best_pos = pos
    start = max(0, best_pos - context)
    end = min(len(text), best_pos + context)
    snippet = ('…' if start > 0 else '') + text[start:end] + ('…' if end < len(text) else '')
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        snippet = pattern.sub(f'<mark>{kw}</mark>', snippet)
    return snippet


STOPWORDS_FA = {
    'که', 'در', 'به', 'از', 'این', 'با', 'را', 'است', 'و', 'یا',
    'هم', 'نیز', 'برای', 'تا', 'اما', 'ولی', 'اگر', 'چون', 'پس',
    'بر', 'آن', 'ما', 'شما', 'آنها', 'او', 'من', 'خود', 'هر',
    'همه', 'بود', 'شد', 'می', 'باید', 'باشد', 'کرد', 'دارد',
    'بین', 'پیش', 'بعد', 'زیر', 'روی', 'نه', 'نی', 'یک', 'دو',
    'هیچ', 'چه', 'چی', 'چند', 'کدام', 'کجا', 'کی', 'چطور',
}
