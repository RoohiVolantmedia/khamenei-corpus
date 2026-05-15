"""مدیریت ورکست‌های ذخیره‌شده"""
import json
from pathlib import Path
from datetime import datetime

WORKSETS_FILE = Path.home() / "Desktop/khamenei_corpus/worksets.json"

def _load() -> dict:
    if WORKSETS_FILE.exists():
        try:
            return json.loads(WORKSETS_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def _save(data: dict):
    WORKSETS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def list_worksets() -> list[dict]:
    """لیست همه ورکست‌ها به ترتیب زمان ذخیره"""
    data = _load()
    return sorted(data.values(), key=lambda x: x.get('saved_at',''), reverse=True)

def save_workset(name: str, filters: dict) -> bool:
    """ذخیره ورکست جدید"""
    if not name.strip():
        return False
    data = _load()
    data[name] = {
        'name': name,
        'filters': filters,
        'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    _save(data)
    return True

def delete_workset(name: str) -> bool:
    data = _load()
    if name in data:
        del data[name]
        _save(data)
        return True
    return False

def get_workset(name: str) -> dict | None:
    data = _load()
    return data.get(name)
