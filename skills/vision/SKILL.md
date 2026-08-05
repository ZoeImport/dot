---
name: vision
description: 调用视觉模型把图片转成文字描述，供没有视觉能力的模型使用。当用户给出图片 URL、要求"看看这张图""描述这张截图""这张图里有什么""提取图表/截图里的数据"，而当前模型无法直接看图片时，使用本 skill。
---

# vision

把一张图片（通过 URL）发给视觉模型，返回文字描述，让没有视觉能力的模型也能拿到图像内容。

## 配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `VISION_API_KEY` | 无（必填） | 视觉模型 API key |
| `VISION_API_BASE` | `https://api.openai.com/v1` | 全局 base，OpenAI 或 Anthropic 兼容端点 |
| `VISION_MODEL_BASES` | — | 模型级 base 覆盖，逗号分隔 `model=base`（如 `qwen-vl-max=http://localhost:8000/v1`） |
| `VISION_MODELS` | `gpt-4o-mini` | 逗号分隔的视觉模型列表 |
| `VISION_MODEL` | — | 单个模型名的兼容写法（`VISION_MODELS` 优先） |
| `VISION_API_FORMAT` | 自动判断 | `openai` 或 `anthropic`，见下 |

**两种 API 格式**：工具同时支持 OpenAI 兼容（`/chat/completions`，`Authorization: Bearer`）与 Anthropic 兼容（`/v1/messages`，`x-api-key` + `anthropic-version`）。
- 格式默认**自动判断**：base 含 `anthropic` 则走 Anthropic（如 `https://api.deepseek.com/anthropic`），否则走 OpenAI；也可用 `-api anthropic|openai` / `VISION_API_FORMAT` 显式指定。
- 图片支持 URL，也支持 `data:` URI（本地图片 base64，如 `data:image/jpeg;base64,...`）——Anthropic 格式会解析出 media_type。
- shell 的代理环境变量（`http_proxy`/`https_proxy`）自动生效。

## 配置确认（先询问再调用）

调用前检查配置是否齐全，缺失时**先向用户询问，不要用默认值硬跑**：

| 情况 | 处理 |
|---|---|
| `VISION_API_KEY` 为空 | 询问用户用哪个端点及对应 key。key 由用户自行设置（`VISION_API_KEY=xxx python3 <skill_dir>/scripts/vision.py ...`），不要从别处读取、不要回显、不要写死 |
| `VISION_API_BASE` 仍是默认值，但用户平时走本地网关/中转/代理 | 询问具体 base 地址（如 `http://127.0.0.1:xxxx/v1`） |
| `VISION_MODELS` 未设置 | 询问用户想用哪些视觉模型（可多选，逗号分隔） |

把以上问题一次性问完，例如：「vision 需要确认配置：1) API base 指向哪个 OpenAI 兼容端点？2) 用哪个视觉模型？API key 我会用环境变量设置」。用户回答后，把 base/模型带入本次调用（`-bases` / `-models`），并提示用户自行 export key。

## 调用

```bash
python3 <skill_dir>/scripts/vision.py "https://example.com/img.png"
python3 <skill_dir>/scripts/vision.py -models gpt-4o-mini,qwen-vl-max "https://example.com/img.png"
python3 <skill_dir>/scripts/vision.py -models gpt-4o,qwen-vl-max -bases "gpt-4o=https://api.openai.com/v1,qwen-vl-max=http://localhost:8000/v1" "https://example.com/img.png"
python3 <skill_dir>/scripts/vision.py -prompt "对比这三张截图，列出每张的关键差异" "https://a.png" "https://b.png" "https://c.png"
# Anthropic 兼容端点（base 含 anthropic 自动识别，也可 -api anthropic 显式指定）
VISION_API_BASE=https://api.deepseek.com/anthropic VISION_API_KEY=xxx python3 <skill_dir>/scripts/vision.py -models claude-sonnet "https://example.com/img.png"
# 本地图片用 data: URI
python3 <skill_dir>/scripts/vision.py "data:image/jpeg;base64,$(base64 < img.jpg | tr -d '\n')"
```

参数：
- `-models`：逗号分隔的模型列表（默认读 `VISION_MODELS` 或 `VISION_MODEL`）
- `-bases`：模型级 base 覆盖，逗号分隔 `model=base`（默认读 `VISION_MODEL_BASES`）；未覆盖的模型用全局 `VISION_API_BASE`
- `-api`：`openai` 或 `anthropic`（默认按 base 自动判断，也可用 `VISION_API_FORMAT`）
- `-max-tokens`：最大输出 token，默认 4096
- `-prompt`：描述提示词，默认要求详细描述（文字、布局、颜色、可见数据）
- 位置参数：一个或多个图片 URL 或 `data:` URI（必填），多张图放进同一个请求发给所有模型

输出为每个模型一段文字回复，按 `==> 模型名 <==` 分隔。多模型时各模型并发调用、并列输出，便于交叉对比——某个模型漏掉或说错的内容可被其他模型补全确认。单个模型失败不影响其余模型，全部失败才非零退出。若调用者需要特定信息（数字、文字、结构、颜色），通过 `-prompt` 指定以获取更针对性的描述。

## 目标定位 / 坐标（grounding）

做检测定位、bbox 坐标任务时，提示词要引导模型**先整体后局部、边定位边自证**：

1. **先描述后坐标**：先让模型描述图像风格、整体结构、各元素的分布与相对关系，再基于这个结构输出坐标——坐标要锚定在模型自己的结构化理解上，而不是凭空给框。
2. **风格化图像勿用写实比例质疑**：动漫/插画/海报等风格化图像比例夸张（大眼睛、大头、长腿、透视变形）是正常现象。调用方若无视觉，**禁止**用几何启发式（对称性、相对尺寸、边缘贴合度）去判定坐标对错——这些启发式对风格化图像天然失效，会得出错误结论。
3. **自校验（多问一点）**：对检测结果拿不准时，追加一次视觉复核调用，例如让模型「基于你对整体构图的描述，逐框复核并修正坐标，说明每个框的依据」。让视觉模型自己校验自己，远比无视觉的调用方猜测可靠。
4. **结构化输出**：坐标统一用归一化 0-1000 的 `[x1,y1,x2,y2]`（左上角原点），要求返回纯 JSON（`[{"name":..., "bbox":[...]}]`），便于后续直接消费。
