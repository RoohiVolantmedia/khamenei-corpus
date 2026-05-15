_DB_CACHE: Optional[Path] = None

# آدرس دیتابیس روی GitHub Releases
_DEFAULT_DB_URL = (
    "https://github.com/RoohiVolantmedia/khamenei-corpus"
    "/releases/download/V1.0/database_deploy.db"
)

def _get_db_path() -> Path:
    global _DB_CACHE
    if _DB_CACHE is not None:
        return _DB_CACHE

    # اجرای محلی: دیتابیس کنار پوشه‌ی app
    local = Path(__file__).resolve().parent.parent.parent / "database.db"
    if local.exists():
        _DB_CACHE = local
        return _DB_CACHE

    # production: بررسی cache در /tmp
    tmp = Path("/tmp/khamenei_db.db")
    if tmp.exists():
        _DB_CACHE = tmp
        return _DB_CACHE

    # دانلود — از secret یا URL پیش‌فرض
    url = os.environ.get("DB_URL", "") or _DEFAULT_DB_URL

    import requests
    with requests.get(url, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        with open(str(tmp), "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    _DB_CACHE = tmp
    return _DB_CACHE
