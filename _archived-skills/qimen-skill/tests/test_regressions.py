"""Audited fixtures, complete sexagenary-cycle invariants, and boundary cases."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from lunar_python import Solar
from engine.calendar_core import (
    SIXTY_JIAZI, get_ganzhi_full, get_ganzhi_day, get_ganzhi_month,
    get_ganzhi_year, get_current_solar_term, is_yang_dun,
    find_solar_term_date, SOLAR_TERMS, _to_datetime, _to_ephem_date,
)
from engine.rija_board import (
    calculate_board_rija, get_xiu_gong, get_taiyi_gong, _place_doors,
    _place_stars, _get_heihuangdao, YANG_XIU_MAP, YIN_XIU_MAP,
    XI_SHEN_MAP, YIN_TAI_YI_GONG_MAP,
)
from engine.analysis_rules import analyze_shijia
from engine.models import GongData, DOOR_GONG_MAP, STAR_GONG_MAP
from engine.utils import board_to_dict, calculate, format_rija_text
from engine.shijia_board import calculate_board_shijia


def test_audited_daily_board():
    b = calculate_board_rija(datetime(2026, 10, 2, 8))
    assert b.ganzhi == dict(year="丙午", month="丁酉", day="己酉", hour="戊辰")
    assert not b.is_yang
    assert (b.xiu_gong, b.xun_shou, b.xun_day, b.taiyi_gong) == (1, "甲辰", 6, 2)
    assert b.doors == {1:"休门",2:"杜门",3:"惊门",4:"死门",6:"生门",7:"伤门",8:"开门",9:"景门"}
    assert b.stars == {1:"摄提",2:"太乙",3:"天乙",4:"太阴",5:"咸池",6:"青龙",7:"天符",8:"招摇",9:"轩辕"}
    assert b.xi_shen == "艮(东北)"
    assert b.tianyi_gui_ren == ["子", "申"] and b.jie_lu == "申酉"
    assert b.heihuangdao == ["司命(黄道)","勾陈(黑道)","青龙(黄道)","明堂(黄道)",
                           "天刑(黑道)","朱雀(黑道)","金匮(黄道)","天德(黄道)",
                           "白虎(黑道)","玉堂(黄道)","天牢(黑道)","玄武(黑道)"]
    assert b.conflicts == [{"branch":"申", "signals":["天乙贵人","截路空亡"]}]
    assert json.loads(json.dumps(board_to_dict(b), ensure_ascii=False))["taiyi_gong"] == 2
    assert "冲突信号: 申" in format_rija_text(b)


@pytest.mark.parametrize("yang", [True, False])
def test_all_sixty_days(yang):
    for index, gz in enumerate(SIXTY_JIAZI):
        anchor = SIXTY_JIAZI[index - index % 3]
        mapping = YANG_XIU_MAP if yang else YIN_XIU_MAP
        palace = get_xiu_gong(gz, yang)
        assert palace == mapping[anchor]
        doors = _place_doors(palace, gz[0])
        assert set(doors) == {1,2,3,4,6,7,8,9}
        assert len(set(doors.values())) == 8
        taiyi = get_taiyi_gong(gz, yang)
        stars = _place_stars(taiyi, yang)
        assert set(stars) == set(range(1,10)) and len(set(stars.values())) == 9
        assert stars[taiyi] == "太乙"
        if index % 10 != 9:
            following = get_taiyi_gong(SIXTY_JIAZI[index + 1], yang)
            assert following == (taiyi - 1 + (1 if yang else -1)) % 9 + 1


def test_yin_xun_fixture():
    assert [get_taiyi_gong(gz, False) for gz in SIXTY_JIAZI[40:50]] == [7,6,5,4,3,2,1,9,8,7]
    assert [get_taiyi_gong(gz, True) for gz in SIXTY_JIAZI[0:10]] == [8,9,1,2,3,4,5,6,7,8]


@pytest.mark.parametrize("yang", [True, False])
def test_three_day_wraparound(yang):
    assert get_xiu_gong("壬戌", yang) == get_xiu_gong("癸亥", yang) == get_xiu_gong("辛酉", yang)


def test_clockwise_geography():
    assert _place_doors(1,"甲") == {1:"休门",8:"生门",3:"伤门",4:"杜门",9:"景门",2:"死门",7:"惊门",6:"开门"}
    assert _place_doors(1,"己") == {1:"休门",6:"生门",7:"伤门",2:"杜门",9:"景门",4:"死门",3:"惊门",8:"开门"}


def test_all_hour_path_anchors():
    # Independent traditional 青龙 starting-hour table, 子..亥 day branches.
    for day, hour in zip("子丑寅卯辰巳午未申酉戌亥", "申戌子寅辰午申戌子寅辰午"):
        result = _get_heihuangdao(day)
        assert result["子丑寅卯辰巳午未申酉戌亥".index(hour)] == "青龙(黄道)"
        assert len(set(result)) == 12


def test_parameter_file_matches_engine():
    d = json.loads((Path(__file__).parents[1]/"data/rija_params.json").read_text())
    assert d["阳遁休门定宫"] == YANG_XIU_MAP
    assert d["阴遁休门定宫"] == YIN_XIU_MAP
    assert d["阴遁太乙起始宫"] == YIN_TAI_YI_GONG_MAP
    assert d["喜神方位"] == XI_SHEN_MAP
    assert [XI_SHEN_MAP[g] for g in "己庚辛壬癸"] == [XI_SHEN_MAP[g] for g in "甲乙丙丁戊"]


def test_calendar_crosscheck_across_centuries():
    # Independent day-cycle implementation: arithmetic here vs Shou Xing calendar.
    for year in range(1900,2101,10):
        for month in range(1,13):
            d = date(year,month,15)
            lunar = Solar.fromYmd(year,month,15).getLunar()
            assert get_ganzhi_day(d) == lunar.getDayInGanZhi()
            year_gz = get_ganzhi_year(d)
            assert year_gz == lunar.getYearInGanZhiExact()
            assert get_ganzhi_month(d, year_gz) == lunar.getMonthInGanZhiExact()
    assert get_ganzhi_day(date(1999,12,31)) == "丁巳"


def test_timezone_equivalence_and_midnight():
    local = calculate_board_rija(datetime(2026,10,2,8))
    utc = calculate_board_rija(datetime(2026,10,2,0,tzinfo=timezone.utc))
    assert board_to_dict(local) == board_to_dict(utc)
    assert calculate_board_rija(datetime(2026,10,1,16,tzinfo=timezone.utc)).ganzhi["day"] == "己酉"
    assert calculate_board_rija(datetime(2026,10,2,23)).ganzhi["day"] == "己酉"
    assert calculate_board_rija(datetime(2026,10,3,0)).ganzhi["day"] == "庚戌"


@pytest.mark.parametrize("term,previous", [("夏至","芒种"),("冬至","大雪"),("立春","大寒"),("小寒","冬至")])
def test_term_instant_boundaries(term, previous):
    boundary = _to_datetime(find_solar_term_date(2026,SOLAR_TERMS[term]))
    before = boundary - timedelta(seconds=1)
    assert get_current_solar_term(before) == previous
    assert get_current_solar_term(boundary) == term
    if term == "夏至":
        assert is_yang_dun(before) and not is_yang_dun(boundary)
    if term == "冬至":
        assert not is_yang_dun(before) and is_yang_dun(boundary)
    if term == "立春":
        assert get_ganzhi_year(before) == "乙巳"
        assert get_ganzhi_year(boundary) == "丙午"
        assert get_ganzhi_month(before,"乙巳") == "己丑"
        assert get_ganzhi_month(boundary,"丙午") == "庚寅"
    # Daily convention: switch on the solstice's local civil date, one board/day.
    a = calculate_board_rija(boundary.replace(hour=0))
    b = calculate_board_rija(boundary.replace(hour=23))
    assert (a.is_yang,a.doors,a.stars) == (b.is_yang,b.doors,b.stars)


def test_ephem_string_conversion():
    assert _to_ephem_date("2026/10/2") is not None


def test_rules_positive_and_negative():
    pan = [GongData(i) for i in range(1,10)]
    pan[1].tian_qi_yi = "乙" # 阴木墓未，坤二
    pan[2].tian_qi_yi = "戊" # 戊刑卯，震三
    pan[5].tian_qi_yi = "丙" # 阳火墓戌，乾六
    pan[7].tian_qi_yi = "丁" # 阴火墓丑，艮八
    pan[7].door = "伤门" # 木克土，门迫
    pan[0].tian_qi_yi, pan[0].di_qi_yi = "戊", "丙"
    markers, patterns = analyze_shijia({"day":"甲子","hour":"庚午"},"甲子",pan)
    rules = {(m["rule"],m["gong"]) for m in markers}
    assert {("旬空",6),("驿马",2),("五不遇时",None),("六仪击刑",3),
            ("三奇入墓",2),("三奇入墓",6),("三奇入墓",8),("门迫",8)} <= rules
    assert "青龙返首" in patterns
    # 辛克甲，但阴阳不同，不是五不遇时。
    markers, _ = analyze_shijia({"day":"甲子","hour":"辛未"},"甲午",[GongData(i) for i in range(1,10)])
    assert not any(m["rule"] == "五不遇时" for m in markers)
    for reversal in (False,True):
        pan = [GongData(i,door=DOOR_GONG_MAP.get(10-i if reversal else i,""),
                          star=STAR_GONG_MAP[10-i if reversal else i]) for i in range(1,10)]
        _, patterns = analyze_shijia({"day":"己酉","hour":"戊辰"},"甲子",pan)
        assert ("门反吟" if reversal else "门伏吟") in patterns
        assert ("星反吟" if reversal else "星伏吟") in patterns


def test_hour_annotations_survive_serialization():
    data = board_to_dict(calculate_board_shijia(datetime(2026,10,2,8)))
    assert data["markers"] and data["notes"] and data["status"] == "experimental"
    assert any(m["rule"] == "旬空" for m in data["markers"])


def test_entry_point_rejects_unknown_board_type():
    with pytest.raises(ValueError):
        calculate("2026-10-02", "typo")
    assert calculate("2026-10-02T00:00:00+00:00","日家").ganzhi["hour"] == "戊辰"


def test_dingju_cross_year_and_futou_yuan():
    from engine.dingju import dingju_maoshan, dingju_chaibu, determine_board, _current_term_start
    assert _current_term_start(date(2026,1,1)) == ("冬至",date(2025,12,21))
    assert dingju_maoshan(date(2026,1,1)) == ("阳遁","阳遁4局","茅山","下元")
    assert dingju_maoshan(date(2026,10,2))[3] == "中元"
    # 己酉为上元符头：接下来四天虽然日支不同，拆补仍应上元。
    for day in range(2,7):
        assert dingju_chaibu(date(2026,10,day))[3] == "上元"
    with pytest.raises(ValueError):
        determine_board(date(2026,10,2),"typo")


def test_historical_term_table_has_fixed_utc_offset():
    table = Solar.fromYmd(1990,6,1).getLunar().getJieQiTable()["夏至"]
    fixed = datetime.strptime(table.toYmdHms(),"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=8)))
    instant = _to_datetime(find_solar_term_date(1990,90))
    assert abs((instant.astimezone(timezone.utc) - fixed.astimezone(timezone.utc)).total_seconds()) < 0.0001
