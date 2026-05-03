"""
集成测试 — 模拟用户真实操作流程
模拟：复制文本 → 数据库插入 → 查询验证 → 固定/删除
"""
import time
import pytest
from database import init_db, add_clip, get_clips, get_count, toggle_pin, delete_clip, clear_all


class TestUserWorkflow:
    """模拟真实用户操作流程"""

    def test_cold_start_to_first_clip(self, temp_db):
        """场景：用户首次启动 → 复制第一段文本 → 在历史中看到它"""
        # Step 1: 冷启动
        assert get_count() == 0

        # Step 2: 用户复制文本
        add_clip("你好，ClipVault！")
        assert get_count() == 1

        # Step 3: 用户在历史列表里看到它
        clips = get_clips()
        assert len(clips) == 1
        assert clips[0][1] == "你好，ClipVault！"

    def test_copy_multiple_items(self, temp_db):
        """场景：用户连续复制多段文本 → 全部出现在历史中，按时间倒序"""
        texts = ["第一段", "第二段", "第三段", "第四段", "第五段"]
        for t in texts:
            add_clip(t)
            time.sleep(0.01)

        clips = get_clips()
        assert len(clips) == 5
        # 最新的在最前面
        assert clips[0][1] == "第五段"
        assert clips[4][1] == "第一段"

    def test_copy_same_text_twice(self, temp_db):
        """场景：用户不小心复制了同样的内容两次 → 不应该重复出现"""
        add_clip("重要链接：https://example.com")
        add_clip("重要链接：https://example.com")  # 又复制了一次

        assert get_count() == 1  # 去重

    def test_search_workflow(self, temp_db):
        """场景：用户复制了很多文本 → 用搜索功能找到目标"""
        add_clip("电商项目需求文档 v3")
        add_clip("周末团建报名表")
        add_clip("Python 自动化脚本 - 数据采集")
        add_clip("电商平台竞品分析")
        add_clip("团建活动方案")

        # 用户搜索"电商"
        results = get_clips(search="电商")
        assert len(results) == 2  # 两条和电商相关

        # 用户搜索"团建"
        results = get_clips(search="团建")
        assert len(results) == 2

    def test_pin_important_item(self, temp_db):
        """场景：用户把重要内容固定到顶部"""
        add_clip("临时笔记1")
        add_clip("今天必须完成的 TODO 清单")
        add_clip("临时笔记2")

        clips = get_clips()
        # 固定中间的"TODO 清单"
        todo_id = clips[1][0]
        toggle_pin(todo_id)

        clips_after = get_clips()
        assert clips_after[0][1] == "今天必须完成的 TODO 清单"
        assert clips_after[0][4] == 1  # 已固定

    def test_delete_and_cleanup(self, temp_db):
        """场景：用户删除不需要的内容，清空非固定项"""
        add_clip("废文本1")
        add_clip("重要密码：123456")
        add_clip("废文本2")

        clips = get_clips()
        toggle_pin(clips[1][0])  # 固定密码
        delete_clip(clips[2][0])  # 删除废文本2

        assert get_count() == 2  # 剩两条

        clear_all()  # 清空非固定
        remaining = get_clips()
        assert len(remaining) == 1  # 只剩密码
        assert "密码" in remaining[0][1]

    def test_free_tier_limit(self, temp_db):
        """场景：免费版用户超过 50 条限制 → 最旧的被自动删除"""
        for i in range(55):
            add_clip(f"历史记录 {i}")
            time.sleep(0.001)

        assert get_count() <= 50, f"免费版不应超过 50 条，实际 {get_count()}"


class TestAutoRefreshScenario:
    """验证 UI 自动刷新依赖的底层逻辑"""

    def test_monitor_callback_wiring(self, temp_db):
        """
        验证 ClipboardMonitor.on_new_clip 回调机制：
        当监控器检测到新内容 → add_clip 返回 True → 应该触发回调
        这个测试确保回调链条在数据库层面是正确的。
        """
        # 新内容应该触发 add_clip 返回 True
        result = add_clip("新剪贴板内容")
        assert result is True, "新内容应返回 True（触发回调）"

        # 重复内容返回 None（不触发回调）
        result2 = add_clip("新剪贴板内容")
        assert result2 is None, "重复内容应返回 None（不触发回调）"

    def test_refresh_returns_fresh_data(self, temp_db):
        """
        模拟 GUI refresh_list 的调用逻辑：
        添加新 clip → refresh → 列表应该包含新 clip
        """
        add_clip("刷新前的内容")

        # 第一次"刷新"（模拟 GUI 加载）
        before = get_clips()
        assert len(before) == 1

        # 新内容到达
        add_clip("刷新后的新内容")

        # 第二次"刷新"（模拟 GUI refresh_list）
        after = get_clips()
        assert len(after) == 2
        assert after[0][1] == "刷新后的新内容"  # 最新的在前
