---
name: qimen-skill
description: 奇门遁甲 (Qi Men Dun Jia) 排盘计算引擎知识库。用于奇门遁甲运算的相关任务。
---

# 奇门遁甲 (Qi Men Dun Jia) Agent Skill

> A comprehensive knowledge document for AI agents to understand and work with the Qi Men Dun Jia divination system and its calculation engine.

---

## Chapter 1: Total Outline (总纲)

### What is 奇门遁甲?

奇门遁甲 (Qi Men Dun Jia, QMDJ) is one of the "Three Greatest Divination Arts of China" (三式), alongside 太乙神数 and 大六壬. The name breaks down as:

- **三奇 (Three Wonders)**: 乙 (日奇), 丙 (月奇), 丁 (星奇)
- **八门 (Eight Gates)**: 休/生/伤/杜/景/死/惊/开
- **遁甲 (Concealed Jia)**: The celestial stem 甲 is "hidden" (遁) under the Six Yi (六仪: 戊/己/庚/辛/壬/癸)

The core principle: the 九星 (Nine Stars), 八门 (Eight Gates), and 八神 (Eight Spirits) move across a 九宫 (Nine Palace) grid. Their positions and interactions at a specific time reveal the cosmic energetic pattern, guiding decision making.

QMDJ is fundamentally a **spacetime coordinate system** that maps celestial influences onto a terrestrial grid. The primary axis is the 二十四节气 (24 Solar Terms) and the 天干地支 (Heavenly Stems and Earthly Branches).

### 时家 vs 日家 Comparison

| Aspect | 时家 (Hour-Based) | 日家 (Day-Based) |
|--------|-------------------|------------------|
| Time unit | Each 2-hour period (时辰) | Each day |
| 九星 | 天蓬/天芮/天冲/天辅/天禽/天心/天柱/天任/天英 | 太乙/摄提/轩辕/招摇/天符/青龙/咸池/太阴/天乙 |
| 八门 | Determined by 值使 (hourly movement) | Fixed per day, 三日一宫 |
| 值符/值使 | Yes (core mechanism) | No |
| 地盘/天盘 | Yes (two-layer divine plate) | No (single layer) |
| 八神 | 值符/腾蛇/太阴/六合/勾陈/朱雀/九地/九天 | 十二黑黄道 instead |
| 吉凶格 | Yes (elaborate system) | Simplified |
| 定局 | 置闰/拆补/茅山 three methods | Direct by day ganzhi |
| Complexity | High (6-step rotation) | Low-Medium |
| Usage | Major decisions, battles, travel | Daily life, quick reference |

### Calling the Engine

```python
from engine.utils import calculate, format_board_text, format_rija_text

# Hour-based (时家) with specific method
board = calculate("2024-06-01 10:30", "时家", "置闰法")
print(format_board_text(board))

# Day-based (日家)
board = calculate("2024-08-15", "日家")
print(format_rija_text(board))
```

The `calculate()` function is the **single entry point** for all QMDJ calculations. It dispatches to `calculate_board_shijia()` or `calculate_board_rija()` depending on `board_type`. For 时家, the `method` parameter selects the 定局 (board determination) algorithm.

---

## Chapter 2: Foundational Knowledge (基础知识体系)

### 阴阳五行生克 (Yin-Yang and Five Elements)

五行 (Five Elements) with their cycles:

| Element | Direction | Season | Color | Transforming | Conquering |
|---------|-----------|--------|-------|-------------|------------|
| 木 (Wood) | East | Spring | Green/Blue | 木生火 | 木克土 |
| 火 (Fire) | South | Summer | Red | 火生土 | 火克金 |
| 土 (Earth) | Center | Late Summer | Yellow | 土生金 | 土克水 |
| 金 (Metal) | West | Autumn | White | 金生水 | 金克木 |
| 水 (Water) | North | Winter | Black | 水生木 | 水克火 |

Yin-Yang mapping: 奇 (odd numbers) = 阳, 偶 (even numbers) = 阴. This applies to stems, branches, palaces, and all elements in the board.

### 天干地支 (Heavenly Stems and Earthly Branches)

**十天干 (10 Heavenly Stems):**

| Index | Stem | Yin/Yang | Element | Direction |
|-------|------|----------|---------|-----------|
| 0 | 甲 | Yang | 木 | East |
| 1 | 乙 | Yin | 木 | East |
| 2 | 丙 | Yang | 火 | South |
| 3 | 丁 | Yin | 火 | South |
| 4 | 戊 | Yang | 土 | Center |
| 5 | 己 | Yin | 土 | Center |
| 6 | 庚 | Yang | 金 | West |
| 7 | 辛 | Yin | 金 | West |
| 8 | 壬 | Yang | 水 | North |
| 9 | 癸 | Yin | 水 | North |

**The 三奇 (Three Wonders):** 乙/丙/丁 are the 三奇. They are the forces that can overcome the 庚 (Metal) killing energy. 乙 uses softness (marry 庚), 丙 uses fire (burn 庚), 丁 uses brightness (reveal 庚).

**十二地支 (12 Earthly Branches):**

| Index | Branch | Yin/Yang | Element | Direction | Month |
|-------|--------|----------|---------|-----------|-------|
| 0 | 子 | Yang | 水 | North | 11 |
| 1 | 丑 | Yin | 土 | NNE | 12 |
| 2 | 寅 | Yang | 木 | ENE | 1 |
| 3 | 卯 | Yin | 木 | East | 2 |
| 4 | 辰 | Yang | 土 | ESE | 3 |
| 5 | 巳 | Yin | 火 | SSE | 4 |
| 6 | 午 | Yang | 火 | South | 5 |
| 7 | 未 | Yin | 土 | SSW | 6 |
| 8 | 申 | Yang | 金 | WSW | 7 |
| 9 | 酉 | Yin | 金 | West | 8 |
| 10 | 戌 | Yang | 土 | WNW | 9 |
| 11 | 亥 | Yin | 水 | NNW | 10 |

### 六十甲子 (Sexagenary Cycle)

The 10 Heavenly Stems and 12 Earthly Branches combine to form 60 unique pairs (60 = LCM of 10 and 12), called 六十甲子. The cycle repeats every 60 days (and also every 60 years, 60 months).

**The 6 旬 (Ten-Day Cycles):**

Each 旬 starts with a 甲-prefix pair:

| 旬 (Xun) | Start | Contains |
|----------|-------|----------|
| 甲子旬 | 甲子 | 甲子~癸酉 (indices 0-9) |
| 甲戌旬 | 甲戌 | 甲戌~癸未 (indices 10-19) |
| 甲申旬 | 甲申 | 甲申~癸巳 (indices 20-29) |
| 甲午旬 | 甲午 | 甲午~癸卯 (indices 30-39) |
| 甲辰旬 | 甲辰 | 甲辰~癸丑 (indices 40-49) |
| 甲寅旬 | 甲寅 | 甲寅~癸亥 (indices 50-59) |

**六仪 (Six Yi):** Each 旬首 (Xun Shou) has a corresponding "hidden" stem:

| 旬首 | 六仪(所遁) |
|------|-----------|
| 甲子 | 戊 |
| 甲戌 | 己 |
| 甲申 | 庚 |
| 甲午 | 辛 |
| 甲辰 | 壬 |
| 甲寅 | 癸 |

This is the "遁甲" (Concealed Jia) mechanism: the 甲 stem is hidden under the Six Yi. In earth plate placement, we place 戊己庚辛壬癸丁丙乙 (the Six Yi + Three Wonders), not 甲.

### 九宫八卦 (Nine Palaces and Eight Trigrams)

```
     巽4(东南)    离9(南)     坤2(西南)
        巽          离          坤

     震3(东)      中5        兑7(西)
        震          中          兑

     艮8(东北)    坎1(北)     乾6(西北)
        艮          坎          乾
```

Palace numbering follows 洛书 (Luo Shu) magic square: 戴九履一, 左三右七, 二四为肩, 六八为足.

The 中5宫 (Center Palace) has no trigram and no original door. It is "寄于坤" (attached to Kun palace 2) for door placement.

**Eight Trigrams mapping to palaces:**

| Palace | Trigram | Direction | Element |
|--------|---------|-----------|---------|
| 坎1 | 坎(Kan) | North | 水 |
| 坤2 | 坤(Kun) | Southwest | 土 |
| 震3 | 震(Zhen) | East | 木 |
| 巽4 | 巽(Xun) | Southeast | 木 |
| 中5 | - | Center | 土 |
| 乾6 | 乾(Qian) | Northwest | 金 |
| 兑7 | 兑(Dui) | West | 金 |
| 艮8 | 艮(Gen) | Northeast | 土 |
| 离9 | 离(Li) | South | 火 |

### 二十四节气与三元 (24 Solar Terms and Three Yuan)

A solar year (365.25 days) is divided into:

- **24 节气 (Solar Terms)**: 12 节 (Jie) + 12 气 (Qi), each at 15 degrees of solar longitude
- Each 节气 spans approximately 15 days
- Each 15-day period has 3 元 (Yuan): 上元 (5 days) + 中元 (5 days) + 下元 (5 days)
- Total: 24 terms x 3 yuan = 72 hou (pentads)

The 12 **节 (Jie)** are used for month boundary determination: 立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/立冬/大雪/小寒.

**Yuan determination by 符头 (Futou):**

| 符头地支 | Yuan |
|----------|------|
| 子/午/卯/酉 | 上元 |
| 寅/申/巳/亥 | 中元 |
| 辰/戌/丑/未 | 下元 |

### 阳遁 vs 阴遁 (Yang Dun vs Yin Dun)

- **阳遁**: From 冬至 (Winter Solstice, solar longitude 270 deg) to 夏至 (Summer Solstice, solar longitude 90 deg). During this period, the yang energy rises. Placement is **clockwise** (顺飞).
- **阴遁**: From 夏至 (90 deg) to 冬至 (270 deg). During this period, the yin energy rises. Placement is **counter-clockwise** (逆飞).

The formula uses solar ecliptic longitude:
```python
yang = (270.0 <= lon < 360.0) or (0.0 <= lon < 90.0)
yin  = (90.0 <= lon < 270.0)
```

**阳遁局数表 (Yang Dun board number table):**

| 节气 | 上元 | 中元 | 下元 |
|------|------|------|------|
| 冬至 | 1 | 7 | 4 |
| 小寒 | 2 | 8 | 5 |
| 大寒 | 3 | 9 | 6 |
| 立春 | 8 | 5 | 2 |
| 雨水 | 9 | 6 | 3 |
| 惊蛰 | 1 | 7 | 4 |
| 春分 | 3 | 9 | 6 |
| 清明 | 4 | 1 | 7 |
| 谷雨 | 5 | 2 | 8 |
| 立夏 | 4 | 1 | 7 |
| 小满 | 5 | 2 | 8 |
| 芒种 | 6 | 3 | 9 |

**阴遁局数表 (Yin Dun board number table):**

| 节气 | 上元 | 中元 | 下元 |
|------|------|------|------|
| 夏至 | 9 | 3 | 6 |
| 小暑 | 8 | 2 | 5 |
| 大暑 | 7 | 1 | 4 |
| 立秋 | 2 | 5 | 8 |
| 处暑 | 1 | 4 | 7 |
| 白露 | 9 | 3 | 6 |
| 秋分 | 7 | 1 | 4 |
| 寒露 | 6 | 9 | 3 |
| 霜降 | 5 | 8 | 2 |
| 立冬 | 6 | 9 | 3 |
| 小雪 | 5 | 8 | 2 |
| 大雪 | 4 | 7 | 1 |

### Code Example: Getting Foundational Data

```python
from engine.calendar_core import (
    get_ganzhi_full, get_solar_terms_for_year,
    get_futou, get_xun_shou, is_yang_dun,
)

from datetime import datetime, date

# Four-pillar ganzhi (四柱八字)
gz = get_ganzhi_full(date(2024, 6, 1), hour=10)
print(gz)  # {'year': '甲辰', 'month': '己巳', 'day': '甲戌', 'hour': '己巳'}

# Solar terms for a year
terms = get_solar_terms_for_year(2024)
for t in terms[:6]:
    print(f"{t['name']}: {t['date']}")

# Futou (符头)
ft = get_futou(date(2024, 6, 1))
print(f"Futou: {ft}")  # nearest 甲/己 day going backward

# Xun Shou (旬首)
xs = get_xun_shou("甲戌")
print(f"Xun Shou: {xs}")

# Yang/Yin Dun
print(f"Is Yang: {is_yang_dun(date(2024, 6, 1))}")
```

---

## Chapter 3: Core Concept — 超神接气与定局 (KEY CHAPTER)

### Overview

定局 (Board Determination) is the most critical step in QMDJ. It determines:
1. Whether the board is 阳遁 or 阴遁
2. Which 局 number (1-9) to use
3. Which 元 (上/中/下) is active
4. The "mode" (正授/超神/接气/置闰/拆补/茅山)

The challenge: the solar calendar (节气, 15 days) and the lunar-stem calendar (符头, 5-day cycles) do not align perfectly. The exact relationship between them creates the 超神接气 phenomenon.

### 符头 (Futou) — The Key

**Definition**: The 符头 is the nearest 甲/己 day going backward from the target date. Since days with 甲/己 stems mark the start of a 5-day cycle (一候/一元), the 符头 determines which 元 the current date belongs to.

```python
from engine.calendar_core import get_futou
# Futou = nearest 甲 or 己 day going backward
ft = get_futou(date(2024, 6, 1))
```

**Yuan from 符头**: The 地支 of the 符头's day ganzhi determines the 元:

| 符头日干支 | 地支 | 元 |
|-----------|------|-----|
| 甲子, 甲午, 己卯, 己酉 | 子/午/卯/酉 | 上元 |
| 甲寅, 甲申, 己巳, 己亥 | 寅/申/巳/亥 | 中元 |
| 甲辰, 甲戌, 己丑, 己未 | 辰/戌/丑/未 | 下元 |

### 正授 (Zheng Shou) — Perfect Alignment

When the 符头 falls on the exact same day as the solar term start, this is 正授. This is the ideal state.

- **Condition**: `diff = futou_date - term_start_date = 0`
- **Implication**: No adjustment needed. The system is in perfect sync.
- The formula is straightforward: use the current term's board table with the 符头-determined 元.

### 超神 (Chao Shen) — Futou Ahead of Term

The 符头 arrives **before** the solar term.

> From 《烟波钓叟赋》:
> "阴阳二遁分顺逆，一气三元人莫测。
>  五日都来换一元，接气超神为准则"

- **Condition**: `diff > 0` (futou is ahead of term start)
- **Implication**: The cosmic energy (符头) has already shifted to the new cycle, but the seasonal energy (节气) hasn't yet arrived. The new board pattern is "ahead of schedule."
- **Action**: Use the **current term's** board (the term that will start), but with the futou-determined yuan.
- **Boundary rule**: If `diff >= 9` at 芒种 or 大雪, we enter 置闰 (see below).

### 接气 (Jie Qi) — Term Ahead of Futou

The solar term arrives **before** the 符头 catches up.

- **Condition**: `diff < 0` (term start is ahead of futou)
- **Implication**: The seasonal energy has changed, but the 符头 system hasn't yet registered the shift.
- **Action**: Use the **previous term's** board (the term that just ended), since the 符头 is still in the old term's cycle.

### 置闰 (Zhi Run) — Intercalation

When 超神 exceeds 9 days and occurs at **芒种 (Grain in Ear)** or **大雪 (Major Snow)**, an intercalation is inserted — a duplicate of the entire term's cycle.

> From 《奇门遁甲统宗》:
> "置闰之法，在芒种、大雪二节之后，冬至、夏至二至之前"

**Why 芒种 and 大雪?** These are the last terms before 夏至 (Yin Dun begins) and 冬至 (Yang Dun begins). Inserting an intercalation at these boundaries resets the alignment before the major yin/yang transition.

**置闰 mechanism:**

1. 超神 `diff >= 9` at 芒种 or 大雪
2. The current term (芒种/大雪) is repeated: its 上元/中元/下元 cycle is run through again
3. After the intercalation, the 超神 is "consumed" and the system resets to 正授 or near-正授
4. The new half-year (阳遁 or 阴遁) starts cleanly

```python
from engine.dingju import dingju_zirun

# This would trigger 置闰 if conditions are met
dun, desc, mode, yuan = dingju_zirun(date(2024, 6, 5))
print(f"{dun} {desc} ({mode}, {yuan})")
```

### 拆补法 (Chai Bu Fa) — The Simplified Approach

拆补法 avoids the complexity of 超神接气 and 置闰 entirely. It uses a direct rule:

**Rule**: The day's 地支 (from the day ganzhi) directly determines the 元, combined with the current solar term.

```python
from engine.dingju import dingju_chaibu

dun, desc, mode, yuan = dingju_chaibu(date(2024, 6, 1))
print(f"{dun} {desc} ({mode}, {yuan})")
```

This is the most commonly used method in modern practice (popularized by Zhang Zhicheng's 《神奇之门》). It is simpler, deterministic, and does not require tracking intercalations. The trade-off: it can produce slightly different results from traditional 置闰法 in certain boundary periods.

### 茅山法 (Mao Shan Fa) — Pure Solar Term

茅山法 ignores the 符头 entirely. It determines 元 purely by how many days have passed since the solar term started:

| Days since term start | 元 |
|----------------------|-----|
| 0-4 | 上元 |
| 5-9 | 中元 |
| 10+ | 下元 |

```python
from engine.dingju import dingju_maoshan

dun, desc, mode, yuan = dingju_maoshan(date(2024, 6, 1))
print(f"{dun} {desc} ({mode}, {yuan})")
```

This is the simplest method but also the least traditional. It smooths out the discontinuities created by 置闰 at the cost of ignoring the 甲/己 cycle.

### Comparison of Three Methods

| Aspect | 置闰法 | 拆补法 | 茅山法 |
|--------|--------|--------|--------|
| Uses 符头? | Yes | Yes (direct) | No |
| Handles 超神? | Yes (tracking) | No (resolved by direct lookup) | N/A |
| Handles 置闰? | Yes (at芒种/大雪) | No | No |
| 元 determination | via 符头 | via 日支 | via days since term |
| Complexity | High | Low | Lowest |
| Authority | Classical | Modern (张志春) | Pure logic |
| Best for | Traditionalists | Most practitioners | Simplicity seekers |

### Unified Interface

```python
from engine.dingju import determine_board

# All three methods through one function
dun, desc, mode, yuan = determine_board(date(2024, 6, 1), "置闰法")
dun, desc, mode, yuan = determine_board(date(2024, 6, 1), "拆补法")
dun, desc, mode, yuan = determine_board(date(2024, 6, 1), "茅山法")
```

---

## Chapter 4: 时家奇门排盘 — 转盘法六步 (Hour-Based Six-Step Rotation Method)

The 转盘法 (rotating board method) is the classical approach. The board elements rotate around the nine palaces. Each of the 6 steps builds on the previous one.

### Overview of the 6 Steps

1. **布地盘** — Place the Six Yi (六仪) and Three Wonders (三奇) on the earth plate
2. **定值符/值使** — Identify the 值符 (Value Star) and 值使 (Value Door)
3. **布天盘九星** — Rotate the Nine Stars and place the heaven plate
4. **布人盘八门** — Rotate the Eight Gates
5. **布神盘八神** — Place the Eight Spirits
6. **标注** — Add annotations (日干, 时干, 旬空, etc.)

### Step 1: 布地盘 (Earth Plate Placement)

**The Rule:**

From 《烟波钓叟赋》: "阳遁顺仪奇逆布，阴遁逆仪奇顺行"

This means:
- **阳遁**: The Six Yi (戊己庚辛壬癸) are placed clockwise (increasing palace numbers); the Three Wonders (丁丙乙) are placed counter-clockwise
- **阴遁**: The Six Yi are placed counter-clockwise; the Three Wonders are placed clockwise

In practice, the engine uses the simplified formula: arrange the 9 items `[戊, 己, 庚, 辛, 壬, 癸, 丁, 丙, 乙]` starting from the 局数 (board number) palace.

**The Algorithm:**
- `YI_YI_SAN_QI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]`
- Start at palace `ju` (1-indexed), place items in order
- 阳遁: move clockwise (increment palace, mod 9)
- 阴遁: move counter-clockwise (decrement palace, mod 9)

```python
from engine.shijia_board import build_di_pan

# Yang Dun 4: start at palace 4, go clockwise
di_pan_yang4 = build_di_pan(4, is_yang=True)
# e.g. 4:戊, 5:己, 6:庚, 7:辛, 8:壬, 9:癸, 1:丁, 2:丙, 3:乙

# Yin Dun 3: start at palace 3, go counter-clockwise
di_pan_yin3 = build_di_pan(3, is_yang=False)
```

**Example — 阳遁4局:**

| Palace | Earth Plate |
|--------|-------------|
| 坎1 (N) | 丁 |
| 坤2 (SW) | 丙 |
| 震3 (E) | 乙 |
| 巽4 (SE) | 戊 |
| 中5 (Center) | 己 |
| 乾6 (NW) | 庚 |
| 兑7 (W) | 辛 |
| 艮8 (NE) | 壬 |
| 离9 (S) | 癸 |

### Step 2: 定值符/值使 (Determine Value Star and Door)

**The Rule:**

The 旬首 (Xun Shou) of the current hour determines the 六仪 (Yi) that is "active." The palace where this Yi is placed on the earth plate determines:
- **值符 (Zhi Fu)**: The original star of that palace becomes the Value Star
- **值使 (Zhi Shi)**: The original door of that palace becomes the Value Door

**The Algorithm:**

1. Get the hour's 旬首: `xun_shou = get_xun_shou(hour_gz)`
2. Get the corresponding 六仪: `xun_yi = get_xun_yi(xun_shou)` (甲子→戊, 甲戌→己, etc.)
3. Find where `xun_yi` sits on the earth plate: `gong = di_pan.index(xun_yi) + 1`
4. Look up the original star of that palace from `STAR_GONG_MAP`
5. Look up the original door from `DOOR_GONG_MAP` (中5 → 寄坤2)

```python
from engine.shijia_board import get_zhi_fu_shi
from engine.calendar_core import get_xun_shou, get_xun_yi

hour_gz = "己巳"
xun_shou = get_xun_shou(hour_gz)      # "甲子"
xun_yi = get_xun_yi(xun_shou)         # "戊"

# di_pan from step 1
zhi_fu, zhi_shi, gong = get_zhi_fu_shi(xun_yi, di_pan)
print(f"值符: {zhi_fu}, 值使: {zhi_shi}, 宫: {gong}")
```

**Star-to-Palace mapping:**

| Palace | Star | Door |
|--------|------|------|
| 1 (坎) | 天蓬 | 休门 |
| 2 (坤) | 天芮 | 死门 |
| 3 (震) | 天冲 | 伤门 |
| 4 (巽) | 天辅 | 杜门 |
| 5 (中) | 天禽 | (寄坤) |
| 6 (乾) | 天心 | 开门 |
| 7 (兑) | 天柱 | 惊门 |
| 8 (艮) | 天任 | 生门 |
| 9 (离) | 天英 | 景门 |

### Step 3: 布天盘九星 (Heaven Plate — Nine Stars Rotation)

**The Rule:**

The 值符 star is placed on the palace of the hour's stem (时干). The remaining stars follow in order, rotating clockwise for 阳遁 or counter-clockwise for 阴遁. Each star brings its original palace's earth plate stem to the new palace (that stem becomes the 天盘奇仪).

**The Algorithm:**

1. Find the palace where the hour's stem (时干) sits on the earth plate → `shi_gan_gong`
2. If the hour stem is 甲 (the hidden one), use the 旬首六仪's palace instead
3. Place 值符 at `shi_gan_gong`
4. The remaining stars rotate in sequence from there

```python
from engine.shijia_board import build_tian_pan

tian_pan, stars = build_tian_pan(
    zhi_fu="天蓬",   # value star
    zhi_fu_gong=1,    # original palace of value star
    di_pan=di_pan,    # from step 1
    is_yang=True,     # 阳遁
    shi_gan_gong=4,   # hour stem's palace
)
```

**Star rotation orders:**

- **阳遁** (clockwise): 天蓬→天任→天冲→天辅→天英→天芮→天柱→天心→天禽
- **阴遁** (counter-clockwise): 天蓬→天心→天柱→天芮→天英→天辅→天冲→天任→天禽

### Step 4: 布人盘八门 (Human Plate — Eight Gates)

**The Rule:**

The 值使 door starts at the 旬首's palace (where the 六仪 sits on the earth plate). It then moves by the number of steps equal to the offset from the 旬首's 地支 to the hour's 地支. The remaining 7 doors follow in sequence after the 值使's target palace.

**The Algorithm:**

1. `offset = (hour_zhi_index - xun_shou_zhi_index) % 12`
2. The 值使 door starts at `xun_gong` (the palace of the xun yi)
3. 阳遁: move forward `offset` steps (skipping palace 5)
4. 阴遁: move backward `offset` steps (skipping palace 5)
5. After placing 值使, the remaining doors are placed in sequence clockwise

**Palace order (skipping 中5):** `GONG_CW = [1, 2, 3, 4, 6, 7, 8, 9]`

```python
from engine.shijia_board import build_doors

doors = build_doors(
    zhi_shi="休门",      # value door
    xun_shou="甲子",     # xun shou
    hour_gz="己巳",      # hour ganzhi
    is_yang=True,
    di_pan=di_pan,
)
```

### Step 5: 布神盘八神 (Eight Spirits)

**The Rule:**

The "lesser 值符" (小值符, the first spirit) follows the "greater 值符" (大值符, the value star on the heaven plate). The remaining 7 spirits follow in fixed order, clockwise for 阳遁, counter-clockwise for 阴遁.

**八神顺序 (Eight Spirits fixed order):**
`[值符, 腾蛇, 太阴, 六合, 勾陈, 朱雀, 九地, 九天]`

For 阴遁, 勾陈→白虎, 朱雀→玄武 (some traditions swap these).

```python
from engine.shijia_board import build_spirits

spirits = build_spirits(
    is_yang=True,
    zhi_fu_star="天蓬",
    stars=stars,  # from step 3
)
```

### Step 6: 标注 (Annotations)

After the 5-layer board is built, the following annotations are added:

1. **日干 (Day Stem)**: Find which palace the day's stem sits on the heaven plate. This palace is called the "Day Stem Palace."
2. **时干 (Hour Stem)**: Where the hour's stem is on the earth plate (this was already used in Step 3).
3. **旬空 (Xun Kong / Void)**: The two 地支 that are "empty" in the current 旬. For 甲子旬, the void is 戌/亥; for 甲午旬, 辰/巳, etc.
4. **马星 (Ma Xing / Horse Star)**: 寅/午/戌→申, 申/子/辰→寅, 巳/酉/丑→亥, 亥/卯/未→巳.
5. **吉凶格 (Patterns)**: Check for auspicious and inauspicious patterns (see Chapter 5).

### Complete Six-Step Assembly

```python
from engine.shijia_board import calculate_board_shijia
from datetime import datetime

board = calculate_board_shijia(
    dt=datetime(2024, 6, 1, 10, 30),
    method="置闰法",
)

# The board contains everything
print(board.dun)          # "阳遁"
print(board.ju)           # 4
print(board.yuan)         # "上元"
print(board.zhi_fu_star)  # "天蓬"
print(board.zhi_shi_door) # "休门"
print(board.pan[0])       # GongData for palace 1
```

---

## Chapter 5: 时家奇门吉凶格 (Auspicious and Inauspicious Patterns)

### 吉格 (Auspicious Patterns)

**1. 龙返首 (Dragon Returns Head)**
- **Condition**: 天盘甲(戊) 落 地盘丙
- **Meaning**: The dragon turns its head. Great for starting new things, seeking advancement, meeting people.
- **Evaluation**: Extremely auspicious.

**2. 鸟跌穴 (Bird Falls into Nest)**
- **Condition**: 天盘丙 落 地盘甲(戊)
- **Meaning**: The bird returns to its nest. Good for hiding, gathering resources, completing things.
- **Evaluation**: Very auspicious.

**3. 三奇得使 (Three Wonders Find Their Envoy)**
- **Condition**: One of 乙/丙/丁 falls on a palace where its corresponding branch is in the 六仪. Specifically:
  - 乙 + 甲午/己未
  - 丙 + 甲辰/壬戌
  - 丁 + 甲寅/癸丑
- **Meaning**: The Wonder is empowered. Extra beneficial effect.
- **Evaluation**: Auspicious.

**4. 玉女守门 (Jade Maiden Guards the Door)**
- **Condition**: 丁奇(玉女) + 值使门落宫
- **Meaning**: The Jade Maiden (丁) guards the door. Good for romantic matters, social events, banquets.
- **Evaluation**: Auspicious.

**5. 天遁 (Heaven Escape)**
- **Condition**: 丙 + 生门 + 天盘 something
- **Meaning**: Heavenly escape. Good for advancement, promotion.
- **Evaluation**: Auspicious.

**6. 地遁 (Earth Escape)**
- **Condition**: 乙 + 开门 + 地盘 something
- **Meaning**: Earthly escape. Good for construction, burying, establishing.
- **Evaluation**: Auspicious.

**7. 人遁 (Human Escape)**
- **Condition**: 丁 + 休门 + 太阴
- **Meaning**: Human escape. Good for negotiation, interpersonal matters.
- **Evaluation**: Auspicious.

### 凶格 (Inauspicious Patterns)

**1. 龙逃走 (Dragon Escapes)**
- **Condition**: 天盘乙 落 地盘辛 (or 乙 + 辛)
- **Meaning**: The dragon flees. The soft (乙) cannot overcome the strong (辛). Loss, retreat, defeat.
- **Evaluation**: Very inauspicious.

**2. 虎猖狂 (Tiger Runs Wild)**
- **Condition**: 天盘辛 落 地盘乙 (or 辛 + 乙)
- **Meaning**: The tiger goes berserk. Violence, conflict, injury. The strong oppresses the weak.
- **Evaluation**: Very inauspicious.

**3. 蛇夭矫 (Snake Twists)**
- **Condition**: 天盘癸 落 地盘丁 (or 癸 + 丁)
- **Meaning**: The snake writhes in distress. Unexpected obstacles, strange events, deceit.
- **Evaluation**: Inauspicious.

**4. 雀投江 (Sparrow Drops into River)**
- **Condition**: 天盘丁 落 地盘癸 (or 丁 + 癸)
- **Meaning**: The sparrow falls into the river. Letters/messages are lost, communication fails.
- **Evaluation**: Inauspicious.

### 特殊格 (Special Patterns)

**5. 五不遇时 (Five Not Meet Time)**
- **Condition**: The hour's stem conquers the day's stem (五行相克), specifically when the hour stem is 阳干 and conquers the day's 阳干 (or yin conquers yin).
- **Evaluation**: Very inauspicious for important matters. "Five Not Meet, no matters can be accomplished" (五不遇时, 百事不可为).
- **Usage**: Avoid starting any major undertaking during this hour.

**6. 六仪击刑 (Six Yi Attacked)**
- **Condition**: The 六仪 is placed on a palace where its 地支 is "punished" (刑):
  - 戊(甲子) to 震3-卯 → 子卯无礼之刑
  - 己(甲戌) to 坤2-未 → 未戌持势之刑
  - 庚(甲申) to 艮8-寅 → 寅申无恩之刑
  - 辛(甲午) to 离9-午 → 午午自刑
  - 壬(甲辰) to 巽4-辰 → 辰辰自刑
  - 癸(甲寅) to 巽4-巳 → 寅巳无恩之刑
- **Evaluation**: Moderate to severe inauspiciousness, depending on the刑 type.

**7. 三奇入墓 (Three Wonders Enter Tomb)**
- **Condition**: 乙 to 乾6 (木墓在戌), 丙/丁 to 艮8 (火墓在丑)
- **Meaning**: The Wonder is "buried" and cannot function effectively.
- **Evaluation**: Inauspicious. The benefit of the Wonder is neutralized.

**8. 伏吟 (Fu Yin — Static Pattern)**
- **Condition**: The gates/stars/spirits remain in their original palaces (the heaven plate matches the earth plate).
- **Meaning**: Stagnation. Things don't move. Good for collecting, storing, waiting. Bad for action.
- **Evaluation**: Mixed — neutral to mildly inauspicious for action-oriented matters.

**9. 反吟 (Fan Yin — Reversal Pattern)**
- **Condition**: The gates/stars/spirits are placed on the opposite palace from their original.
- **Meaning**: Reversal, upheaval. Things turn upside down. Good for clearing out old things. Bad for stability.
- **Evaluation**: Mixed — can be good for clearing, bad for building.

### 八门吉凶 (Eight Gates Good/Bad)

| Door | Nature | Best Used For | Avoid For |
|------|--------|--------------|-----------|
| 休门 (Rest) | **Great** | Rest, negotiation, marriage | Military action |
| 生门 (Life) | **Great** | Business, wealth, construction | Funerals |
| 伤门 (Hurt) | Bad | Hunting, fishing, catching | Business, travel |
| 杜门 (Block) | Neutral | Hiding, defense, sealing | Open action |
| 景门 (Scenery) | Neutral | Exams, writing, strategies | Major decisions |
| 死门 (Death) | Bad | Funerals, burials, sacrifice | All else |
| 惊门 (Surprise) | Bad | Debates, lawsuits, games | Diplomacy |
| 开门 (Open) | **Great** | Openings, travel, new ventures | Secret matters |

---

## Chapter 6: 日家奇门 (Day-Based Qi Men)

### Core Differences from 时家

The 日家 (Day-based) system is significantly simpler than 时家 (Hour-based):

1. **No 地盘/天盘**: There is only one plate, not two layers of rotation
2. **No 值符/值使**: These concepts do not exist in 日家
3. **Different 九星**: 日家 uses a completely different set of 9 stars
4. **八门 三日一宫**: The gates stay in the same palace for 3 consecutive days
5. **八门 placement is by 日干 (day stem)**, not by 值使 movement
6. **Has 十二黑黄道**: An additional auspiciousness system for the 12 earthly branches
7. **Has 喜神/贵人/截路空亡**: Additional day-specific annotations

### 八门排法 (Eight Gates Placement)

**阳遁起休门歌 (Yang Dun Xiu Men Song):**

This song determines which palace 休门 starts at for any given day's 地支:

```
甲戊壬子坎为休(1),  丁辛乙卯向坤游(2),
庚甲戊午居震位(3),  癸丁辛酉巽方求(4),
庚丙鼠入乾乡去(6),  己癸兔居水泽留(7),
壬丙马行山上路(8),  乙己鸡与火为休(9).
```

This maps certain 四仲日 (子/午/卯/酉 days) to the 休门 palace:

| 日干 | 子日 | 午日 | 卯日 | 酉日 |
|------|------|------|------|------|
| 甲/戊/壬 | 坎1 | 震3 | - | - |
| 丁/辛/乙 | - | - | 坤2 | 巽4 |
| 庚/丙 | 乾6 | 艮8 | - | - |
| 己/癸 | - | - | 兑7 | - |
| 乙/己 | - | - | - | 离9 |

**阴遁歌诀 (Yin Dun Song):**

For 阴遁 (夏至到冬至), the 休门 starts at the **opposite** palace (对冲宫) from the 阳遁 position.

After 休门 is placed, the remaining 7 gates are positioned:
- **阳日** (甲/丙/戊/庚/壬): clockwise (顺飞), skipping 中5
- **阴日** (乙/丁/己/辛/癸): counter-clockwise (逆飞), skipping 中5

### 九星排法 (Nine Stars Placement)

**太乙歌诀 (Tai Yi Song):**

```
甲子为头起艮(8), 甲戌飞入离宫(9),
猿猴翻入水晶宫(1/坎), 甲午坤宫不动(2).
曾见龙生震地(3), 再看虎啸生风(4),
九星殿上显奇功, 太乙临之法用.
```

This gives the starting palace for 太乙 (the first/primary star) based on the 旬首:

| 旬首 | 太乙起宫 |
|------|---------|
| 甲子 | 艮8 |
| 甲戌 | 离9 |
| 甲申 | 坎1 |
| 甲午 | 坤2 |
| 甲辰 | 震3 |
| 甲寅 | 巽4 |

**日家九星 (Day-Based Nine Stars):** 太乙, 摄提, 轩辕, 招摇, 天符, 青龙, 咸池, 太阴, 天乙

The remaining 8 stars follow 太乙 in sequence through the palaces. For 阳遁 the star order follows palace sequence [8,9,1,2,3,4,5,6,7]; for 阴遁 [2,1,9,8,7,6,5,4,3].

### 十二黑黄道 (Twelve Black-Yellow Paths)

These are 12 spirits that govern each of the 12 地支 hours of the day, starting from the day's 地支:

| Index | Name | Type | Auspiciousness |
|-------|------|------|----------------|
| 0 | 青龙 | 黄道 | Great |
| 1 | 明堂 | 黄道 | Great |
| 2 | 天刑 | 黑道 | Bad |
| 3 | 朱雀 | 黑道 | Bad |
| 4 | 金匮 | 黄道 | Great |
| 5 | 天德 | 黄道 | Great |
| 6 | 白虎 | 黑道 | Bad |
| 7 | 玉堂 | 黄道 | Great |
| 8 | 天牢 | 黑道 | Bad |
| 9 | 玄武 | 黑道 | Bad |
| 10 | 司命 | 黄道 | Great |
| 11 | 勾陈 | 黑道 | Bad |

The start index is determined by the day's 地支: 子→0, 丑→1, 寅→2, etc.

### 喜神方位 (Joy Spirit Direction)

| Day Stem | Direction |
|----------|-----------|
| 甲 | 艮(东北) |
| 乙 | 乾(西北) |
| 丙 | 坤(西南) |
| 丁 | 离(南) |
| 戊 | 巽(东南) |
| 己 | 震(东) |
| 庚 | 巽(东南) |
| 辛 | 离(南) |
| 壬 | 兑(西) |
| 癸 | 震(东) |

喜神 indicates the favorable direction for seeking joy (marriage, celebration, social gatherings).

### 天乙贵人 (Heavenly Noble)

| Day Stem | Noble Branches |
|----------|---------------|
| 甲 | 丑, 未 |
| 乙 | 子, 申 |
| 丙 | 亥, 酉 |
| 丁 | 亥, 酉 |
| 戊 | 丑, 未 |
| 己 | 子, 申 |
| 庚 | 丑, 未 |
| 辛 | 寅, 午 |
| 壬 | 卯, 巳 |
| 癸 | 卯, 巳 |

天乙贵人 indicates the direction where help and protection can be found. When in need, move toward the Noble's direction.

### 截路空亡 (Roadblock Void)

| Day Stem | Void Branches |
|----------|---------------|
| 甲, 己 | 申, 酉 |
| 乙, 庚 | 午, 未 |
| 丙, 辛 | 辰, 巳 |
| 丁, 壬 | 寅, 卯 |
| 戊, 癸 | 子, 丑 |

截路空亡 indicates times (in the 2-hour period system) when travel or action is blocked. During these periods, progress is difficult.

### Complete 日家 Calculation

```python
from engine.rija_board import calculate_board_rija
from datetime import datetime

board = calculate_board_rija(datetime(2024, 8, 15, 10, 0))
print(board.xiu_gong)         # 休门 palace number
print(board.doors)            # {palace: door_name}
print(board.stars)            # {palace: star_name}
print(board.xi_shen)          # Joy spirit direction
print(board.tianyi_gui_ren)   # Heavenly noble
print(board.jie_lu)           # Roadblock void
print(board.heihuangdao)      # 12 black-yellow paths
```

---

## Chapter 7: Engine API Reference (排盘引擎调用指南)

### Entry Point: `calculate()`

```python
from engine.utils import calculate

# 时家 (hour-based)
board_shijia = calculate("2024-06-01 10:30", "时家", "置闰法")
board_shijia = calculate("2024-06-01 10:30", "时家", "拆补法")
board_shijia = calculate("2024-06-01 10:30", "时家", "茅山法")

# 日家 (day-based)
board_rija = calculate("2024-08-15", "日家")
```

### Format Output Functions

```python
from engine.utils import format_board_text, format_rija_text

# Pretty-print 时家 board
text = format_board_text(board_shijia)
print(text)

# Pretty-print 日家 board
text = format_rija_text(board_rija)
print(text)

# JSON-serializable dict
from engine.utils import board_to_dict
data = board_to_dict(board_shijia)
import json
print(json.dumps(data, ensure_ascii=False, indent=2))
```

### Module Reference Table

| Module | File | Purpose | Key Functions |
|--------|------|---------|---------------|
| calendar_core | `calendar_core.py` | 干支/节气/符头/旬首/遁甲计算 | `get_ganzhi_full()`, `get_futou()`, `get_xun_shou()`, `is_yang_dun()`, `get_solar_terms_for_year()` |
| dingju | `dingju.py` | 定局引擎(超神接气/拆补/茅山) | `determine_board()`, `dingju_zirun()`, `dingju_chaibu()`, `dingju_maoshan()` |
| shijia_board | `shijia_board.py` | 时家排盘(转盘法六步) | `calculate_board_shijia()`, `build_di_pan()`, `build_tian_pan()`, `build_doors()`, `build_spirits()` |
| rija_board | `rija_board.py` | 日家排盘 | `calculate_board_rija()`, `get_xiu_gong()`, `_place_doors()`, `_place_stars()` |
| models | `models.py` | 数据模型(ShiJiaBoard/RiJiaBoard/GongData) | `ShiJiaBoard`, `RiJiaBoard`, `GongData`, `STAR_GONG_MAP`, `DOOR_GONG_MAP` |
| utils | `utils.py` | 格式化/序列化/统一入口 | `calculate()`, `format_board_text()`, `format_rija_text()`, `board_to_dict()` |

### calendar_core.py Key Functions

```python
# Solar terms
get_solar_terms_for_year(year) -> List[Dict]
  # Returns: [{"name": "立春", "date": date, "longitude": 315}, ...]

get_current_solar_term(d) -> str
  # Returns: current term name (e.g. "立春")

# Ganzhi (stems and branches)
get_ganzhi_full(d, hour) -> Dict[str, str]
  # Returns: {"year": "甲辰", "month": "...", "day": "...", "hour": "..."}

get_ganzhi_year(d) -> str
get_ganzhi_month(d, year_gan) -> str
get_ganzhi_day(d) -> str
get_ganzhi_hour(hour, day_gan) -> str

# Futou and Xun
get_futou(d) -> date
  # Returns: nearest 甲/己 day going backward

get_xun_shou(ganzhi) -> str
  # Returns: xun shou (e.g. "甲子")

get_xun_yi(xun_shou) -> str
  # Returns: the Yi hiding under this xun (戊/己/庚/辛/壬/癸)

is_yang_dun(d) -> bool
  # Returns: True if 阳遁 period (冬至-夏至)
```

### dingju.py Key Functions

```python
determine_board(d, method="置闰法") -> (dun, desc, mode, yuan)
  # dun: "阳遁" or "阴遁"
  # desc: e.g. "阳遁4局"
  # mode: "正授" | "超神" | "接气" | "置闰" | "拆补" | "茅山"
  # yuan: "上元" | "中元" | "下元"

# Direct methods:
dingju_zirun(d)    -> DingjuResult   # 置闰法 (超神接气)
dingju_chaibu(d)   -> DingjuResult   # 拆补法
dingju_maoshan(d)  -> DingjuResult   # 茅山法
```

### shijia_board.py Key Functions

```python
calculate_board_shijia(dt, method="置闰法") -> ShiJiaBoard
  # Complete 6-step hour-based board calculation

# Individual steps (for educational/debug purposes):
build_di_pan(ju, is_yang) -> List[str]       # Step 1: earth plate
get_zhi_fu_shi(xun_yi, di_pan) -> Tuple      # Step 2: value star/door
build_tian_pan(zhi_fu, ...) -> Tuple          # Step 3: heaven plate + stars
build_doors(zhi_shi, ...) -> Dict[int, str]   # Step 4: eight gates
build_spirits(is_yang, ...) -> Dict[int, str] # Step 5: eight spirits
```

### rija_board.py Key Functions

```python
calculate_board_rija(dt) -> RiJiaBoard
  # Complete day-based board calculation

get_xiu_gong(ganzhi) -> int
  # Returns: 休门 palace number (三日一宫)
```

### ShiJiaBoard Data Model

```python
@dataclass
class ShiJiaBoard:
    input_datetime: str        # ISO format
    ganzhi: Dict[str, str]     # {'year': '甲辰', 'month': ..., 'day': ..., 'hour': ...}
    dun: str                   # "阳遁" or "阴遁"
    ju: int                    # Board number (1-9)
    dingju_mode: str           # "正授", "超神", "接气", "置闰", "拆补", or "茅山"
    method: str                # "置闰法", "拆补法", or "茅山法"
    yuan: str                  # "上元", "中元", or "下元"
    xun_shou: str              # e.g. "甲子"
    zhi_fu_star: str           # e.g. "天蓬"
    zhi_shi_door: str          # e.g. "休门"
    di_pan: List[str]          # 9 items (palaces 1-9), earth plate stems
    tian_pan: List[str]        # 9 items, heaven plate stems
    stars: List[str]           # 9 items, star names
    doors: Dict[int, str]      # palace -> door name (8 items)
    spirits: Dict[int, str]    # palace -> spirit name (8 items)
    pan: List[GongData]        # 9 GongData objects (full per-palace data)
    patterns: List[str]        # detected auspicious/inauspicious patterns
    notes: List[str]           # additional annotations

@dataclass
class GongData:
    gong_index: int            # 1-9
    di_qi_yi: str              # earth plate stem
    tian_qi_yi: str            # heaven plate stem
    star: str                  # star in this palace
    door: str                  # gate in this palace
    spirit: str                # spirit in this palace
    notes: List[str]           # pattern annotations for this palace
```

### RiJiaBoard Data Model

```python
@dataclass
class RiJiaBoard:
    input_datetime: str        # ISO format
    ganzhi: Dict[str, str]     # 4-pillar ganzhi
    is_yang: bool              # True=阳遁, False=阴遁
    xiu_gong: int              # 休门 palace (1-9)
    doors: Dict[int, str]      # palace -> door name
    stars: Dict[int, str]      # palace -> star name
    heihuangdao: List[str]     # 12 items (子-亥)
    xi_shen: str               # joy spirit direction
    tianyi_gui_ren: List[str]  # heavenly noble branches
    jie_lu: str                # roadblock void branches
```

### Data Files

| File | Purpose | Format |
|------|---------|--------|
| `data/ganzhi_table.json` | 六十甲子 table with stem/branch indices | JSON |
| `data/rija_params.json` | 日家 parameters lookup | JSON |

---

## Chapter 8: Case Studies and Reasoning (经典案例与推理)

### Analysis Workflow

A complete QMDJ analysis follows these steps:

1. **四柱确立** — Get the 4-pillar ganzhi for the target moment
2. **定局** — Determine 阳遁/阴遁 and 局数
3. **八门评估** — Evaluate the 8 gates (which palace has 开/休/生?)
4. **三奇定位** — Find 乙/丙/丁 on the board (are they in favorable positions?)
5. **奇门相合** — Check if 三奇 and 八门 form auspicious combinations
6. **吉凶格识别** — Scan for auspicious/inauspicious patterns
7. **综合判断** — Synthesize all factors into a recommendation

### Use Case 1: 出行 (Travel)

**Key factors for travel:**
- 开门: Open road, smooth travel
- 休门: Rest stops, peaceful journey
- 生门: Profitable destination
- 乙奇: Route is clear
- 避免: 死门 (blocked), 惊门 (accidents), 杜门 (obstruction)

**Interpretation:** If 开门 falls on the direction of travel and 乙奇 is also in a favorable palace, the journey is auspicious. If 死门 or 惊门 occupies the travel direction, postpone or choose a different route.

### Use Case 2: 求财 (Wealth Seeking)

**Key factors for wealth:**
- 生门: Primary wealth gate (best if with 丙奇 or 戊)
- 戊: The wealth stem itself
- 丙奇: Wealth that grows
- 开+生: Ideal combination for business openings

**Interpretation:** 生门 in a palace with 丙奇 and good 神 (六合/太阴) indicates excellent wealth prospects. 生门 + 死门 (the "life-death" cycle) suggests unstable wealth.

### Use Case 3: 婚姻 (Marriage)

**Key factors for marriage:**
- 乙奇: The bride (soft, yielding)
- 庚: The groom (strong, metal)
- 六合: The matchmaker (relationship)
- 休门: Harmony, rest in relationship

**Interpretation:** 乙 + 庚 in a constructive relationship (乙庚合) is ideal. 六合 as the spirit in the palace where both 乙 and 庚 reside indicates harmonious matchmaking. Avoid 庚 + 乙 in a harming position (虎猖狂).

### Use Case 4: 疾病 (Illness)

**Key factors for health:**
- 天芮: The illness star — its palace indicates the nature of the illness
- 死门: Severity of condition
- 乙奇/丙奇: Healing potential
- 天心: Doctor/healing star

**Interpretation:** The palace of 天芮 reveals the affected area (by trigram/element). If 天心 (physician) overcomes 天芮 (illness), recovery is possible. If 乙奇 or 丙奇 is in the illness palace, medicine will help.

### Complete Walkthrough Example

**Scenario**: A business meeting on 2024-06-01 at 10:30 AM in Beijing.

**Step 1: Calculate the board**

```python
from engine.utils import calculate, format_board_text

board = calculate("2024-06-01 10:30", "时家", "置闰法")
print(format_board_text(board))
```

**Step 2: Examine the 4 pillars (四柱)**

The ganzhi tells us the broader cosmic context. Let's say:
- 年: 甲辰 — Wood Dragon year, 木 energy dominant
- 月: 己巳 — Earth Snake month, 火 grows
- 日: 甲戌 — Wood Dog day
- 时: 己巳 — Earth Snake hour

Interpretation: The strong 木 of the year meets 火 of month/hour. This is a 木生火 cycle — energy flows outward. Good for expansion, promotion, visibility.

**Step 3: Examine the board structure**

Look at the 值符 (Zhi Fu) and 值使 (Zhi Shi):
- 值符 is the "commander" — its star and palace reveal the overall energy
- 值使 is the "executor" — its door and palace reveal the practical outcome

**Step 4: Evaluate gates (八门)**

Check which palaces contain 开/休/生 (the three auspicious gates):
- If 开门 is in the direction of the meeting or in the day/hour stem's palace, the meeting will proceed smoothly
- If 死门 or 惊门 occupies the main palace, obstacles are expected

**Step 5: Locate the Three Wonders (三奇)**

Find 乙/丙/丁 on the heaven plate:
- 乙 + 开/休/生: Excellent for relationship building
- 丙 + 生门: The meeting generates profit
- 丁 + 景门: Good for presentations, visibility

**Step 6: Check patterns (吉凶格)**

Scan for known patterns:
- 龙返首 (戊+丙)? — Extremely auspicious
- 虎猖狂 (辛+乙)? — Conflict, avoid lawsuits
- 五不遇时? — If the hour stem conquers the day stem, postpone
- 三奇入墓 (乙在乾6, 丙/丁在艮8)? — The Wonders are neutralized

**Step 7: Synthesize**

A reasoned judgment:
- If 开门 or 休门 is on the direction of travel AND 三奇 is in a favorable position AND no 凶格 is triggered: **Good timing**, proceed with confidence
- If a 凶格 is present but 开门 is favorable: **Proceed with caution**, have backup plans
- If 五不遇时 OR 死门 in the day/hour palace: **Postpone**, the time energy opposes the action

### Example Output (Complete Board)

```
=== 时家奇门排盘 ===
时间: 2024-06-01T10:30:00
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

### Quick Reference: Analysis Checklist

| Factor | What to Check | Good | Bad |
|--------|---------------|------|-----|
| 值符 | Which star? Which palace? | 天心/天辅 | 天芮/天柱 |
| 开门 Palace | Business direction | Open | Blocked |
| 休门 Palace | Negotiation direction | Restful | Disturbed |
| 生门 Palace | Wealth direction | Growing | Decaying |
| 乙奇 | Relationship energy | Soft | Overcome |
| 丙奇 | Expansion energy | Warm | Burning |
| 丁奇 | Visibility energy | Bright | Hidden |
| 值使 | Execution energy | Smooth | Stuck |
| 旬空 | Void palaces | Empty | Filled |
| 马星 | Movement trigger | Active | Still |
| 时干 Palace | Timing | Strong | Weak |
| 日干 Palace | Self energy | Supported | Attacked |

---

## References

- 《烟波钓叟赋》 — Song dynasty classic, the foundational QMDJ text
- 《奇门遁甲统宗》 — Ming dynasty comprehensive compilation
- 《御定奇门宝鉴》 — Qing dynasty official compilation
- 《神奇之门》(张志春) — Modern authoritative reference, popularized 拆补法
- 《Qimen Dun Jia: The Door to All Wonders》 — English language reference
