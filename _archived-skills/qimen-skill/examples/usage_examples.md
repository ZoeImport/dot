# 可复核日家示例

在 Skill 根目录安装 `requirements.txt` 后运行：

```python
from engine.utils import calculate, format_rija_text, board_to_dict
board = calculate("2026-10-02T08:00:00+08:00", "日家")
print(format_rija_text(board))
assert board.ganzhi == {"year":"丙午", "month":"丁酉", "day":"己酉", "hour":"戊辰"}
assert board.taiyi_gong == 2
```

阴遁，甲辰旬第六日，休门坎一，太乙坤二。

| 方位 / 宫 | 八门 | 九星 |
|---|---|---|
| 北 / 坎1 | 休门 | 摄提 |
| 西南 / 坤2 | 杜门 | 太乙 |
| 东 / 震3 | 惊门 | 天乙 |
| 东南 / 巽4 | 死门 | 太阴 |
| 中5 | — | 咸池 |
| 西北 / 乾6 | 生门 | 青龙 |
| 西 / 兑7 | 伤门 | 天符 |
| 东北 / 艮8 | 开门 | 招摇 |
| 南 / 离9 | 景门 | 轩辕 |

喜神艮东北，贵人子申，截路空亡申酉。申同时有贵人与空亡信号，不能只输出单一吉凶。
卯酉日寅时起青龙，辰时为天刑；这只是日盘附加的时段信息。

```python
# 同一时刻 UTC 输入得到同一盘。
assert board_to_dict(board) == board_to_dict(calculate("2026-10-02T00:00:00+00:00", "日家"))
# 同一天不同小时门星相同。
late = calculate("2026-10-02 23:00", "日家")
assert (board.doors, board.stars) == (late.doors, late.stars)
```

时家调用仍受实验性实现限制：

```python
hour_board = calculate("2026-10-02 08:00", "时家", "拆补法")
data = board_to_dict(hour_board)
assert data["status"] == "experimental"
print(data["markers"])  # 确定性规则证据，不等于权威排盘认证。
print(data["notes"])
```

旧版示例中未经校验的时家盘与断语已移除；实现范围参见 [SKILL.md](../SKILL.md)。
