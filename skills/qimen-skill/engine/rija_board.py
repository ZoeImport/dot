"""
日家奇门 (Day-based Qi Men) Board Calculation Module

Implements the day-based Qi Men Dun Jia board calculation, which differs
significantly from the hour-based (时家) system:
- Uses different 九星: 太乙, 摄提, 轩辕, 招摇, 天符, 青龙, 咸池, 太阴, 天乙
- 休门 changes every 3 days (三日一宫)
- 八门 determined by 日干 (阳顺阴逆), NOT by 值使
- Has 十二黑黄道, 喜神方位, 天乙贵人, 截路空亡
- Does NOT have 值符/值使/地盘/天盘 concept (those are for 时家)
"""

import datetime
from typing import Dict, List

from .models import RiJiaBoard, RI_JIA_STARS, HEI_HUANG_DAO
from .calendar_core import (
    get_ganzhi_full,
    get_ganzhi_day,
    is_yang_dun,
    TIAN_GAN,
    DI_ZHI,
    get_xun_shou,
    GANZHI_INDEX,
    SIXTY_JIAZI,
)


# ============================================================
# Constants — 日家奇门
# ============================================================

# 阳遁起休门歌（三日一宫口诀）:
#   甲戊壬子坎为休(1), 丁辛乙卯向坤游(2),
#   庚甲戊午居震位(3), 癸丁辛酉巽方求(4),
#   庚丙鼠入乾乡去(6), 己癸兔居水泽留(7),
#   壬丙马行山上路(8), 乙己鸡与火为休(9).
#
# Maps specific 四仲日 (子/午/卯/酉) ganzhi to 休门 palace.
YANG_XIU_MAP: Dict[str, int] = {
    "甲子": 1, "戊子": 1, "壬子": 1,
    "丁卯": 2, "辛卯": 2, "乙卯": 2,
    "庚午": 3, "甲午": 3, "戊午": 3,
    "癸酉": 4, "丁酉": 4, "辛酉": 4,
    "丙子": 6, "庚子": 6,
    "己卯": 7, "癸卯": 7,
    "丙午": 8, "壬午": 8,
    "乙酉": 9, "己酉": 9,
}

# 四仲日地支 — used for 三日一宫 fallback logic
SI_ZHONG_ZHI: set = {"子", "午", "卯", "酉"}

# 九星太乙歌诀:
#   甲子为头起艮(8), 甲戌飞入离宫(9),
#   猿猴翻入水晶宫(1/坎), 甲午坤宫不动(2).
#   曾见龙生震地(3), 再看虎啸生风(4),
#   九星殿上显奇功, 太乙临之法用.
TAI_YI_GONG_MAP: Dict[str, int] = {
    "甲子": 8,  # 艮
    "甲戌": 9,  # 离
    "甲申": 1,  # 坎
    "甲午": 2,  # 坤
    "甲辰": 3,  # 震
    "甲寅": 4,  # 巽
}

# 阳遁星宫顺序 (太乙→... 按此顺序填入各宫)
YANG_STAR_GONG_ORDER: List[int] = [8, 9, 1, 2, 3, 4, 5, 6, 7]

# 阴遁星宫顺序
YIN_STAR_GONG_ORDER: List[int] = [2, 1, 9, 8, 7, 6, 5, 4, 3]

# 八门顺序: 休生伤杜景死惊开
DOORS_ORDER: List[str] = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]

# 阳干 (阳日顺布八门)
YANG_GAN: set = {"甲", "丙", "戊", "庚", "壬"}

# 喜神方位
XI_SHEN_MAP: Dict[str, str] = {
    "甲": "艮(东北)", "乙": "乾(西北)", "丙": "坤(西南)", "丁": "离(南)",
    "戊": "巽(东南)", "己": "震(东)", "庚": "巽(东南)", "辛": "离(南)",
    "壬": "兑(西)", "癸": "震(东)",
}

# 天乙贵人: 甲戊庚牛羊(丑未), 乙己鼠猴乡(子申),
#           丙丁猪鸡位(亥酉), 辛逢虎马(寅午),
#           壬癸兔蛇藏(卯巳)
TIAN_YI_GUI_REN_MAP: Dict[str, tuple] = {
    "甲": ("丑", "未"),
    "乙": ("子", "申"),
    "丙": ("亥", "酉"),
    "丁": ("亥", "酉"),
    "戊": ("丑", "未"),
    "己": ("子", "申"),
    "庚": ("丑", "未"),
    "辛": ("寅", "午"),
    "壬": ("卯", "巳"),
    "癸": ("卯", "巳"),
}

# 截路空亡: 甲己申酉, 乙庚午未, 丙辛辰巳, 丁壬寅卯, 戊癸子丑
JIE_LU_KONG_WANG_MAP: Dict[str, tuple] = {
    "甲": ("申", "酉"),
    "乙": ("午", "未"),
    "丙": ("辰", "巳"),
    "丁": ("寅", "卯"),
    "戊": ("子", "丑"),
    "己": ("申", "酉"),
    "庚": ("午", "未"),
    "辛": ("辰", "巳"),
    "壬": ("寅", "卯"),
    "癸": ("子", "丑"),
}


# ============================================================
# Palace Navigation Helpers (八门, skip 中5宫)
# ============================================================

def _next_clockwise(gong: int) -> int:
    """Get next palace in clockwise (顺飞) order, skipping 中5宫.

    顺飞: 1→2→3→4→6→7→8→9→1→...
    """
    n = gong % 9 + 1
    return 6 if n == 5 else n


def _next_counterclockwise(gong: int) -> int:
    """Get next palace in counter-clockwise (逆飞) order, skipping 中5宫.

    逆飞: 1→9→8→7→6→4→3→2→1→...
    """
    n = gong - 1 if gong > 1 else 9
    return 4 if n == 5 else n


# ============================================================
# Section 1: 休门 Palace — 三日一宫
# ============================================================

def get_xiu_gong(ganzhi: str) -> int:
    """Find the 休门 palace for a given day ganzhi (三日一宫 rule).

    For 四仲日 (子/午/卯/酉), looks up directly in YANG_XIU_MAP.
    For other days, walks backwards up to 3 days to find the nearest
    四仲日 anchor (休门 stays in the same palace for 3 consecutive days).

    Args:
        ganzhi: Day ganzhi string (e.g. "甲子", "丙寅").

    Returns:
        Palace number (1-9, never 5) where 休门 resides.
    """
    if ganzhi in YANG_XIU_MAP:
        return YANG_XIU_MAP[ganzhi]

    idx = GANZHI_INDEX[ganzhi]
    for offset in range(1, 4):
        prev_idx = (idx - offset) % 60
        prev_gz = SIXTY_JIAZI[prev_idx]
        if prev_gz[1] in SI_ZHONG_ZHI:
            return YANG_XIU_MAP[prev_gz]

    raise ValueError(f"Cannot find xiu gong for {ganzhi}")


# ============================================================
# Section 2: 太乙 — 九星 starting palace
# ============================================================

def get_taiyi_gong(xun_shou: str, is_yang: bool) -> int:
    """Find the 太乙 starting palace for a given 旬首.

    Uses the 九星太乙歌诀:
        甲子→艮(8), 甲戌→离(9), 甲申→坎(1),
        甲午→坤(2), 甲辰→震(3), 甲寅→巽(4)

    The is_yang parameter is accepted for interface consistency with
    the star placement logic; the 太乙 placement itself is the same
    regardless of 阳遁/阴遁.

    Args:
        xun_shou: Xun shou string (e.g. "甲子").
        is_yang: Whether it's 阳遁.

    Returns:
        Palace number (1-9) where 太乙 resides.
    """
    return TAI_YI_GONG_MAP[xun_shou]


# ============================================================
# Section 3: 八门 Placement (阳顺阴逆)
# ============================================================

def _place_doors(xiu_gong: int, day_gan: str) -> Dict[int, str]:
    """Place the 八门 around the 九宫格.

    Rules:
        - 休门 starts at xiu_gong
        - 阳日 (甲丙戊庚壬): clockwise (顺飞), skip 中5宫
        - 阴日 (乙丁己辛癸): counter-clockwise (逆飞), skip 中5宫

    Args:
        xiu_gong: Palace where 休门 is placed.
        day_gan: Day 天干 (first char of day ganzhi).

    Returns:
        Dict mapping palace number → door name.
    """
    is_yang = day_gan in YANG_GAN
    doors: Dict[int, str] = {}

    current = xiu_gong
    for door in DOORS_ORDER:
        doors[current] = door
        # Advance to next palace (skip after last door)
        if door != "开门":
            current = _next_clockwise(current) if is_yang else _next_counterclockwise(current)

    return doors


# ============================================================
# Section 4: 九星 Placement (日家九星)
# ============================================================

def _place_stars(taiyi_gong: int, is_yang: bool) -> Dict[int, str]:
    """Place the 日家九星 around the 九宫格.

    Order:
        - 阳遁 star gong sequence: [8,9,1,2,3,4,5,6,7]
        - 阴遁 star gong sequence: [2,1,9,8,7,6,5,4,3]

    太乙 starts at its determined gong, then remaining 8 stars
    are placed following the sequence in order.

    Unlike 八门, 九星 DO occupy 中5宫 (all 9 palaces for 9 stars).

    Args:
        taiyi_gong: Palace where 太乙 is placed.
        is_yang: Whether it's 阳遁.

    Returns:
        Dict mapping palace number → star name.
    """
    order = YANG_STAR_GONG_ORDER if is_yang else YIN_STAR_GONG_ORDER
    start_idx = order.index(taiyi_gong)

    stars: Dict[int, str] = {}
    for i, star in enumerate(RI_JIA_STARS):
        gong = order[(start_idx + i) % 9]
        stars[gong] = star

    return stars


# ============================================================
# Section 5: 十二黑黄道
# ============================================================

def _get_heihuangdao(day_zhi: str) -> List[str]:
    """Get the 十二黑黄道 for the day.

    Starting from the 日支's position in the HEI_HUANG_DAO list:
        子→青龙(黄道), 丑→明堂(黄道), 寅→天刑(黑道), ...

    Args:
        day_zhi: Day 地支 (second char of day ganzhi).

    Returns:
        List of 12 strings, each "名称(类型)".
    """
    start_idx = DI_ZHI.index(day_zhi)
    result: List[str] = []
    for i in range(12):
        idx = (start_idx + i) % 12
        name, htype = HEI_HUANG_DAO[idx]
        result.append(f"{name}({htype})")
    return result


# ============================================================
# Section 6: Main Calculation
# ============================================================

def calculate_board_rija(dt: datetime.datetime) -> RiJiaBoard:
    """Calculate the full 日家奇门 board for a given datetime.

    Computes all components:
        1. 四柱八字 (4-pillar ganzhi)
        2. 阳遁/阴遁 determination
        3. 休门 palace via 三日一宫 rule
        4. 八门 placement (阳顺阴逆)
        5. 九星 placement (太乙 starting gong + sequence)
        6. 十二黑黄道
        7. 喜神方位
        8. 天乙贵人
        9. 截路空亡

    Args:
        dt: The datetime to calculate the board for.

    Returns:
        RiJiaBoard dataclass with all computed fields.
    """
    # 1. Four-pillar ganzhi
    ganzhi_full = get_ganzhi_full(dt, dt.hour)
    day_gz = ganzhi_full["day"]
    day_gan = day_gz[0]
    day_zhi = day_gz[1]

    # 2. Yang/Yin dun
    is_yang = is_yang_dun(dt)

    # 3. 休门 palace (三日一宫)
    xiu_gong = get_xiu_gong(day_gz)

    # 4. 八门 placement
    doors = _place_doors(xiu_gong, day_gan)

    # 5. 旬首
    xun_shou = get_xun_shou(day_gz)

    # 6. 太乙 starting palace
    taiyi_gong = get_taiyi_gong(xun_shou, is_yang)

    # 7. 九星 placement
    stars = _place_stars(taiyi_gong, is_yang)

    # 8. 十二黑黄道
    heihuangdao = _get_heihuangdao(day_zhi)

    # 9. 喜神方位
    xi_shen = XI_SHEN_MAP[day_gan]

    # 10. 天乙贵人
    tianyi = TIAN_YI_GUI_REN_MAP[day_gan]

    # 11. 截路空亡
    jie_lu_str = JIE_LU_KONG_WANG_MAP[day_gan]
    jie_lu = "".join(jie_lu_str)

    return RiJiaBoard(
        input_datetime=dt.isoformat(),
        ganzhi=ganzhi_full,
        is_yang=is_yang,
        xiu_gong=xiu_gong,
        doors=doors,
        stars=stars,
        heihuangdao=heihuangdao,
        xi_shen=xi_shen,
        tianyi_gui_ren=list(tianyi),
        jie_lu=jie_lu,
    )
