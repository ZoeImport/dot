"""奇门遁甲排盘引擎 — 工具函数

提供排盘结果的格式化输出（文本/JSON）及统一计算入口。
"""
import datetime
from typing import Dict, Union

from .models import ShiJiaBoard, RiJiaBoard, GONG_NAMES, GONG_POSITION
from .shijia_board import calculate_board_shijia
from .rija_board import calculate_board_rija

# ============================================================
# 十二地支列表（仅供 format_rija_text 使用）
# ============================================================
_DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def format_board_text(board: ShiJiaBoard) -> str:
    """Pretty-print 时家奇门盘面为多行文本。

    Args:
        board: ShiJiaBoard 实例

    Returns:
        格式化的多行排盘文本
    """
    lines = []
    lines.append("=== 时家奇门排盘 ===")
    lines.append(f"时间: {board.input_datetime}")
    lines.append(
        f"四柱: {board.ganzhi['year']}年 "
        f"{board.ganzhi['month']}月 "
        f"{board.ganzhi['day']}日 "
        f"{board.ganzhi['hour']}时"
    )
    lines.append(
        f"{board.dun}{board.ju}局 | {board.dingju_mode} | {board.yuan}"
    )
    lines.append(
        f"值符: {board.zhi_fu_star} | 值使: {board.zhi_shi_door}"
    )
    lines.append(f"旬首: {board.xun_shou}")
    lines.append("")
    lines.append("宫位 | 地盘 | 天盘   | 九星 | 八门 | 八神")
    lines.append("-" * 52)
    for g in board.pan:
        gong_name = GONG_NAMES[g.gong_index - 1]
        lines.append(
            f"  {g.gong_index}  "
            f"| {g.di_qi_yi:>3} "
            f"| {g.tian_qi_yi:>5} "
            f"| {g.star:>4} "
            f"| {g.door:>4} "
            f"| {g.spirit:>4}"
        )
    if board.patterns:
        lines.append(f"")
        lines.append(f"吉凶格: {', '.join(board.patterns)}")
    if board.notes:
        lines.append(f"备注: {'; '.join(board.notes)}")
    return "\n".join(lines)


def format_rija_text(board: RiJiaBoard) -> str:
    """Pretty-print 日家奇门盘面为多行文本。

    包含八门、九星、喜神、贵人、黑黄道的详细显示。

    Args:
        board: RiJiaBoard 实例

    Returns:
        格式化的多行排盘文本
    """
    lines = []
    lines.append("=== 日家奇门排盘 ===")
    lines.append(f"时间: {board.input_datetime}")
    lines.append(
        f"四柱: {board.ganzhi['year']}年 "
        f"{board.ganzhi['month']}月 "
        f"{board.ganzhi['day']}日 "
        f"{board.ganzhi['hour']}时"
    )
    lines.append(f"{'阳遁' if board.is_yang else '阴遁'}")
    gong_name = GONG_NAMES[board.xiu_gong - 1]
    lines.append(f"休门起宫: {board.xiu_gong} ({gong_name})")
    lines.append("")

    # 八门表
    lines.append("--- 八门 ---")
    for gong in range(1, 10):
        door = board.doors.get(gong, "-")
        gn = GONG_NAMES[gong - 1]
        lines.append(f"  {gn}: {door}")

    # 九星表
    lines.append("")
    lines.append("--- 九星 ---")
    for gong in range(1, 10):
        star = board.stars.get(gong, "-")
        gn = GONG_NAMES[gong - 1]
        lines.append(f"  {gn}: {star}")

    # 喜神 / 贵人 / 截路空亡
    lines.append("")
    lines.append(f"喜神方位: {board.xi_shen}")
    lines.append(f"天乙贵人: {', '.join(board.tianyi_gui_ren)}")
    lines.append(f"截路空亡: {board.jie_lu}")

    # 十二黑黄道
    lines.append("")
    lines.append("--- 十二黑黄道 ---")
    for i, item in enumerate(board.heihuangdao):
        dz = _DI_ZHI[i] if i < len(_DI_ZHI) else "?"
        lines.append(f"  {dz}: {item}")

    return "\n".join(lines)


def board_to_dict(board: Union[ShiJiaBoard, RiJiaBoard]) -> dict:
    """将排盘结果序列化为 JSON 兼容的 dict。

    Args:
        board: ShiJiaBoard 或 RiJiaBoard 实例

    Returns:
        包含所有相关数据的 dict（可直接 json.dumps）
    """
    if isinstance(board, ShiJiaBoard):
        return board.to_dict()

    # RiJiaBoard → dict
    return {
        "type": "rija",
        "datetime": board.input_datetime,
        "ganzhi": board.ganzhi,
        "is_yang": board.is_yang,
        "xiu_gong": board.xiu_gong,
        "xiu_gong_name": GONG_NAMES[board.xiu_gong - 1],
        "doors": {str(k): v for k, v in board.doors.items()},
        "stars": {str(k): v for k, v in board.stars.items()},
        "heihuangdao": board.heihuangdao,
        "xi_shen": board.xi_shen,
        "tianyi_gui_ren": board.tianyi_gui_ren,
        "jie_lu": board.jie_lu,
    }


def calculate(
    dt_str: str,
    board_type: str = "时家",
    method: str = "置闰法",
) -> Union[ShiJiaBoard, RiJiaBoard]:
    """统一排盘计算接口。

    根据 board_type 自动分派到时家或日家排盘函数。

    Args:
        dt_str: 日期时间字符串
            "YYYY-MM-DD HH:MM" — 时家排盘（精确到小时）
            "YYYY-MM-DD"       — 日家排盘（仅日期）
        board_type: 排盘类型，可选 "时家" / "日家"
        method: 定局方法（仅时家有效），
            可选 "置闰法" / "拆补法" / "茅山法"

    Returns:
        ShiJiaBoard（时家）或 RiJiaBoard（日家）

    Raises:
        ValueError: 当 dt_str 格式无法解析时抛出
    """
    if " " in dt_str:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    else:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")

    if board_type == "时家":
        return calculate_board_shijia(dt, method)
    else:
        return calculate_board_rija(dt)
