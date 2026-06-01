"""时家奇门排盘测试"""
import datetime
import pytest
from engine.shijia_board import calculate_board_shijia, build_di_pan
from engine.dingju import determine_board


class TestDiPan:
    def test_yang_1(self):
        """阳遁1局：戊在坎1宫，顺排"""
        pan = build_di_pan(1, True)
        assert pan[0] == "戊"
        # 阳遁: 戊己庚辛壬癸丁丙乙 顺排
        assert pan[8] == "乙"

    def test_yin_1(self):
        """阴遁1局：戊在坎1宫，逆排"""
        pan = build_di_pan(1, False)
        assert pan[0] == "戊"
        # 阴遁: 戊乙丙丁癸壬辛庚己 逆排
        assert pan[8] == "己"


class TestShiJiaBoard:
    def test_board_creation(self):
        dt = datetime.datetime(2024, 6, 1, 10, 0)
        board = calculate_board_shijia(dt)
        assert board is not None
        assert board.dun in ["阳遁", "阴遁"]
        assert 1 <= board.ju <= 9
        assert len(board.pan) == 9

    def test_zhifu_zhishi(self):
        dt = datetime.datetime(2024, 6, 1, 10, 0)
        board = calculate_board_shijia(dt)
        assert board.zhi_fu_star != ""
        assert board.zhi_shi_door != ""

    def test_dingju_modes(self):
        dt = datetime.datetime(2024, 6, 1, 10, 0)
        b1 = calculate_board_shijia(dt, "置闰法")
        b2 = calculate_board_shijia(dt, "拆补法")
        assert b1.ju != 0
        assert b2.ju != 0
