"""
时家奇门排盘 — 转盘法 (Rotating Board Method)

实现经典的 6 步时家奇门转盘排盘：
1. 布地盘 (六仪三奇)
2. 找值符值使
3. 布天盘 (九星)
4. 布八门
5. 布八神
6. 组装 ShiJiaBoard
"""

import datetime
from typing import Dict, List, Tuple

from .models import (
    ShiJiaBoard,
    GongData,
    STAR_GONG_MAP,
    DOOR_GONG_MAP,
    YANG_STAR_ORDER,
    YIN_STAR_ORDER,
    SHI_JIA_SPIRITS,
)
from .calendar_core import (
    get_ganzhi_full,
    get_xun_shou,
    get_xun_yi,
    DI_ZHI,
)
from .dingju import determine_board

# ============================================================
# Constants
# ============================================================

# 六仪三奇排布顺序
YI_YI_SAN_QI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]

# 八门顺序
DOOR_ORDER = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]

# 八门/八神实际经过的宫位（跳过中五，按洛书顺时针）
GONG_CW = [1, 2, 3, 4, 6, 7, 8, 9]


# ============================================================
# Step 1: 布地盘
# ============================================================

def build_di_pan(ju: int, is_yang: bool) -> List[str]:
    """
    地盘排布：六仪三奇（戊己庚辛壬癸丁丙乙）。

    依据《烟波钓叟赋》：
      "阳遁顺仪奇逆布，阴遁逆仪奇顺行"

    阳遁：从 ju 宫起顺排（宫号递增）
    阴遁：从 ju 宫起逆排（宫号递减）

    Args:
        ju: 局数 (1-9)
        is_yang: True=阳遁, False=阴遁

    Returns:
        长度为 9 的列表，索引 0-8 对应宫 1-9
    """
    grid = [""] * 9
    pos = ju - 1  # 0-indexed
    step = 1 if is_yang else -1
    for i, item in enumerate(YI_YI_SAN_QI):
        actual_pos = (pos + i * step) % 9
        grid[actual_pos] = item
    return grid


# ============================================================
# Step 2: 找值符值使
# ============================================================

def get_zhi_fu_shi(xun_yi: str, di_pan: List[str]) -> Tuple[str, str, int]:
    """
    旬首六仪在地盘所在宫 → 该宫原星 = 值符，原门 = 值使。

    六仪（戊己庚辛壬癸）在地盘上找到其位置，
    所在宫位的原始九星为值符，原始八门为值使。

    Args:
        xun_yi: 旬首对应的六仪（戊/己/庚/辛/壬/癸）
        di_pan: 地盘（9 宫列表）

    Returns:
        (zhi_fu_star, zhi_shi_door, gong_number)
        gong_number 为旬首六仪所在宫号 (1-9)
    """
    gong = di_pan.index(xun_yi)  # 0-indexed
    gong_num = gong + 1

    zhi_fu = STAR_GONG_MAP.get(gong_num, "")

    # 中五宫无原门 → 寄于坤二宫
    door_gong = gong_num if gong_num in DOOR_GONG_MAP else 2
    zhi_shi = DOOR_GONG_MAP.get(door_gong, "")

    return zhi_fu, zhi_shi, gong_num


# ============================================================
# Helper: 星序旋转
# ============================================================

def get_star_order(is_yang: bool, zhi_fu: str) -> List[str]:
    """
    根据阴阳遁获取旋转后的星序（值符星为起点）。

    Args:
        is_yang: True=阳遁(用 YANG_STAR_ORDER), False=阴遁(用 YIN_STAR_ORDER)
        zhi_fu: 值符星名

    Returns:
        旋转后的 9 星列表，zhi_fu 为首
    """
    order = YANG_STAR_ORDER if is_yang else YIN_STAR_ORDER
    idx = order.index(zhi_fu)
    return order[idx:] + order[:idx]


# ============================================================
# Step 3: 布天盘（九星 + 天盘奇仪）
# ============================================================

def build_tian_pan(
    zhi_fu: str,
    zhi_fu_gong: int,
    di_pan: List[str],
    is_yang: bool,
    shi_gan_gong: int,
) -> Tuple[List[str], List[str]]:
    """
    天盘排布：值符星加临时干宫，其余星阳顺阴逆旋转。

    每颗星带其原宫的地盘奇仪到新宫，即天盘奇仪。

    Args:
        zhi_fu: 值符星名
        zhi_fu_gong: 值符星原始宫 (1-9)
        di_pan: 地盘（9 宫列表）
        is_yang: True=阳遁顺转, False=阴遁逆转
        shi_gan_gong: 时干宫 (1-9)，值符星将至此宫

    Returns:
        (tian_pan, stars)
        tian_pan: 天盘奇仪列表（每宫一天干，9 元素）
        stars: 九星列表（每宫一星，9 元素）
    """
    star_order = get_star_order(is_yang, zhi_fu)

    # 星 → 原宫号 (0-indexed) 反向映射
    star_to_gong: Dict[str, int] = {v: k - 1 for k, v in STAR_GONG_MAP.items()}

    tian_pan = [""] * 9
    stars = [""] * 9

    step = 1 if is_yang else -1

    for i in range(9):
        star = star_order[i]
        target = (shi_gan_gong - 1 + i * step) % 9  # 0-indexed

        stars[target] = star

        # 星带其原宫的地盘奇仪到天盘
        orig_gong = star_to_gong.get(star, 0)
        tian_pan[target] = di_pan[orig_gong]

    return tian_pan, stars


# ============================================================
# Step 4: 布八门
# ============================================================

def build_doors(
    zhi_shi: str,
    xun_shou: str,
    hour_gz: str,
    is_yang: bool,
    di_pan: List[str],
) -> Dict[int, str]:
    """
    八门排布：值使门从旬首宫起，按时支偏移运行，阳顺阴逆，跳过中五。

    1. 计算旬首地支 → 时支 偏移步数
    2. 值使门从旬首宫移动 offset 步（跳过中五）
    3. 其余七门按 DOOR_ORDER 顺排

    Args:
        zhi_shi: 值使门名（如 "休门"）
        xun_shou: 旬首（如 "甲子"）
        hour_gz: 时柱（如 "庚午"）
        is_yang: True=阳遁(顺行), False=阴遁(逆行)
        di_pan: 地盘（9 宫列表）

    Returns:
        Dict[宫号, 门名] 共 8 项，无中五
    """
    # 旬首地支 → 时支 偏移
    xun_zhi = xun_shou[1]
    shi_zhi = hour_gz[1]
    xun_zhi_idx = DI_ZHI.index(xun_zhi)
    shi_zhi_idx = DI_ZHI.index(shi_zhi)
    offset = (shi_zhi_idx - xun_zhi_idx) % 12

    # 旬首宫（六仪在地盘位置）
    xun_yi = get_xun_yi(xun_shou)
    xun_gong = di_pan.index(xun_yi) + 1
    if xun_gong == 5:
        xun_gong = 2  # 中五寄坤

    start_idx = GONG_CW.index(xun_gong)

    # 值使门落宫
    if is_yang:
        zhi_shi_gong = GONG_CW[(start_idx + offset) % 8]
    else:
        zhi_shi_gong = GONG_CW[(start_idx - offset) % 8]

    # 从值使门位置起，顺排八门
    zhi_shi_idx = DOOR_ORDER.index(zhi_shi)
    zhi_shi_pos = GONG_CW.index(zhi_shi_gong)

    doors: Dict[int, str] = {}
    for i, door in enumerate(DOOR_ORDER):
        rel = (i - zhi_shi_idx) % 8
        if is_yang:
            gong = GONG_CW[(zhi_shi_pos + rel) % 8]
        else:
            gong = GONG_CW[(zhi_shi_pos - rel) % 8]
        doors[gong] = door

    return doors


# ============================================================
# Step 5: 布八神
# ============================================================

def build_spirits(
    is_yang: bool,
    zhi_fu_star: str,
    stars: List[str],
) -> Dict[int, str]:
    """
    八神排布：小值符随大值符，阳顺阴逆，跳过中五。

    SHI_JIA_SPIRITS 共 8 神，布于 8 个外宫。

    Args:
        is_yang: True=阳遁(顺转), False=阴遁(逆转)
        zhi_fu_star: 值符星名
        stars: 天盘九星列表

    Returns:
        Dict[宫号, 神名] 共 8 项，无中五
    """
    # 大值符所在宫（天盘上）
    zhi_fu_gong = stars.index(zhi_fu_star) + 1
    if zhi_fu_gong == 5:
        zhi_fu_gong = 2  # 中五寄坤

    start_idx = GONG_CW.index(zhi_fu_gong)

    spirits: Dict[int, str] = {}
    step = 1 if is_yang else -1
    for i, spirit in enumerate(SHI_JIA_SPIRITS):
        comp_idx = (start_idx + i * step) % 8
        gong_num = GONG_CW[comp_idx]
        spirits[gong_num] = spirit

    return spirits


# ============================================================
# Main: 时家奇门完整排盘
# ============================================================

def calculate_board_shijia(
    dt: datetime.datetime,
    method: str = "置闰法",
) -> ShiJiaBoard:
    """
    时家奇门完整排盘（转盘法 6 步 → ShiJiaBoard）。

    Steps:
      0. 计算四柱（年/月/日/时 干支）
      1. 定局（阳遁/阴遁 + 局数）
      2. 布地盘（六仪三奇）
      3. 找值符值使
      4. 布天盘（九星旋转 + 天盘奇仪）
      5. 布八门
      6. 布八神
      7. 组装 ShiJiaBoard

    Args:
        dt: 日期时间
        method: 定局方法，可选 "置闰法" / "拆补法" / "茅山法"

    Returns:
        ShiJiaBoard 完整时家奇门排盘结果
    """
    # —— Step 0: 四柱 ——
    ganzhi = get_ganzhi_full(dt.date(), dt.hour)
    hour_gz = ganzhi["hour"]
    shi_gan = hour_gz[0]

    xun_shou = get_xun_shou(hour_gz)
    xun_yi = get_xun_yi(xun_shou)

    # —— Step 1: 定局 ——
    dun_str, desc, mode, yuan = determine_board(dt.date(), method)
    is_yang = dun_str == "阳遁"
    # 从 "阳遁4局" 提取局数
    ju = int(desc.replace("阳遁", "").replace("阴遁", "").replace("局", ""))

    # —— Step 2: 布地盘 ——
    di_pan = build_di_pan(ju, is_yang)

    # —— Step 3: 找值符值使 ——
    zhi_fu, zhi_shi, zhi_fu_gong = get_zhi_fu_shi(xun_yi, di_pan)

    # 时干所在宫
    # 若时干为甲（值符本身，未显于地盘），以旬首六仪位置代之
    try:
        shi_gan_gong = di_pan.index(shi_gan) + 1
    except ValueError:
        # 时干=甲 → 值符不动，以旬首六仪宫为时干宫
        shi_gan_gong = di_pan.index(xun_yi) + 1

    # —— Step 4: 布天盘 ——
    tian_pan, stars = build_tian_pan(
        zhi_fu, zhi_fu_gong, di_pan, is_yang, shi_gan_gong,
    )

    # —— Step 5: 布八门 ——
    doors = build_doors(zhi_shi, xun_shou, hour_gz, is_yang, di_pan)

    # —— Step 6: 布八神 ——
    spirits = build_spirits(is_yang, zhi_fu, stars)

    # —— Assemble ——
    pan: List[GongData] = []
    for i in range(9):
        gong_num = i + 1
        pan.append(GongData(
            gong_index=gong_num,
            di_qi_yi=di_pan[i],
            tian_qi_yi=tian_pan[i] if tian_pan[i] else "",
            star=stars[i] if stars[i] else "",
            door=doors.get(gong_num, ""),
            spirit=spirits.get(gong_num, ""),
        ))

    return ShiJiaBoard(
        input_datetime=dt.isoformat(),
        ganzhi=ganzhi,
        dun=dun_str,
        ju=ju,
        dingju_mode=mode,
        method=method,
        yuan=yuan,
        xun_shou=xun_shou,
        zhi_fu_star=zhi_fu,
        zhi_shi_door=zhi_shi,
        di_pan=di_pan,
        tian_pan=tian_pan,
        stars=stars,
        doors=doors,
        spirits=spirits,
        pan=pan,
        patterns=[],
        notes=[],
    )
