"""
Calendar core module for Qi Men Dun Jia calculation.

Provides functions for:
- Solar term (节气) instants using a pinned Shou Xing calendar table
- Ganzhi (天干地支) for year, month, day, hour
- Futou (符头), Xun Shou (旬首), Xun Yi (六仪)
- Yang/Yin Dun determination
- Yuan (元) determination
"""

import ephem
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from functools import lru_cache
from lunar_python import Solar
from typing import List, Dict, Union

SHANGHAI = ZoneInfo("Asia/Shanghai")

def normalize_datetime(d: datetime) -> datetime:
    """Naive input is Beijing civil time; aware input is converted to Beijing."""
    return d.replace(tzinfo=SHANGHAI) if d.tzinfo is None else d.astimezone(SHANGHAI)



# ============================================================
# Constants
# ============================================================

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六十甲子 (Sexagenary cycle)
SIXTY_JIAZI = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

# 干支索引 (ganzhi string -> sexagenary index 0-59)
GANZHI_INDEX = {gz: i for i, gz in enumerate(SIXTY_JIAZI)}

# 24节气名称 in canonical order (立春->大寒, by solar longitude)
TERM_NAMES = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

# 节气 -> 太阳黄经 (solar longitude)
SOLAR_TERMS = {
    "立春": 315, "雨水": 330, "惊蛰": 345, "春分": 0,
    "清明": 15,  "谷雨": 30,  "立夏": 45,  "小满": 60,
    "芒种": 75,  "夏至": 90,  "小暑": 105, "大暑": 120,
    "立秋": 135, "处暑": 150, "白露": 165, "秋分": 180,
    "寒露": 195, "霜降": 210, "立冬": 225, "小雪": 240,
    "大雪": 255, "冬至": 270, "小寒": 285, "大寒": 300,
}

# 阳遁局数表 (每个节气的上/中/下三元局数)
YANG_JU_TABLE = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (4, 1, 7), "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
}

# 阴遁局数表 (每个节气的上/中/下三元局数)
YIN_JU_TABLE = {
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "处暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (6, 9, 3), "霜降": (5, 8, 2),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}

# 三元索引: 符头地支 -> 上元/中元/下元
YUAN_INDEX = {
    "子": "上元", "午": "上元", "卯": "上元", "酉": "上元",
    "寅": "中元", "申": "中元", "巳": "中元", "亥": "中元",
    "辰": "下元", "戌": "下元", "丑": "下元", "未": "下元",
}

# 12节气 (节) -- 用于定月, 按黄经顺序
# 立春->寅月, 惊蛰->卯月, 清明->辰月, 立夏->巳月,
# 芒种->午月, 小暑->未月, 立秋->申月, 白露->酉月,
# 寒露->戌月, 立冬->亥月, 大雪->子月, 小寒->丑月
JIE_TERMS = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
             "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]
JIE_LONGITUDES = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
JIE_ZHI = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

# 六仪映射: 旬首 -> 所遁之仪
XUN_YI_MAP = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
}


# ============================================================
# Internal helpers
# ============================================================

def _to_ephem_date(d) -> ephem.Date:
    if isinstance(d, ephem.Date):
        return d
    if isinstance(d, datetime):
        return ephem.Date(normalize_datetime(d).astimezone(timezone.utc))
    if isinstance(d, date):
        return _to_ephem_date(datetime.combine(d, datetime.min.time()))
    return ephem.Date(d)


def _to_datetime(d_ephem: ephem.Date) -> datetime:
    return d_ephem.datetime().replace(tzinfo=timezone.utc).astimezone(SHANGHAI)


def _to_date(d: Union[date, datetime]) -> date:
    """Convert to Python date object."""
    if isinstance(d, datetime):
        return normalize_datetime(d).date()
    if isinstance(d, date):
        return d
    return _to_datetime(_to_ephem_date(d)).date()


# ============================================================
# Solar Term Functions
# ============================================================

@lru_cache(maxsize=256)
def find_solar_term_date(year: int, longitude: float) -> ephem.Date:
    """Astronomical term instant, returned as UTC ephem.Date.

    lunar-python's Shou Xing calendar table supplies Beijing civil timestamps.
    Searching two years includes the winter-solstice alias at year end.
    """
    name = next((n for n, lon in SOLAR_TERMS.items() if lon == longitude), None)
    if name is None:
        raise ValueError("longitude must identify one of the 24 solar terms")
    for y in (year, year + 1):
        term = Solar.fromYmd(y, 6, 1).getLunar().getJieQiTable()[name]
        if term.getYear() == year:
            local = datetime.strptime(term.toYmdHms(), "%Y-%m-%d %H:%M:%S")
            # The upstream almanac uses fixed UTC+8, including historical DST years.
            return ephem.Date(local.replace(tzinfo=timezone(timedelta(hours=8))))
    raise ValueError(f"No solar term {name} in {year}")


def get_solar_terms_for_year(year: int) -> List[Dict]:
    """Get all 24 solar terms for a given year.

    Returns a list of dicts with keys:
        - name: 节气 name (e.g. "立春")
        - date: datetime.date when the term occurs
        - longitude: the corresponding solar longitude
    """
    terms = []
    for name in TERM_NAMES:
        longitude = SOLAR_TERMS[name]
        d = find_solar_term_date(year, longitude)
        dt = _to_datetime(d)
        terms.append({
            "name": name,
            "date": dt.date(),
            "longitude": longitude,
        })
    return terms


def get_current_solar_term(d: Union[date, datetime]) -> str:
    year = _to_date(d).year
    terms = []
    for y in (year - 1, year):
        for name, lon in SOLAR_TERMS.items():
            instant = _to_datetime(find_solar_term_date(y, lon))
            key = instant if isinstance(d, datetime) else instant.date()
            terms.append((key, name))
    target = normalize_datetime(d) if isinstance(d, datetime) else d
    return max((key, name) for key, name in terms if key <= target)[1]


def get_ganzhi_year(d: Union[date, datetime]) -> str:
    year = _to_date(d).year
    boundary = _to_datetime(find_solar_term_date(year, SOLAR_TERMS["立春"]))
    target = normalize_datetime(d) if isinstance(d, datetime) else d
    if target < (boundary if isinstance(d, datetime) else boundary.date()):
        year -= 1
    return SIXTY_JIAZI[(year - 4) % 60]


def _get_year_gan_index(year_gan_input: str) -> int:
    """Extract year 天干 index from full ganzhi or single stem."""
    if len(year_gan_input) >= 2 and year_gan_input[0] in TIAN_GAN:
        return TIAN_GAN.index(year_gan_input[0])
    if year_gan_input in TIAN_GAN:
        return TIAN_GAN.index(year_gan_input)
    raise ValueError(f"Invalid year_gan input: {year_gan_input}")


def get_ganzhi_month(d: Union[date, datetime], year_gan: str) -> str:
    year = _to_date(d).year
    target = normalize_datetime(d) if isinstance(d, datetime) else d
    timeline = []
    for y in (year - 1, year):
        for offset, name in enumerate(JIE_TERMS):
            instant = _to_datetime(find_solar_term_date(y, SOLAR_TERMS[name]))
            key = instant if isinstance(d, datetime) else instant.date()
            timeline.append((key, offset))
    _, offset = max(entry for entry in timeline if entry[0] <= target)
    first = (_get_year_gan_index(year_gan) + 1) * 2 % 10
    return TIAN_GAN[(first + offset) % 10] + JIE_ZHI[offset]


def get_ganzhi_day(d: Union[date, datetime]) -> str:
    """Get day ganzhi.

    Base: 2000-01-01 = 戊午日 (index 54). Cycle repeats every 60 days.

    Returns:
        Day ganzhi string (e.g. "甲子").
    """
    d_obj = _to_date(d)
    base = date(2000, 1, 1)
    delta_days = (d_obj - base).days
    idx = (delta_days + 54) % 60
    return SIXTY_JIAZI[idx]


def get_ganzhi_hour(hour: int, day_gan: str) -> str:
    """Get hour ganzhi using 五鼠遁元 (Five Rat Escape).

    五鼠遁元:
        甲己还加甲      -> 甲/己 day -> 甲子 starts
        乙庚丙作初      -> 乙/庚 day -> 丙子 starts
        丙辛从戊起      -> 丙/辛 day -> 戊子 starts
        丁壬庚子居      -> 丁/壬 day -> 庚子 starts
        戊癸何方发，壬子是真途 -> 戊/癸 day -> 壬子 starts

    Formula: first_hour_gan_idx = day_gan_idx * 2 % 10

    Args:
        hour: Hour in 24-hour format (0-23).
        day_gan: Day ganzhi string (e.g. "甲子").

    Returns:
        Hour ganzhi string (e.g. "甲子").
    """
    if not isinstance(hour, int) or not 0 <= hour <= 23:
        raise ValueError("hour must be an integer from 0 to 23")
    hour_zhi_idx = (hour + 1) // 2 % 12

    day_gan_idx = TIAN_GAN.index(day_gan[0])
    first_gan_idx = (day_gan_idx * 2) % 10
    hour_gan_idx = (first_gan_idx + hour_zhi_idx) % 10

    return TIAN_GAN[hour_gan_idx] + DI_ZHI[hour_zhi_idx]


def get_ganzhi_full(d: Union[date, datetime], hour: int) -> Dict[str, str]:
    """Get full 4-pillar ganzhi (四柱八字).

    Args:
        d: Target date.
        hour: Hour in 24-hour format (0-23).

    Returns:
        Dict with keys 'year', 'month', 'day', 'hour'.
    """
    d_obj = _to_date(d)
    year_gz = get_ganzhi_year(d)
    day_gz = get_ganzhi_day(d_obj)
    month_gz = get_ganzhi_month(d, year_gz)
    hour_gz = get_ganzhi_hour(hour, day_gz)

    return {
        "year": year_gz,
        "month": month_gz,
        "day": day_gz,
        "hour": hour_gz,
    }


# ============================================================
# Futou, Xun Shou, Xun Yi
# ============================================================

def get_futou(d: Union[date, datetime]) -> date:
    """Get 符头 (futou) -- nearest 甲/己 day going backwards.

    Returns:
        date object of the 符头 day.
    """
    d_obj = _to_date(d)
    current = d_obj

    for _ in range(60):
        day_gz = get_ganzhi_day(current)
        if day_gz[0] in ("甲", "己"):
            return current
        current -= timedelta(days=1)

    raise ValueError(f"Could not find futou for date {d}")


def get_xun_shou(ganzhi: str) -> str:
    """Get 旬首 (xun shou) -- first 甲 day of current 10-day cycle.

    The 60-day cycle is divided into 6 旬 (10 days each), each starting
    with a 甲-prefix day: 甲子, 甲戌, 甲申, 甲午, 甲辰, 甲寅.

    Args:
        ganzhi: A ganzhi string (e.g. "乙丑").

    Returns:
        Xun shou string (e.g. "甲子").
    """
    idx = GANZHI_INDEX.get(ganzhi)
    if idx is None:
        raise ValueError(f"Invalid ganzhi: {ganzhi}")
    xun_shou_idx = (idx // 10) * 10
    return SIXTY_JIAZI[xun_shou_idx]


def get_xun_yi(xun_shou: str) -> str:
    """Get corresponding 六仪 for a given 旬首.

    六仪:
        甲子旬->戊, 甲戌旬->己, 甲申旬->庚
        甲午旬->辛, 甲辰旬->壬, 甲寅旬->癸
    """
    yi = XUN_YI_MAP.get(xun_shou)
    if yi is None:
        raise ValueError(f"Invalid xun shou: {xun_shou}")
    return yi


# ============================================================
# Yang/Yin Dun and Yuan
# ============================================================

def is_yang_dun(d: Union[date, datetime]) -> bool:
    return get_current_solar_term(d) in YANG_JU_TABLE


def get_yuan_by_futou(futou_date: Union[date, datetime]) -> str:
    """Get 元 (yuan) for a given 符头 (futou) date.

    上元: 子/午/卯/酉
    中元: 寅/申/巳/亥
    下元: 辰/戌/丑/未

    Args:
        futou_date: The 符头 date.

    Returns:
        "上元", "中元", or "下元".
    """
    d_obj = _to_date(futou_date)
    day_gz = get_ganzhi_day(d_obj)
    zhi = day_gz[1]
    return YUAN_INDEX[zhi]
