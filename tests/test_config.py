"""
配置层测试 — 读写、默认值、持久化
"""
import json
import os
from config import DEFAULT_SETTINGS, load_settings, save_settings


class TestConfigDefaults:
    def test_default_values(self, temp_config):
        """无配置文件时应该返回默认值"""
        settings = temp_config["load"]()
        assert settings["max_items"] == 50
        assert settings["theme"] == "dark"
        assert settings["language"] == "zh"
        assert settings["auto_start"] is True
        assert settings["is_pro"] is False

    def test_load_nonexistent_file(self, temp_config):
        """配置文件不存在时不应报错"""
        assert not os.path.exists(temp_config["path"])
        settings = temp_config["load"]()
        assert settings == temp_config["defaults"]


class TestConfigSave:
    def test_save_and_reload(self, temp_config):
        """保存后重新加载应该一致"""
        new_settings = {"max_items": 100, "theme": "light", "language": "en"}
        temp_config["save"](new_settings)
        loaded = temp_config["load"]()
        assert loaded["max_items"] == 100
        assert loaded["theme"] == "light"
        assert loaded["language"] == "en"

    def test_save_creates_file(self, temp_config):
        """保存应该创建配置文件"""
        temp_config["save"]({"max_items": 200})
        assert os.path.exists(temp_config["path"])

    def test_partial_save_keeps_defaults(self, temp_config):
        """部分保存时缺失项应保留默认值"""
        temp_config["save"]({"max_items": 75})
        loaded = temp_config["load"]()
        assert loaded["max_items"] == 75
        assert loaded["theme"] == DEFAULT_SETTINGS["theme"]
        assert loaded["language"] == DEFAULT_SETTINGS["language"]
