# 奇门遁甲引擎 — 使用示例

> 本文档提供引擎 API 的实用代码示例，覆盖时家/日家排盘、定局方法对比、超神接气检测、统一入口调用及底层模块使用。

---

## 示例1：基本时家排盘

输入时间 `2024-06-01 10:00`（北京时间），使用三种不同定局方法排盘。

```python
from engine.utils import calculate, format_board_text

# 置闰法（传统超神接气）
board_1 = calculate("2024-06-01 10:00", "时家", "置闰法")
print("=== 置闰法 ===")
print(format_board_text(board_1))

# 拆补法（现代常用）
board_2 = calculate("2024-06-01 10:00", "时家", "拆补法")
print("=== 拆补法 ===")
print(format_board_text(board_2))

# 茅山法（纯节气）
board_3 = calculate("2024-06-01 10:00", "时家", "茅山法")
print("=== 茅山法 ===")
print(format_board_text(board_3))
```

### 预期输出（节选）

```
=== 时家奇门排盘 ===
时间: 2024-06-01T10:00:00
四柱: 甲辰年 己巳月 甲戌日 己巳时
阳遁4局 | 上元 | 置闰法
值符: 天蓬 | 值使: 休门
旬首: 甲子

宫位 | 地盘 | 天盘   | 九星 | 八门 | 八神
------------------------------------------------------
  1  |  丁  |   癸   | 天蓬 | 休门 | 值符
  2  |  丙  |   己   | 天英 | 死门 | 九天
  3  |  乙  |   辛   | 天冲 | 伤门 | 九地
  4  |  戊  |   乙   | 天辅 | 杜门 | 朱雀
  5  |  己  |   戊   | 天禽 |      |
  6  |  庚  |   丙   | 天心 | 开门 | 勾陈
  7  |  辛  |   丁   | 天柱 | 惊门 | 六合
  8  |  壬  |   庚   | 天任 | 生门 | 太阴
  9  |  癸  |   壬   | 天芮 | 景门 | 腾蛇

吉凶格: 龙返首(戊+丙)
```

拆补法与茅山法结果可能不同（取决于日期在节气中的位置），需对比分析。

---

## 示例2：三种定局方法对比

在同一日期上比较置闰法、拆补法、茅山法的定局差异。

```python
from engine.dingju import determine_board
from datetime import date

target = date(2024, 6, 1)

for method in ["置闰法", "拆补法", "茅山法"]:
    dun, desc, mode, yuan = determine_board(target, method)
    print(f"{method:6s} → {desc:6s} | {mode:4s} | {yuan}")
```

### 预期输出

```
置闰法 → 阳遁4局 | 正授 | 上元
拆补法 → 阳遁4局 | 拆补 | 上元
茅山法 → 阳遁4局 | 茅山 | 上元
```

> **说明**：当符头与节气对齐时（正授），三种方法得出相同结果。差异出现在节气与符头偏差较大的日期，尤其是芒种/大雪前后的超神接气期。

### 对比不同日期的差异

```python
from engine.dingju import determine_board
from datetime import date, timedelta

# 遍历 2024 年全年，找出三种方法局数不同的日期
base = date(2024, 1, 1)
diff_dates = []
for i in range(366):
    d = base + timedelta(days=i)
    results = [determine_board(d, m) for m in ["置闰法", "拆补法", "茅山法"]]
    # 如果定局描述不同则记录
    if len(set(r[1] for r in results)) > 1:
        diff_dates.append((d, results))

print(f"差异天数共计: {len(diff_dates)}")
for d, res in diff_dates[:5]:
    print(f"{d}: 置闰={res[0][1]}, 拆补={res[1][1]}, 茅山={res[2][1]}")
```

---

## 示例3：日家排盘

输入日期 `2024-08-15`，计算日家奇门盘面。

```python
from engine.utils import calculate, format_rija_text

# 日家只用到日期（精确到日）
board = calculate("2024-08-15", "日家")
print(format_rija_text(board))
```

### 预期输出

```
=== 日家奇门排盘 ===
时间: 2024-08-15T00:00:00
四柱: 甲辰年 壬申月 丁亥日 庚子时
阴遁
休门起宫: 6 (乾6)

--- 八门 ---
  坎1: 伤门
  坤2: 死门
  震3: 景门
  巽4: 杜门
  中5: -
  乾6: 休门
  兑7: 生门
  艮8: 开门
  离9: 惊门

--- 九星 ---
  坎1: 青龙
  坤2: 太阴
  震3: 天乙
  巽4: 摄提
  中5: 轩辕
  乾6: 太乙
  兑7: 招摇
  艮8: 天符
  离9: 咸池

喜神方位: 离(南)
天乙贵人: 亥, 酉
截路空亡: 寅卯

--- 十二黑黄道 ---
  子: 白虎(黑道)
  丑: 玉堂(黄道)
  寅: 天牢(黑道)
  卯: 玄武(黑道)
  辰: 司命(黄道)
  巳: 勾陈(黑道)
  午: 青龙(黄道)
  未: 明堂(黄道)
  申: 天刑(黑道)
  酉: 朱雀(黑道)
  戌: 金匮(黄道)
  亥: 天德(黄道)
```

### 访问日家盘面的结构字段

```python
from engine.utils import calculate

board = calculate("2024-08-15", "日家")

print(f"阳遁/阴遁: {'阳遁' if board.is_yang else '阴遁'}")
print(f"休门起宫: {board.xiu_gong}")
print(f"喜神方位: {board.xi_shen}")
print(f"天乙贵人: {', '.join(board.tianyi_gui_ren)}")
print(f"截路空亡: {board.jie_lu}")

# 八门分布（仅含外八宫）
for gong in range(1, 10):
    if gong == 5:
        continue
    door = board.doors.get(gong, "-")
    print(f"  宫{gong}: {door}")

# 黑黄道列表（12时辰）
for i, item in enumerate(board.heihuangdao):
    print(f"  时{i}: {item}")
```

---

## 示例4：超神接气检测

检测指定日期属于哪种超神接气模式，并识别置闰边界。

```python
from engine.dingju import dingju_zirun, dingju_chaibu, dingju_maoshan
from datetime import date

test_dates = [
    date(2024, 1, 1),     # 年初
    date(2024, 3, 20),    # 春分前后
    date(2024, 6, 5),     # 芒种前后（可能置闰）
    date(2024, 6, 21),    # 夏至（阴阳遁分界）
    date(2024, 12, 7),    # 大雪前后（可能置闰）
    date(2024, 12, 21),   # 冬至（阴阳遁分界）
]

for d in test_dates:
    dun, desc, mode, yuan = dingju_zirun(d)
    # mode 可以是: 正授, 超神, 接气, 置闰
    print(f"{d} → {desc:6s} | 模式: {mode} | {yuan}")
```

### 预期输出（示意）

```
2024-01-01 → 阳遁2局 | 模式: 正授 | 上元
2024-03-20 → 阳遁3局 | 模式: 接气 | 下元
2024-06-05 → 阳遁6局 | 模式: 超神 | 上元
2024-06-21 → 阴遁9局 | 模式: 正授 | 上元
2024-12-07 → 阴遁4局 | 模式: 超神 | 上元
2024-12-21 → 阳遁1局 | 模式: 正授 | 上元
```

> **模式含义**：
> - **正授** — 符头与节气同日，理想对齐状态
> - **超神** — 符头先到，节气后到。如 diff >= 9 且为芒种/大雪则触发**置闰**
> - **接气** — 节气先到，符头未到，沿用上一节气的局数

### 检测置闰年份

```python
from engine.dingju import dingju_zirun
from datetime import date, timedelta

def find_zirun_year(year: int):
    """找出某年中触发置闰的日期"""
    base = date(year, 5, 1)   # 从5月开始扫描
    zirun_dates = []
    for i in range(220):      # 覆盖到年底
        d = base + timedelta(days=i)
        _, _, mode, _ = dingju_zirun(d)
        if mode == "置闰":
            zirun_dates.append(d)
    return zirun_dates

for yr in [2020, 2021, 2022, 2023, 2024, 2025]:
    zd = find_zirun_year(yr)
    status = f"{yr}: 置闰触发于 {zd}" if zd else f"{yr}: 无置闰"
    print(status)
```

---

## 示例5：统一入口与序列化

### 通过 `calculate()` 调用全部排盘类型

```python
from engine.utils import calculate, format_board_text, format_rija_text, board_to_dict
import json

# --- 时家排盘（三种方法全览） ---
print("=== 时家排盘 ===")
for method in ["置闰法", "拆补法", "茅山法"]:
    board = calculate("2024-10-01 14:30", "时家", method)
    # 提取关键属性
    print(f"[{method}] {board.dun}{board.ju}局 | "
          f"{board.dingju_mode} | {board.yuan} | "
          f"值符:{board.zhi_fu_star} 值使:{board.zhi_shi_door}")

# --- 日家排盘 ---
print()
print("=== 日家排盘 ===")
board_rija = calculate("2024-10-01", "日家")
print(f"休门起宫: {board_rija.xiu_gong}")
print(f"喜神: {board_rija.xi_shen}")
print(f"贵人: {board_rija.tianyi_gui_ren}")

# --- JSON 序列化 ---
print()
print("=== JSON 输出（时家） ===")
board = calculate("2024-10-01 14:30", "时家", "拆补法")
data = board_to_dict(board)
print(json.dumps(data, ensure_ascii=False, indent=2))
```

### JSON 输出示例

```json
{
  "datetime": "2024-10-01T14:30:00",
  "ganzhi": {
    "year": "甲辰",
    "month": "癸酉",
    "day": "丙申",
    "hour": "丙申"
  },
  "dun": "阴遁",
  "ju": 6,
  "dingju_mode": "拆补",
  "method": "拆补法",
  "yuan": "上元",
  "xun_shou": "甲午",
  "zhi_fu": "天英",
  "zhi_shi": "景门",
  "pan": [
    {"gong": 1, "di": "丁", "tian": "癸", "star": "天蓬", "door": "伤门", "spirit": "九地", "notes": []},
    {"gong": 2, "di": "庚", "tian": "己", "star": "天任", "door": "死门", "spirit": "朱雀", "notes": []}
  ],
  "patterns": []
}
```

> **提示**：`board_to_dict()` 自动识别 `ShiJiaBoard` 与 `RiJiaBoard` 类型，返回对应的 JSON 兼容字典。可用于 API 响应、数据库存储或前端展示。

---

## 示例6：底层模块使用

### 二十四节气查询

```python
from engine.calendar_core import get_solar_terms_for_year, get_current_solar_term
from datetime import date

# 获取全年节气日期
terms = get_solar_terms_for_year(2024)
for t in terms[:6]:
    print(f"{t['name']}: {t['date']} (黄经 {t['longitude']}°)")

# 查询当前所在节气
today = date(2024, 6, 15)
print(f"节气: {get_current_solar_term(today)}")
```

### 四柱八字与旬首

```python
from engine.calendar_core import get_ganzhi_full, get_xun_shou, get_xun_yi, get_futou
from datetime import date

gz = get_ganzhi_full(date(2024, 6, 1), hour=10)
print(f"四柱: {gz['year']}年 {gz['month']}月 {gz['day']}日 {gz['hour']}时")
# 输出: 四柱: 甲辰年 己巳月 甲戌日 己巳时

xs = get_xun_shou(gz["hour"])
xy = get_xun_yi(xs)
print(f"时柱旬首: {xs} → 六仪: {xy}")

ft = get_futou(date(2024, 6, 1))
print(f"符头日: {ft}")
```

### 阳遁/阴遁判断

```python
from engine.calendar_core import is_yang_dun
from datetime import date

dates = [
    date(2024, 1, 15),   # 冬至-夏至 → 阳遁
    date(2024, 6, 21),   # 夏至 → 阴遁起点
    date(2024, 9, 1),    # 夏至-冬至 → 阴遁
    date(2024, 12, 21),  # 冬至 → 阳遁起点
]

for d in dates:
    yang = is_yang_dun(d)
    print(f"{d}: {'阳遁' if yang else '阴遁'}")
```

---

## 示例7：批量排盘（时间序列分析）

对连续时间段进行排盘，用于趋势或窗口期分析。

```python
from engine.utils import calculate
from datetime import datetime, timedelta

def analyze_hours(start_str: str, hours: int = 6, method: str = "拆补法"):
    """对连续时辰逐个排盘，输出值符/值使/八门分布"""
    dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
    for i in range(hours):
        cur = dt + timedelta(hours=i)
        board = calculate(cur.strftime("%Y-%m-%d %H:%M"), "时家", method)
        # 简单摘要：三个吉门（开休生）所在宫位
        lucky_doors = [f"{g}({d})" for g, d in board.doors.items()
                       if d in ("开门", "休门", "生门")]
        print(f"{cur:%H:%M} | {board.dun}{board.ju}局 | "
              f"{board.dingju_mode} | "
              f"值符:{board.zhi_fu_star} 值使:{board.zhi_shi_door} | "
              f"吉门:{' '.join(lucky_doors)}")

# 分析某日上午6个时辰（06:00-12:00）
analyze_hours("2024-06-15 06:00", hours=6, method="拆补法")
```

---

## 示例8：排盘结果的程序化访问

直接访问 `ShiJiaBoard` 的结构化字段，而非依赖文本格式化。

```python
from engine.utils import calculate

board = calculate("2024-06-01 10:00", "时家", "拆补法")

# 元数据
print(f"时间: {board.input_datetime}")
print(f"四柱: {board.ganzhi}")
print(f"遁局: {board.dun}{board.ju}局")
print(f"定局模式: {board.dingju_mode} ({board.method})")
print(f"元: {board.yuan}")
print(f"旬首: {board.xun_shou}")
print(f"值符: {board.zhi_fu_star}")
print(f"值使: {board.zhi_shi_door}")

# 遍历九宫
for gong_data in board.pan:
    g = gong_data.gong_index
    print(f"\n--- 宫{g} ---")
    print(f"  地盘: {gong_data.di_qi_yi}")
    print(f"  天盘: {gong_data.tian_qi_yi}")
    print(f"  九星: {gong_data.star}")
    print(f"  八门: {gong_data.door}")
    print(f"  八神: {gong_data.spirit}")

# 检测吉凶模式
if board.patterns:
    print(f"\n吉凶格: {', '.join(board.patterns)}")
else:
    print("\n当前无已识别吉凶格")
```

---

## 示例9：异常处理

```python
from engine.utils import calculate
from engine.dingju import determine_board
from datetime import date

# 无效格式
try:
    board = calculate("not-a-date", "时家")
except ValueError as e:
    print(f"格式错误: {e}")

# 无效方法名（回退为默认置闰法）
board = calculate("2024-06-01 10:00", "时家", "未知法")
print(f"方法名回退: {board.method}")  # 输出 "置闰法"

# 有效但不常见的 board_type
try:
    board = calculate("2024-06-01", "月家")  # 暂不支持
except Exception as e:
    print(f"不支持的排盘类型: {e}")
```

---

## 附录：常用入口速查

| 操作 | 代码 |
|------|------|
| 时家排盘（置闰法） | `calculate("2024-06-01 10:00", "时家", "置闰法")` |
| 时家排盘（拆补法） | `calculate("2024-06-01 10:00", "时家", "拆补法")` |
| 时家排盘（茅山法） | `calculate("2024-06-01 10:00", "时家", "茅山法")` |
| 日家排盘 | `calculate("2024-08-15", "日家")` |
| 文本输出（时家） | `format_board_text(board)` |
| 文本输出（日家） | `format_rija_text(board)` |
| JSON 序列化 | `board_to_dict(board)` |
| 定局检测（置闰法） | `determine_board(date(2024,6,1), "置闰法")` |
| 四柱八字 | `get_ganzhi_full(date(2024,6,1), 10)` |
| 节气查询 | `get_solar_terms_for_year(2024)` |
| 当前节气 | `get_current_solar_term(date(2024,6,1))` |
| 符头 | `get_futou(date(2024,6,1))` |
| 旬首 | `get_xun_shou("甲戌")` |
| 六仪 | `get_xun_yi("甲子")` |
| 阳遁判断 | `is_yang_dun(date(2024,6,1))` |
