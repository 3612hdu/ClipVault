"""
Shared fixtures for ClipVault test suite.
"""
import sys
import os
import pytest

# Add clipvault to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """提供临时数据库路径，隔离测试环境"""
    db_path = tmp_path / "test_clipboard.db"
    monkeypatch.setattr("database.DB_PATH", str(db_path))
    from database import init_db, get_conn

    init_db()
    yield str(db_path)
    # 清理
    try:
        os.remove(str(db_path))
    except Exception:
        pass


@pytest.fixture
def clean_database(temp_db):
    """已初始化的空数据库"""
    from database import add_clip, get_clips, get_count

    return {"add_clip": add_clip, "get_clips": get_clips, "get_count": get_count}


@pytest.fixture
def sample_clips(clean_database):
    """预填充一些测试数据"""
    add = clean_database["add_clip"]
    add("第一段测试文本")
    add("Hello World")
    add("Python 剪贴板管理器")
    add("https://github.com/3612hdu/ClipVault")
    add("第二段测试文本，用于验证搜索功能")
    return clean_database


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """隔离配置文件"""
    config_path = tmp_path / "test_settings.json"
    monkeypatch.setattr("config.CONFIG_PATH", str(config_path))
    from config import DEFAULT_SETTINGS, save_settings, load_settings

    return {
        "path": str(config_path),
        "save": save_settings,
        "load": load_settings,
        "defaults": dict(DEFAULT_SETTINGS),
    }
