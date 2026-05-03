"""应力测试用数据库隔离 — 无 pytest 依赖"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_original_db_path = None
_patched_path = None


def patch(db_path):
    global _original_db_path, _patched_path
    import database
    _original_db_path = database.DB_PATH
    _patched_path = db_path
    database.DB_PATH = db_path


def cleanup():
    global _original_db_path, _patched_path
    import database
    if _original_db_path:
        database.DB_PATH = _original_db_path
    if _patched_path and os.path.exists(_patched_path):
        try:
            os.remove(_patched_path)
        except OSError:
            pass
    _original_db_path = None
    _patched_path = None
