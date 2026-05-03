"""
端到端用户模拟测试 — 模拟真实剪贴板操作
独立运行: python tests/test_clipboard_integration.py
"""
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyperclip

# 使用临时数据库，绝不污染真实数据
_temp_dir = tempfile.mkdtemp(prefix="clipvault_test_")
_test_db = os.path.join(_temp_dir, "test_integration.db")
os.environ["CLIPVAULT_TEST_DB"] = _test_db

import database
database.DB_PATH = _test_db

from database import init_db, add_clip, get_clips, get_count, toggle_pin, delete_clip, clear_all


def cleanup():
    """清理测试数据库"""
    try:
        os.remove(_test_db)
        os.rmdir(_temp_dir)
    except Exception:
        pass


def test_full_user_session():
    """
    模拟完整用户会话：冷启动 → 复制 → 搜索 → 固定 → 去重 → 删除 → 清空
    """
    print("=" * 60)
    print("ClipVault 用户会话模拟测试")
    print(f"测试数据库: {_test_db}")
    print("=" * 60)
    passed = 0
    failed = 0

    # 确保干净启动
    cleanup()
    init_db()

    # 1. 冷启动
    print("\n[TEST 1] 冷启动 — 数据库应该为空")
    try:
        assert get_count() == 0, f"预期 0 条，实际 {get_count()}"
        print("  PASS: 冷启动成功，数据库为空")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 2. 模拟用户复制 5 段文本
    print("\n[TEST 2] 模拟用户复制 5 段文本")
    test_texts = [
        "会议纪要：2026年Q2产品规划",
        "https://github.com/3612hdu/ClipVault",
        "TODO: 修复登录页 CSS 对齐问题",
        "外卖优惠券码：SAVE50",
        "周末记得给爸妈打电话",
    ]
    try:
        for i, text in enumerate(test_texts):
            pyperclip.copy(text)
            content = pyperclip.paste()
            assert content == text, f"剪贴板读写不一致: {content} != {text}"
            add_clip(content)
            print(f"  [{i+1}] 复制并存储: {text[:40]}...")
            time.sleep(0.3)

        assert get_count() == 5, f"应该有 5 条，实际 {get_count()}"
        print("  PASS: 5 段文本全部存入数据库")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 3. 验证历史列表顺序（新→旧）
    print("\n[TEST 3] 验证历史列表顺序")
    try:
        clips = get_clips()
        assert clips[0][1] == test_texts[-1], f"最新应在前，期望'{test_texts[-1][:20]}' 实际'{clips[0][1][:20]}'"
        assert clips[-1][1] == test_texts[0], f"最早应在后，期望'{test_texts[0][:20]}' 实际'{clips[-1][1][:20]}'"
        print("  PASS: 顺序正确（新→旧）")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 4. 搜索测试
    print("\n[TEST 4] 搜索功能")
    try:
        results = get_clips(search="会议")
        assert len(results) == 1
        assert "会议纪要" in results[0][1]
        print("  PASS: 搜索'会议'返回 1 条正确结果")

        results = get_clips(search="不存在关键词xyz")
        assert len(results) == 0
        print("  PASS: 搜索无匹配词返回空")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 5. 固定测试
    print("\n[TEST 5] 固定功能")
    try:
        clips = get_clips()
        todo_id = None
        for c in clips:
            if "TODO" in c[1]:
                todo_id = c[0]
                break
        assert todo_id is not None
        toggle_pin(todo_id)

        clips_after = get_clips()
        assert clips_after[0][4] == 1, "固定项应排最前"
        assert clips_after[0][0] == todo_id
        print("  PASS: TODO 项固定成功，排在最前")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 6. 连续重复去重
    print("\n[TEST 6] 去重验证（连续重复）")
    try:
        count_before = get_count()
        pyperclip.copy("测试去重专用文本")
        add_clip("测试去重专用文本")
        assert get_count() == count_before + 1
        # 模拟连续复制同一内容
        result = add_clip("测试去重专用文本")
        assert result is None, "连续重复应返回 None"
        assert get_count() == count_before + 1, "计数不应增加"
        print("  PASS: 连续重复被正确过滤")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 7. 删除
    print("\n[TEST 7] 删除功能")
    try:
        count_before = get_count()
        clips = get_clips()
        delete_clip(clips[-1][0])
        assert get_count() == count_before - 1
        print("  PASS: 删除成功")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 8. 清空（保留固定项）
    print("\n[TEST 8] 清空（保留固定项）")
    try:
        clear_all()
        remaining = get_clips()
        assert len(remaining) == 1, f"清空后应剩 1 条固定项，实际 {len(remaining)}"
        assert remaining[0][4] == 1
        print("  PASS: 清空成功，固定项被保留")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failed += 1

    # 总结
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败, {passed + failed} 总计")
    print("=" * 60)

    cleanup()
    return failed == 0


if __name__ == "__main__":
    success = test_full_user_session()
    sys.exit(0 if success else 1)
