"""
定局引擎 (Dingju Engine) — Board Determination for Qi Men Dun Jia.

This module determines which 遁局 (dun/ju) a given date falls under,
using three different methods:

置闰法 (Chao Shen Jie Qi / 超神接气):
    Traditional method detecting 正授/超神/接气/置闰 by comparing
    符头 (futou) position against solar term start.

拆补法 (Chai Bu Fa):
    Uses the nearest 甲/己 符头 to determine 元 with the current solar term.

茅山法 (Mao Shan Fa):
    Pure solar-term-based; ignores 符头 entirely.
"""

from datetime import date, datetime
from typing import Tuple, Union

from .calendar_core import (
    get_current_solar_term,
    _to_date,
    get_solar_terms_for_year,
    get_futou,
    get_yuan_by_futou,
    YANG_JU_TABLE,
    YIN_JU_TABLE,
)

def _current_term_start(d):
    """Most recent local term date, including the previous December."""
    d = _to_date(d)
    term = get_current_solar_term(d)
    dates = [t["date"] for y in (d.year - 1, d.year)
             for t in get_solar_terms_for_year(y)
             if t["name"] == term and t["date"] <= d]
    return term, max(dates)


# Type alias: (dun, description, mode, yuan)
#   dun:   "阳遁" or "阴遁"
#   desc:  e.g. "阳遁4局"
#   mode:  "正授", "超神", "接气", "置闰", "拆补", or "茅山"
#   yuan:  "上元", "中元", or "下元"
DingjuResult = Tuple[str, str, str, str]

# Map yuan string to index (0/1/2) into YANG_JU_TABLE / YIN_JU_TABLE tuples
_YUAN_TO_IDX = {"上元": 0, "中元": 1, "下元": 2}


def _lookup_ju(term: str, yuan: str) -> Tuple[str, int]:
    """Look up ju number and yin/yang dun type for a term + yuan.
    
    Returns:
        (dun_string, ju_number)
    """
    if term in YANG_JU_TABLE:
        ju = YANG_JU_TABLE[term][_YUAN_TO_IDX[yuan]]
        return "阳遁", ju
    else:
        ju = YIN_JU_TABLE[term][_YUAN_TO_IDX[yuan]]
        return "阴遁", ju


def dingju_zirun(d: Union[date, datetime]) -> DingjuResult:
    """置闰法 (Chao Shen Jie Qi / 超神接气).

    Compares the 符头 (futou) against the current solar term's start date
    to determine the mode:
      - diff == 0  → 正授 (perfect alignment)
      - diff  > 0  → 超神 (futou ahead; if >= 9 at 芒种/大雪 → 置闰)
      - diff <  0  → 接气 (term ahead; use previous term's board)
    
    The futou also determines which 元 (upper/middle/lower) is active.

    Returns:
        (dun, description, mode, yuan)
    """
    d = _to_date(d)
    term, term_start = _current_term_start(d)
    terms_list = get_solar_terms_for_year(d.year)

    futou = get_futou(d)
    diff = (futou - term_start).days  # positive = futou ahead, negative = term ahead

    if diff == 0:
        mode = "正授"  # Perfect alignment
    elif diff > 0:
        # 符头在前 → 超神: futou arrived before the solar term
        if diff >= 9 and term in ("芒种", "大雪"):
            mode = "置闰"  # Intercalation needed at boundary terms
        else:
            mode = "超神"
    else:
        # 节气在前 → 接气: solar term arrived but futou hasn't caught up
        mode = "接气"
        # Use the *previous* term's board data
        term_names = [t["name"] for t in terms_list]
        idx = term_names.index(term)
        term = term_names[(idx - 1) % 24]

    yuan = get_yuan_by_futou(futou)
    dun, ju = _lookup_ju(term, yuan)

    return dun, f"{dun}{ju}局", mode, yuan


def dingju_chaibu(d: Union[date, datetime]) -> DingjuResult:
    """拆补法 (Chai Bu Fa).

    Uses the nearest 甲/己 符头's 地支 to determine yuan:
      - 子/午/卯/酉 → 上元
      - 寅/申/巳/亥 → 中元
      - 辰/戌/丑/未 → 下元
    Combined with the current solar term to look up the ju number.

    Returns:
        (dun, description, mode, yuan)
    """
    term = get_current_solar_term(_to_date(d))
    yuan = get_yuan_by_futou(get_futou(d))

    dun, ju = _lookup_ju(term, yuan)
    return dun, f"{dun}{ju}局", "拆补", yuan


def dingju_maoshan(d: Union[date, datetime]) -> DingjuResult:
    """茅山法 (Mao Shan Fa).

    Pure solar-term-based method that ignores 符头 entirely.
    Yuan is determined by days elapsed since the solar term start:
      -   0-4  days → 上元
      -   5-9  days → 中元
      - 10+    days → 下元

    Returns:
        (dun, description, mode, yuan)
    """
    d = _to_date(d)
    term, term_start = _current_term_start(d)
    days_since = (d - term_start).days
    yuan = "上元" if days_since < 5 else "中元" if days_since < 10 else "下元"

    dun, ju = _lookup_ju(term, yuan)
    return dun, f"{dun}{ju}局", "茅山", yuan


def determine_board(d: Union[date, datetime], method: str = "置闰法") -> DingjuResult:
    """Unified interface for board determination.

    Args:
        d: The date (or datetime) to determine the board for.
        method: One of "置闰法", "拆补法", or "茅山法".
                Defaults to "置闰法".

    Returns:
        (dun, description, mode, yuan)
    """
    method_map = {
        "置闰法": dingju_zirun,
        "拆补法": dingju_chaibu,
        "茅山法": dingju_maoshan,
    }
    if method not in method_map:
        raise ValueError(f"Unsupported dingju method: {method}")
    return method_map[method](d)
