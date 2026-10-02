"""Deterministic annotations; no fortune scoring or inferred user context.

These rules expose evidence even when conflicting. They do not certify the
experimental hour-board calculation that supplied the palaces.
"""
from .calendar_core import DI_ZHI
from .models import DOOR_GONG_MAP, STAR_GONG_MAP

BRANCH_GONG = {"子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
               "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6}
GONG_ELEMENT = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
DOOR_ELEMENT = {"休门": "水", "生门": "土", "伤门": "木", "杜门": "木",
                "景门": "火", "死门": "土", "惊门": "金", "开门": "金"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
PUNISHMENT = {"戊": {3}, "己": {2}, "庚": {8}, "辛": {9}, "壬": {4}, "癸": {4}}
TOMBS = {"乙": {2}, "丙": {6}, "丁": {8}}
NAMED_PAIRS = {("戊", "丙"): "青龙返首", ("丙", "戊"): "飞鸟跌穴",
               ("辛", "乙"): "白虎猖狂", ("乙", "辛"): "青龙逃走"}


def analyze_shijia(ganzhi, xun_shou, pan):
    """Return structured markers and pattern names from an explicit board.

    Uses hour 旬空 and hour-branch 驿马; 三奇墓库 follows 阳干顺、阴干逆.
    五不遇时 requires both 克日干 and matching stem parity.
    """
    markers = []
    patterns = []

    def add(rule, gong=None, **evidence):
        markers.append({"rule": rule, "gong": gong, "evidence": evidence})
        if gong is not None and rule not in pan[gong - 1].notes:
            pan[gong - 1].notes.append(rule)

    first_zhi = DI_ZHI.index(xun_shou[1])
    void = [DI_ZHI[(first_zhi - 2) % 12], DI_ZHI[(first_zhi - 1) % 12]]
    for z in void:
        add("旬空", BRANCH_GONG[z], branch=z, xun_shou=xun_shou)
    horse = {0: "寅", 1: "亥", 2: "申", 3: "巳"}[DI_ZHI.index(ganzhi["hour"][1]) % 4]
    add("驿马", BRANCH_GONG[horse], branch=horse, basis="时支")
    stems = "甲乙丙丁戊己庚辛壬癸"
    elements = "木木火火土土金金水水"
    day_idx, hour_idx = stems.index(ganzhi["day"][0]), stems.index(ganzhi["hour"][0])
    if day_idx % 2 == hour_idx % 2 and CONTROLS[elements[hour_idx]] == elements[day_idx]:
        add("五不遇时", day_stem=stems[day_idx], hour_stem=stems[hour_idx])
        patterns.append("五不遇时")
    for g in pan:
        palace, stem = g.gong_index, g.tian_qi_yi
        if palace in PUNISHMENT.get(stem, set()):
            add("六仪击刑", palace, stem=stem)
        if palace in TOMBS.get(stem, set()):
            add("三奇入墓", palace, stem=stem)
        if g.door:
            door_el, palace_el = DOOR_ELEMENT[g.door], GONG_ELEMENT[palace]
            if CONTROLS[door_el] == palace_el:
                add("门迫", palace, door=g.door, relation="门克宫")
            elif CONTROLS[palace_el] == door_el:
                add("宫克门", palace, door=g.door)
        name = NAMED_PAIRS.get((stem, g.di_qi_yi))
        if name:
            add(name, palace, tian=stem, di=g.di_qi_yi)
            patterns.append(name)
    outer = [g for g in pan if g.gong_index != 5]
    for label, attr, original in (("门", "door", DOOR_GONG_MAP), ("星", "star", STAR_GONG_MAP)):
        if all(getattr(g, attr) == original[g.gong_index] for g in outer):
            add(label + "伏吟")
            patterns.append(label + "伏吟")
        if all(getattr(g, attr) == original[10 - g.gong_index] for g in outer):
            add(label + "反吟")
            patterns.append(label + "反吟")
    return markers, list(dict.fromkeys(patterns))
