#!/usr/bin/env python3
"""vision: 调用 OpenAI 兼容或 Anthropic 兼容视觉模型，把图片转成文字描述。
支持多张图、多个模型并发、模型级 base 覆盖、本地图片 data: URI。
纯 stdlib，无第三方依赖。"""
import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DEFAULT_BASE = "https://api.openai.com/v1"
DEFAULT_MAX_TOKENS = 4096


def http_post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def describe_openai(model, base, key, urls, prompt, max_tokens):
    content = [{"type": "text", "text": prompt}]
    content += [{"type": "image_url", "image_url": {"url": u}} for u in urls]
    data = http_post(
        base + "/chat/completions",
        {"model": model, "max_tokens": max_tokens,
         "messages": [{"role": "user", "content": content}]},
        {"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    if data.get("error"):
        raise RuntimeError(f"API 错误: {data['error'].get('message')}")
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"无输出: {json.dumps(data, ensure_ascii=False)}")


def describe_anthropic(model, base, key, urls, prompt, max_tokens):
    content = [{"type": "text", "text": prompt}]
    for u in urls:
        if u.startswith("data:"):
            mime, _, b64 = u[len("data:"):].partition(";base64,")
            content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
        else:
            content.append({"type": "image", "source": {"type": "url", "url": u}})
    data = http_post(
        base + "/v1/messages",
        {"model": model, "max_tokens": max_tokens,
         "messages": [{"role": "user", "content": content}]},
        {"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    if data.get("type") == "error":
        raise RuntimeError(f"API 错误: {data.get('error', {}).get('message')}")
    try:
        return "".join(b["text"] for b in data["content"] if b.get("type") == "text")
    except (KeyError, TypeError):
        raise RuntimeError(f"无输出: {json.dumps(data, ensure_ascii=False)}")


def main():
    p = argparse.ArgumentParser(description="调视觉模型描述图片（纯 stdlib，支持 OpenAI / Anthropic 兼容端点）")
    p.add_argument("urls", nargs="+", help="一个或多个图片 URL（或 data: URI）")
    p.add_argument("-models", default=os.getenv("VISION_MODELS") or os.getenv("VISION_MODEL") or "gpt-4o-mini",
                   help="逗号分隔的模型列表")
    p.add_argument("-bases", default=os.getenv("VISION_MODEL_BASES") or "",
                   help="模型级 base 覆盖，逗号分隔 model=base")
    p.add_argument("-prompt", default="Describe these images in detail, including all visible text, layout, colors and data.")
    p.add_argument("-api", default=os.getenv("VISION_API_FORMAT") or "",
                   help="openai 或 anthropic（默认按 base 含 anthropic 自动判断）")
    p.add_argument("-max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    a = p.parse_args()

    key = os.getenv("VISION_API_KEY")
    if not key:
        p.error("需要设置 VISION_API_KEY")
    base_default = os.getenv("VISION_API_BASE") or DEFAULT_BASE
    api = a.api.lower()
    if api not in ("openai", "anthropic"):
        api = "anthropic" if "anthropic" in base_default.lower() else "openai"
    bases = dict(kv.split("=", 1) for kv in a.bases.split(",") if "=" in kv)
    models = [m.strip() for m in a.models.split(",") if m.strip()] or ["gpt-4o-mini"]

    describe = describe_anthropic if api == "anthropic" else describe_openai

    def run(model):
        try:
            return model, describe(model, bases.get(model, base_default), key, a.urls, a.prompt, a.max_tokens), None
        except Exception as e:
            return model, None, e

    ok = False
    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        for model, text, err in ex.map(run, models):
            if err:
                print(f"[{model}] 失败: {err}", file=sys.stderr)
                continue
            ok = True
            print(f"==> {model} <==\n{text}\n")

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
