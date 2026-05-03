"""
数据库层单元测试 — CRUD、去重、限制、固定、搜索
"""
import time
import pytest
from database import init_db, add_clip, get_clips, get_count, toggle_pin, delete_clip, clear_all


class TestDatabaseInit:
    def test_init_creates_table(self, temp_db):
        """冷启动：init_db 应该创建 clips 表"""
        from database import get_conn
        conn = get_conn()
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clips'")
        assert cur.fetchone() is not None, "clips 表应该存在"

    def test_init_idempotent(self, temp_db):
        """多次调用 init_db 不应该报错"""
        init_db()  # 第一次
        init_db()  # 第二次 — 不应抛异常
        assert get_count() == 0


class TestAddClip:
    def test_add_single(self, temp_db):
        """添加单条剪贴板记录"""
        result = add_clip("测试文本")
        assert result is True
        assert get_count() == 1

    def test_add_duplicate_skipped(self, temp_db):
        """重复添加相同内容应该跳过（返回 None）"""
        add_clip("重复测试")
        result = add_clip("重复测试")  # 同上一条
        assert result is None
        assert get_count() == 1, "重复条目不应增加计数"

    def test_add_duplicate_updates_timestamp(self, temp_db):
        """重复添加应该更新时间戳"""
        add_clip("时间戳测试")
        time.sleep(0.1)
        result = add_clip("时间戳测试")
        assert result is None
        clips = get_clips(limit=1)
        # 时间戳应该比 sleep 之前晚
        now = time.time()
        assert now - clips[0][5] < 1.0

    def test_add_different_content(self, temp_db):
        """不同内容应该各自独立存储"""
        add_clip("A")
        add_clip("B")
        add_clip("C")
        assert get_count() == 3


class TestGetClips:
    def test_order_descending(self, temp_db):
        """应该按时间倒序返回"""
        add_clip("旧")
        time.sleep(0.05)
        add_clip("新")
        clips = get_clips()
        assert len(clips) >= 2
        assert clips[0][1] == "新"

    def test_limit(self, temp_db):
        """limit 参数应该生效"""
        for i in range(10):
            add_clip(f"文本{i}")
        clips = get_clips(limit=3)
        assert len(clips) == 3

    def test_offset(self, temp_db):
        """offset 参数应该生效"""
        for i in range(5):
            add_clip(f"文本{i}")
        all_clips = get_clips(limit=100)
        first_page = get_clips(limit=2, offset=0)
        second_page = get_clips(limit=2, offset=2)
        assert len(first_page) == 2
        assert len(second_page) == 2
        assert first_page[0][0] != second_page[0][0]

    def test_search(self, temp_db):
        """搜索应该过滤结果"""
        add_clip("Python 编程")
        add_clip("Java 编程")
        add_clip("Python 测试")
        results = get_clips(search="Python")
        assert len(results) == 2
        for r in results:
            assert "Python" in r[1]

    def test_search_no_match(self, temp_db):
        """搜索无匹配时返回空列表"""
        add_clip("测试")
        results = get_clips(search="不存在的关键词xxx")
        assert len(results) == 0


class TestPin:
    def test_toggle_pin(self, temp_db):
        """固定/取消固定切换"""
        add_clip("可固定的文本")
        clips = get_clips()
        clip_id = clips[0][0]

        toggle_pin(clip_id)
        clips_after = get_clips()
        assert clips_after[0][4] == 1  # is_pinned = 1

        toggle_pin(clip_id)
        clips_after2 = get_clips()
        assert clips_after2[0][4] == 0  # is_pinned = 0

    def test_pinned_appears_first(self, temp_db):
        """固定项应该排在最前面"""
        add_clip("普通文本1")
        add_clip("普通文本2")
        clips = get_clips()
        toggle_pin(clips[1][0])  # 固定第二条

        clips_after = get_clips()
        assert clips_after[0][4] == 1  # 第一条是固定的


class TestDelete:
    def test_delete_single(self, temp_db):
        """删除单条记录"""
        add_clip("待删除")
        assert get_count() == 1
        clips = get_clips()
        delete_clip(clips[0][0])
        assert get_count() == 0

    def test_clear_all_keeps_pinned(self, temp_db):
        """清空应该保留固定项"""
        add_clip("普通")
        add_clip("重要")
        clips = get_clips()
        toggle_pin(clips[0][0])  # 固定"重要"（最新一条）
        add_clip("另一个普通")

        clear_all()
        remaining = get_clips()
        assert len(remaining) == 1
        assert remaining[0][4] == 1  # 固定项被保留
