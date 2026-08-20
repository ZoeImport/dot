"""日家奇门排盘测试"""
import datetime
import pytest
from engine.rija_board import calculate_board_rija, get_xiu_gong
from engine.calendar_core import get_ganzhi_day, is_yang_dun, get_ganzhi_full


class TestRiJia:
    def test_board_creation(self):
        dt = datetime.datetime(2024, 8, 15, 0, 0)
        board = calculate_board_rija(dt)
        assert board is not None
        assert len(board.doors) == 8
        assert len(board.stars) == 9
        assert board.xi_shen != ""

    def test_xiu_gong_mapped(self):
        """甲子日休门应在坎1宫"""
        gong = get_xiu_gong("甲子")
        assert gong == 1

    def test_heihuangdao(self):
        dt = datetime.datetime(2024, 8, 15, 0, 0)
        board = calculate_board_rija(dt)
        assert len(board.heihuangdao) == 12

    def test_guiren(self):
        dt = datetime.datetime(2024, 8, 15, 0, 0)
        board = calculate_board_rija(dt)
        assert len(board.tianyi_gui_ren) > 0
