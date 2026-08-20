"""干支历法核心测试"""
import datetime
import pytest
from engine.calendar_core import (
    get_ganzhi_day, get_ganzhi_hour, get_ganzhi_year,
    get_ganzhi_month, get_ganzhi_full,
    get_futou, get_xun_shou, is_yang_dun, get_current_solar_term,
    get_xun_yi, get_yuan_by_futou, SIXTY_JIAZI
)


class TestGanzhi:
    def test_known_date(self):
        """2000-01-01 = 甲子日"""
        assert get_ganzhi_day(datetime.date(2000, 1, 1)) == "甲子"

    def test_hour_ganzhi_jia(self):
        """甲日 子时 = 甲子"""
        assert get_ganzhi_hour(0, "甲") == "甲子"

    def test_hour_ganzhi_yi(self):
        """乙日 子时 = 丙子"""
        assert get_ganzhi_hour(0, "乙") == "丙子"

    def test_futou(self):
        """符头必须是甲/己日"""
        f = get_futou(datetime.date(2024, 3, 15))
        assert f <= datetime.date(2024, 3, 15)
        assert get_ganzhi_day(f)[0] in ["甲", "己"]

    def test_xun_shou(self):
        assert get_xun_shou("甲子") == "甲子"
        assert get_xun_shou("乙丑") == "甲子"
        assert get_xun_shou("甲戌") == "甲戌"
        assert get_xun_shou("癸未") == "甲戌"

    def test_xun_yi(self):
        assert get_xun_yi("甲子") == "戊"
        assert get_xun_yi("甲申") == "庚"

    def test_yang_dun(self):
        """冬至→夏至前为阳遁"""
        assert is_yang_dun(datetime.date(2024, 6, 1)) is True
        assert is_yang_dun(datetime.date(2024, 7, 1)) is False


class TestGanzhiFull:
    def test_full_ganzhi(self):
        gz = get_ganzhi_full(datetime.date(2024, 3, 20), 12)
        assert all(k in gz for k in ["year", "month", "day", "hour"])
        assert all(len(v) == 2 for v in gz.values())


class TestYuan:
    def test_yuan_by_futou(self):
        from engine.calendar_core import get_ganzhi_day
        # 甲申日 → 申=中元
        f = datetime.date(2024, 3, 15)
        assert get_yuan_by_futou(f) in ["上元", "中元", "下元"]
