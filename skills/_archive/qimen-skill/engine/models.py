"""奇门遁甲排盘数据模型"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

GONG_NAMES = ["坎1", "坤2", "震3", "巽4", "中5", "乾6", "兑7", "艮8", "离9"]
GONG_POSITION = {1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中", 6: "西北", 7: "西", 8: "东北", 9: "南"}

TIAN_GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DI_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

SHI_JIA_STARS = ["天蓬","天任","天冲","天辅","天英","天芮","天柱","天心","天禽"]
SHI_JIA_DOORS = ["休门","生门","伤门","杜门","景门","死门","惊门","开门"]
SHI_JIA_SPIRITS = ["值符","腾蛇","太阴","六合","勾陈","朱雀","九地","九天"]

STAR_GONG_MAP = {1:"天蓬", 2:"天芮", 3:"天冲", 4:"天辅", 5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英"}
DOOR_GONG_MAP = {1:"休门", 8:"生门", 3:"伤门", 4:"杜门", 9:"景门", 2:"死门", 7:"惊门", 6:"开门"}

YANG_STAR_ORDER = ["天蓬","天任","天冲","天辅","天英","天芮","天柱","天心","天禽"]
YIN_STAR_ORDER = ["天蓬","天心","天柱","天芮","天英","天辅","天冲","天任","天禽"]

RI_JIA_STARS = ["太乙","摄提","轩辕","招摇","天符","青龙","咸池","太阴","天乙"]

HEI_HUANG_DAO = [
    ("青龙", "黄道"), ("明堂", "黄道"), ("天刑", "黑道"), ("朱雀", "黑道"),
    ("金匮", "黄道"), ("天德", "黄道"), ("白虎", "黑道"), ("玉堂", "黄道"),
    ("天牢", "黑道"), ("玄武", "黑道"), ("司命", "黄道"), ("勾陈", "黑道"),
]

@dataclass
class GongData:
    gong_index: int
    di_qi_yi: str = ""
    tian_qi_yi: str = ""
    star: str = ""
    door: str = ""
    spirit: str = ""
    notes: List[str] = field(default_factory=list)

@dataclass
class ShiJiaBoard:
    input_datetime: str
    ganzhi: Dict[str, str]
    dun: str
    ju: int
    dingju_mode: str
    method: str
    yuan: str
    xun_shou: str
    zhi_fu_star: str
    zhi_shi_door: str
    di_pan: List[str]
    tian_pan: List[str]
    stars: List[str]
    doors: Dict[int, str]
    spirits: Dict[int, str]
    pan: List[GongData]
    patterns: List[str]
    notes: List[str]

    def to_dict(self) -> dict:
        return {
            "datetime": self.input_datetime,
            "ganzhi": self.ganzhi,
            "dun": self.dun,
            "ju": self.ju,
            "dingju_mode": self.dingju_mode,
            "method": self.method,
            "yuan": self.yuan,
            "xun_shou": self.xun_shou,
            "zhi_fu": self.zhi_fu_star,
            "zhi_shi": self.zhi_shi_door,
            "pan": [{"gong": g.gong_index, "di": g.di_qi_yi,
                     "tian": g.tian_qi_yi, "star": g.star,
                     "door": g.door, "spirit": g.spirit,
                     "notes": g.notes} for g in self.pan],
            "patterns": self.patterns,
        }

@dataclass
class RiJiaBoard:
    input_datetime: str
    ganzhi: Dict[str, str]
    is_yang: bool
    xiu_gong: int
    doors: Dict[int, str]
    stars: Dict[int, str]
    heihuangdao: List[str]
    xi_shen: str
    tianyi_gui_ren: List[str]
    jie_lu: str
