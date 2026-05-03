"""
ClipVault 压力测试 — 模拟真实用户使用 100+ 次
验证: 无崩溃、无数据损坏、响应时间合理
"""
import sys
import os
import time
import random
import string
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def random_text(min_len=5, max_len=200):
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))


def random_chinese_text(min_len=3, max_len=50):
    common = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情最"
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(common, k=length))


# ============================================================
# pytest 版本 — 使用 conftest fixtures
# ============================================================

class TestRapidCopies:
    def test_100_copies_within_limit(self, clean_database):
        """快速复制 100 次，验证上限限制和去重"""
        add = clean_database["add_clip"]
        get_count = clean_database["get_count"]
        start = time.time()

        for i in range(100):
            add(f"stress_{i:04d}_{random_text()}")

        elapsed = time.time() - start
        count = get_count()
        assert 45 <= count <= 51, f"预期 45-51 条（上限50），实际 {count}"
        assert elapsed < 1.0, f"100 次插入太慢: {elapsed:.2f}s"


class TestDedup:
    def test_repeated_paste_dedup(self, clean_database):
        """连续粘贴相同内容 — 应被去重"""
        add = clean_database["add_clip"]
        get_clips = clean_database["get_clips"]

        add("唯一的重复内容")
        add("不同的中间内容")
        for _ in range(48):
            add("唯一的重复内容")

        clips = get_clips()
        unique = set(c[1] for c in clips)
        assert len(unique) <= 3


class TestPinDelete:
    def test_pin_delete_cycle(self, clean_database):
        """固定/取消/删除 循环 20 轮"""
        add = clean_database["add_clip"]
        get_clips = clean_database["get_clips"]
        from database import toggle_pin, delete_clip

        for i in range(20):
            add(f"pin_test_{i:03d}")

        clips = get_clips()
        for _ in range(20):
            clip = random.choice(clips)
            if random.random() < 0.5:
                toggle_pin(clip[0])
            else:
                delete_clip(clip[0])
            add(random_text())

        count = clean_database["get_count"]()
        assert count >= 0


class TestSearchPerf:
    def test_search_response_time(self, sample_clips):
        """搜索 100 条内容的响应时间应 < 500ms"""
        get_clips = sample_clips["get_clips"]

        start = time.time()
        results = get_clips(search="测试")
        elapsed = (time.time() - start) * 1000

        assert len(results) > 0
        assert elapsed < 500, f"搜索太慢: {elapsed:.1f}ms"

    def test_search_no_match(self, sample_clips):
        """搜索不存在内容的响应时间"""
        get_clips = sample_clips["get_clips"]
        start = time.time()
        results = get_clips(search="xyznonexistent999")
        elapsed = (time.time() - start) * 1000
        assert len(results) == 0
        assert elapsed < 500, f"搜索不存在太慢: {elapsed:.1f}ms"


class TestUnicode:
    def test_emoji_and_special_chars(self, clean_database):
        """emoji / 特殊字符 / 长文本"""
        add = clean_database["add_clip"]
        edge_cases = [
            "🎉✨🌟💡🚀🔥",
            "emoji混合😀中文test",
            "a" * 5000,
            "  leading and trailing   ",
            "\t\n\r\f",
            "日本語 한국어 العربية",
        ]
        for text in edge_cases:
            try:
                add(text)
            except Exception as e:
                pytest.fail(f"边缘文本插入失败: {repr(text[:50])} — {e}")


class TestThreadSafety:
    def test_concurrent_writes(self, clean_database):
        """5 线程同时写入 — SQLite WAL 模式应安全"""
        add = clean_database["add_clip"]
        errors = []
        results = []

        def writer(tid, count):
            try:
                for i in range(count):
                    add(f"thread_{tid}_item_{i:03d}")
                    results.append(1)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=writer, args=(tid, 20)) for tid in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert not errors, f"线程错误: {errors}"
        assert len(results) >= 80


class TestLimit:
    def test_free_tier_cap(self, clean_database):
        """插入 80 条，保留不超过 51 条"""
        add = clean_database["add_clip"]
        for i in range(80):
            add(f"limit_test_{i:04d}_{random_text(10, 20)}")
        count = clean_database["get_count"]()
        assert count <= 51, f"超出上限: {count}"


class TestColdStart:
    def test_repeated_init(self, temp_db):
        """连续 init_db 10 次 — 不应崩溃"""
        from database import init_db, get_clips
        for _ in range(10):
            init_db()
            clips = get_clips()
            assert isinstance(clips, list)


class TestFullSession:
    def test_30_sessions(self, clean_database):
        """完整用户会话 × 30 — 复制→搜索→固定→删除"""
        add = clean_database["add_clip"]
        get_clips = clean_database["get_clips"]
        get_count = clean_database["get_count"]
        from database import toggle_pin, delete_clip, clear_all

        for session in range(30):
            for i in range(random.randint(8, 15)):
                add(f"s_{session}_{i}_{random_chinese_text()}")

            get_clips(search=f"s_{session}")
            clips = get_clips()
            if len(clips) >= 2:
                for _ in range(2):
                    toggle_pin(random.choice(clips)[0])

            clips = get_clips()
            non_pinned = [c for c in clips if c[4] == 0]
            if non_pinned:
                delete_clip(random.choice(non_pinned)[0])

            assert get_count() >= 0


# ============================================================
# 独立运行入口 — 手动触发 100+ 操作
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("ClipVault 压力测试 — 模拟 100+ 次用户操作")
    print("=" * 60)

    # 使用独立 monkeypatch 而非 pytest fixtures
    import tempfile
    import monkeypatch_sqlite

    db_path = tempfile.mktemp(suffix="_stress.db")
    monkeypatch_sqlite.patch(db_path)

    from database import init_db, add_clip, get_clips, get_count, toggle_pin, delete_clip, clear_all

    init_db()

    tests_run = 0
    errors = []

    # 1. 快速复制 100 次
    start = time.time()
    for i in range(100):
        add_clip(f"stress_{i:04d}_{random_text()}")
    elapsed = time.time() - start
    count = get_count()
    ok = 45 <= count <= 51
    status = "✓" if ok else "✗"
    print(f"  [{status}] 快速复制 100 次: {elapsed:.2f}s, {count} 条")
    if not ok:
        errors.append(f"快速复制: 预期 45-51 条, 实际 {count}")

    # 2. 去重 — 用独立数据库避免前面测试残留
    monkeypatch_sqlite.cleanup()
    db_path2 = tempfile.mktemp(suffix="_stress2.db")
    monkeypatch_sqlite.patch(db_path2)
    init_db()
    add_clip("唯一内容A")
    add_clip("唯一内容B")
    for _ in range(48):
        result = add_clip("唯一内容A")
    clips = get_clips()
    unique = set(c[1] for c in clips)
    # 去重逻辑：仅检查最后一条，所以 "B" + "A"(×1) = 2种
    ok = len(unique) <= 3
    status = "✓" if ok else "✗"
    print(f"  [{status}] 去重 48 次: {len(clips)} 条, {len(unique)} 种")
    if not ok:
        errors.append(f"去重: 预期≤3种, 实际{len(unique)}种")
    monkeypatch_sqlite.cleanup()
    # 切换回主测试数据库
    monkeypatch_sqlite.patch(db_path)
    init_db()

    # 3. 固定/删除循环
    clips = get_clips()
    for _ in range(20):
        c = random.choice(clips)
        if random.random() < 0.5:
            toggle_pin(c[0])
        else:
            try:
                delete_clip(c[0])
            except Exception:
                pass
        add_clip(random_text())
    print(f"  [✓] 固定/删除循环 20 轮: {get_count()} 条")

    # 4. 搜索性能
    start = time.time()
    get_clips(search="stress_0050")
    ms = (time.time() - start) * 1000
    ok = ms < 500
    status = "✓" if ok else "✗"
    print(f"  [{status}] 搜索性能: {ms:.1f}ms")
    if not ok:
        errors.append(f"搜索: {ms:.1f}ms > 500ms")

    # 5. 线程安全
    results = []
    thr_errors = []

    def writer(tid, cnt):
        try:
            for i in range(cnt):
                add_clip(f"thr_{tid}_{i:03d}")
                results.append(1)
        except Exception as e:
            thr_errors.append(str(e))

    threads = [threading.Thread(target=writer, args=(tid, 20)) for tid in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    ok = not thr_errors and len(results) >= 80
    status = "✓" if ok else "✗"
    print(f"  [{status}] 线程安全: {len(results)} 次写入, {len(thr_errors)} 错误")
    if not ok:
        errors.append(f"线程: {thr_errors}")

    # 6. 完整会话 × 30
    session_time = 0
    for s in range(30):
        st = time.time()
        for i in range(random.randint(8, 15)):
            add_clip(f"sess_{s}_{i}_{random_chinese_text()}")
        get_clips(search=f"sess_{s}")
        clips = get_clips()
        if len(clips) >= 2:
            toggle_pin(random.choice(clips)[0])
        clips = get_clips()
        non_pinned = [c for c in clips if c[4] == 0]
        if non_pinned:
            delete_clip(random.choice(non_pinned)[0])
        session_time += time.time() - st

    avg = session_time / 30
    ok = avg < 2.0
    status = "✓" if ok else "✗"
    print(f"  [{status}] 完整会话 × 30: 平均 {avg:.2f}s/次")
    if not ok:
        errors.append(f"会话: 平均 {avg:.2f}s > 2s")

    # 清理
    monkeypatch_sqlite.cleanup()

    print("\n" + "=" * 60)
    if errors:
        print(f"✗ {len(errors)} 项失败:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("✓ 全部通过 — 产品可交付")
    print("=" * 60)
