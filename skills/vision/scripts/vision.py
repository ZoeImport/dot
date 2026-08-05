#!/usr/bin/env python3
"""vision: 调用 OpenAI 兼容视觉模型，把图片 URL 转成文字描述。
支持多张图、多个模型并发、模型级 base 覆盖。纯 stdlib，无第三方依赖。"""
import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DEFAULT_BASE = "https://api.openai.com/v1"


def describe(model, base, key, urls, prompt):
    content = [{"type": "text", "text": prompt}]
    content += [{"type": "image_url", "image_url": {"url": u}} for u in urls]
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": content}]}).encode()
    req = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    if data.get("error"):
        raise RuntimeError(f"API 错误: {data['error'].get('message')}")
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"无输出: {json.dumps(data, ensure_ascii=False)}")


def main():
    p = argparse.ArgumentParser(description="调视觉模型描述图片（纯 stdlib）")
    p.add_argument("urls", nargs="+", help="一个或多个图片 URL")
    p.add_argument("-models", default=os.getenv("VISION_MODELS") or os.getenv("VISION_MODEL") or "gpt-4o-mini",
                   help="逗号分隔的模型列表")
    p.add_argument("-bases", default=os.getenv("VISION_MODEL_BASES") or "",
                   help="模型级 base 覆盖，逗号分隔 model=base")
    p.add_argument("-prompt", default="Describe these images in detail, including all visible text, layout, colors and data.")
    a = p.parse_args()

    key = os.getenv("VISION_API_KEY")
    if not key:
        p.error("需要设置 VISION_API_KEY")
    base_default = os.getenv("VISION_API_BASE") or DEFAULT_BASE
    bases = dict(kv.split("=", 1) for kv in a.bases.split(",") if "=" in kv)
    models = [m.strip() for m in a.models.split(",") if m.strip()] or ["gpt-4o-mini"]

    def run(model):
        try:
            return model, describe(model, bases.get(model, base_default), key, a.urls, a.prompt), None
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
