"""
Calendar core module for Qi Men Dun Jia calculation.

Provides functions for:
- Solar term (节气) calculation using pyephem
- Ganzhi (天干地支) for year, month, day, hour
- Futou (符头), Xun Shou (旬首), Xun Yi (六仪)
- Yang/Yin Dun determination
- Yuan (元) determination
"""

import ephem
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Union


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

def _to_ephem_date(d: Union[date, datetime, str, ephem.Date]) -> ephem.Date:
    """Convert various date types to ephem.Date."""
    if isinstance(d, ephem.Date):
        return d
    if isinstance(d, datetime):
        return ephem.Date(d)
    if isinstance(d, date):
        return ephem.Date(datetime.combine(d, datetime.min.time()))


def _to_datetime(d_ephem: ephem.Date) -> datetime:
    """Convert ephem.Date to Python datetime."""
    return d_ephem.datetime()
    if isinstance(d, str):
        return ephem.Date(d)
    return ephem.Date(d)


def _to_date(d: Union[date, datetime]) -> date:
    """Convert to Python date object."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return _to_datetime(_to_ephem_date(d)).date()


def _sun_longitude_degrees(d: ephem.Date) -> float:
    """Compute the Sun's geocentric ecliptic longitude in degrees (0-360).

    pyephem's sun.hlong returns the Earth's heliocentric longitude in radians.
    Sun's geocentric ecliptic longitude = Earth's heliocentric longitude + 180 deg.
    """
    import math
    sun = ephem.Sun()
    sun.compute(d)
    # float(sun.hlong) gives Earth's heliocentric longitude in radians
    earth_lon_rad = float(sun.hlong)
    # Add pi (180 deg) to get Sun's geocentric ecliptic longitude
    sun_lon_rad = earth_lon_rad + math.pi
    return (sun_lon_rad * 180.0 / math.pi) % 360.0


# ============================================================
# Solar Term Functions
# ============================================================

def find_solar_term_date(year: int, longitude: float) -> ephem.Date:
    """Find the exact date when the Sun reaches a specific ecliptic longitude.

    Uses Newton's method with pyephem for precision.
    The Sun moves ~0.9856 degrees per day, so correction factor ~1.0146 day/deg.

    Args:
        year: The calendar year to search in.
        longitude: Target ecliptic longitude in degrees (0-360).

    Returns:
        ephem.Date of the solar term.
    """
    sun = ephem.Sun()

    # Starting estimate: day-of-year ~ 79 (Mar 20 ~ 春分 0 deg) + (lon/360)*365.25
    # Wrap around for longitudes > ~282 deg
    day_offset = (longitude / 360.0) * 365.25
    start_doy = 79.0 + day_offset
    if start_doy > 365.0:
        start_doy -= 365.25

    d = ephem.Date(f"{year}/1/1") + (start_doy - 1.0)

    # Newton iteration: compute Sun's geocentric ecliptic longitude
    # float(sun.hlong) gives Earth's heliocentric longitude in radians
    # Sun's ecliptic = Earth's heliocentric + 180 deg
    import math
    for _ in range(30):
        sun.compute(d)
        earth_lon_rad = float(sun.hlong)
        sun_lon_deg = ((earth_lon_rad + math.pi) * 180.0 / math.pi) % 360.0
        diff = sun_lon_deg - longitude
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        if abs(diff) < 1e-9:
            break
        d = ephem.Date(d - diff * 365.25 / 360.0)

    return d


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
    """Get the current (most recent) solar term for a given date.

    Returns:
        Solar term name string (e.g. "立春").
    """
    d_obj = _to_date(d)
    year = d_obj.year

    terms_prev = get_solar_terms_for_year(year - 1)
    terms_curr = get_solar_terms_for_year(year)
    all_terms = sorted(terms_prev + terms_curr, key=lambda t: t["date"])

    current = all_terms[0]["name"]
    for term in all_terms:
        if d_obj >= term["date"]:
            current = term["name"]
        else:
            break
    return current


# ============================================================
# Ganzhi Functions
# ============================================================

def get_ganzhi_year(d: Union[date, datetime]) -> str:
    """Get the year ganzhi (e.g. '甲辰', '癸卯').

    Year ganzhi changes at 立春 (~Feb 4), not on Jan 1.
    Base: Gregorian year 4 CE = 甲子 (甲 idx 0, 子 idx 0).
    """
    d_obj = _to_date(d)
    year = d_obj.year

    lichun = find_solar_term_date(year, SOLAR_TERMS["立春"])
    lichun_date = _to_datetime(lichun).date()

    if d_obj < lichun_date:
        eff_year = year - 1
    else:
        eff_year = year

    gan = (eff_year - 4) % 10
    zhi = (eff_year - 4) % 12
    return TIAN_GAN[gan] + DI_ZHI[zhi]


def _get_year_gan_index(year_gan_input: str) -> int:
    """Extract year 天干 index from full ganzhi or single stem."""
    if len(year_gan_input) >= 2 and year_gan_input[0] in TIAN_GAN:
        return TIAN_GAN.index(year_gan_input[0])
    if year_gan_input in TIAN_GAN:
        return TIAN_GAN.index(year_gan_input)
    raise ValueError(f"Invalid year_gan input: {year_gan_input}")


def get_ganzhi_month(d: Union[date, datetime], year_gan: str) -> str:
    """Get month ganzhi using 五虎遁元 (Five Tiger Escape).

    五虎遁元:
        甲己之年丙作首  -> 甲/己 year -> 丙寅 starts
        乙庚之岁戊为头  -> 乙/庚 year -> 戊寅 starts
        丙辛之岁寻庚上  -> 丙/辛 year -> 庚寅 starts
        丁壬壬寅顺水流  -> 丁/壬 year -> 壬寅 starts
        若问戊癸何处起，甲寅之上好追求 -> 戊/癸 year -> 甲寅 starts

    Formula: first_month_gan_idx = (year_gan_idx + 1) * 2 % 10

    Args:
        d: Target date.
        year_gan: Year ganzhi string (e.g. "甲辰" or "甲").

    Returns:
        Month ganzhi string (e.g. "丙寅").
    """
    d_obj = _to_date(d)
    year = d_obj.year
    year_gan_idx = _get_year_gan_index(year_gan)

    prev_xiaohan = find_solar_term_date(year - 1, SOLAR_TERMS["小寒"])
    prev_xiaohan_date = _to_datetime(prev_xiaohan).date()

    jie_dates = []
    for name, lon in zip(JIE_TERMS, JIE_LONGITUDES):
        jd = find_solar_term_date(year, lon)
        jie_dates.append((name, _to_datetime(jd).date()))

    # Timeline: [prev 小寒(丑), 立春(寅), 惊蛰(卯), ..., 小寒(丑)]
    # Each entry: (label, date, zhi, month_offset, use_prev_year_gan)
    timeline: List[Tuple[str, date, str, int, bool]] = [
        ("小寒(prev)", prev_xiaohan_date, "丑", 11, True)
    ]
    for jie_name, jd_date in jie_dates:
        idx = JIE_TERMS.index(jie_name)
        timeline.append((jie_name, jd_date, JIE_ZHI[idx], idx, False))

    for i in range(1, len(timeline)):
        if d_obj < timeline[i][1]:
            prev_entry = timeline[i - 1]
            _, _, zhi, offset, use_prev_year = prev_entry

            if use_prev_year:
                prev_year = year - 1
                eff_year_gan_idx = (prev_year - 4) % 10
            else:
                eff_year_gan_idx = year_gan_idx

            first_gan_idx = (eff_year_gan_idx + 1) * 2 % 10
            month_gan_idx = (first_gan_idx + offset) % 10
            return TIAN_GAN[month_gan_idx] + zhi

    _, _, zhi, offset, _ = timeline[-1]
    first_gan_idx = (year_gan_idx + 1) * 2 % 10
    month_gan_idx = (first_gan_idx + offset) % 10
    return TIAN_GAN[month_gan_idx] + zhi


def get_ganzhi_day(d: Union[date, datetime]) -> str:
    """Get day ganzhi.

    Base: 2000-01-01 = 甲子日. Cycle repeats every 60 days.

    Returns:
        Day ganzhi string (e.g. "甲子").
    """
    d_obj = _to_date(d)
    base = date(2000, 1, 1)
    delta_days = (d_obj - base).days
    idx = delta_days % 60
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
    year_gz = get_ganzhi_year(d_obj)
    day_gz = get_ganzhi_day(d_obj)
    month_gz = get_ganzhi_month(d_obj, year_gz)
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
    """Determine if a date is in 阳遁 (yang dun) period.

    Yang dun: 冬至 -> 夏至 (sun longitude 270 -> 90 deg).
    Yin dun:  夏至 -> 冬至 (sun longitude 90 -> 270 deg).

    Uses the Sun's ecliptic longitude for precise determination:
        yang = longitude in [270, 360) or [0, 90)
        yin  = longitude in [90, 270)

    Returns:
        True if yang dun, False if yin dun.
    """
    d_ephem = _to_ephem_date(d)
    lon = _sun_longitude_degrees(d_ephem)
    return (270.0 <= lon < 360.0) or (0.0 <= lon < 90.0)


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
