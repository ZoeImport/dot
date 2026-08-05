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
| `VISION_API_BASE` | `https://api.openai.com/v1` | 全局 base，OpenAI 兼容端点（可指向本地网关/代理/中转） |
| `VISION_MODEL_BASES` | — | 模型级 base 覆盖，逗号分隔 `model=base`（如 `qwen-vl-max=http://localhost:8000/v1`） |
| `VISION_MODELS` | `gpt-4o-mini` | 逗号分隔的视觉模型列表 |
| `VISION_MODEL` | — | 单个模型名的兼容写法（`VISION_MODELS` 优先） |

所有 base 都必须是 OpenAI 兼容 `/chat/completions` 端点。shell 的代理环境变量（`http_proxy`/`https_proxy`）自动生效。

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
```

参数：
- `-models`：逗号分隔的模型列表（默认读 `VISION_MODELS` 或 `VISION_MODEL`）
- `-bases`：模型级 base 覆盖，逗号分隔 `model=base`（默认读 `VISION_MODEL_BASES`）；未覆盖的模型用全局 `VISION_API_BASE`
- `-prompt`：描述提示词，默认要求详细描述（文字、布局、颜色、可见数据）
- 位置参数：一个或多个图片 URL（必填），多张图放进同一个请求发给所有模型

输出为每个模型一段文字回复，按 `==> 模型名 <==` 分隔。多模型时各模型并发调用、并列输出，便于交叉对比——某个模型漏掉或说错的内容可被其他模型补全确认。单个模型失败不影响其余模型，全部失败才非零退出。若调用者需要特定信息（数字、文字、结构、颜色），通过 `-prompt` 指定以获取更针对性的描述。
