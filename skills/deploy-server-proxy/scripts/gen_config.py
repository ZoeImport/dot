#!/usr/bin/env python3
"""从本地 Clash/mihomo 订阅抽取节点，生成 mihomo 服务端配置（带 fallback 容灾）。

用法:
  python gen_config.py --profile <profile.yaml> --match "日本|Tokyo|JP" --out out.yaml
  python gen_config.py --profile <profile.yaml> --names "节点A,节点B" --out out.yaml
"""
import argparse, re, sys
try:
    # Windows 控制台默认 GBK，节点名含 emoji 会导致 print 崩溃；强制 UTF-8 输出
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    import yaml
except ImportError:
    sys.exit("缺少 PyYAML，请先: pip install pyyaml")


def load_proxies(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    proxies = data.get("proxies") or []
    if not proxies:
        sys.exit(f"在 {path} 里没找到 proxies")
    return proxies


def pick(proxies, match=None, names=None):
    if names:
        want = [n.strip() for n in names.split(",") if n.strip()]
        chosen = [p for p in proxies if p.get("name") in want]
    else:
        rx = re.compile(match, re.I)
        chosen = [p for p in proxies if rx.search(str(p.get("name", "")))]
    # 去重（按 name）
    seen, out = set(), []
    for p in chosen:
        n = p.get("name")
        if n not in seen:
            seen.add(n)
            out.append(p)
    return out


def build(proxies, group="JP-Fallback"):
    names = [p["name"] for p in proxies]
    cfg = {
        "mixed-port": 7890,
        "bind-address": "127.0.0.1",
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "ipv6": False,
        "external-controller": "127.0.0.1:9090",
        "dns": {
            "enable": True,
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "nameserver": ["223.5.5.5", "119.29.29.29"],
        },
        "proxies": proxies,
        "proxy-groups": [{
            "name": group,
            "type": "fallback",
            "url": "https://www.gstatic.com/generate_204",
            "interval": 60,
            "tolerance": 50,
            "proxies": names,
        }],
        "rules": [
            "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
            "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
            "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
            "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
            "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve",
            "DOMAIN-SUFFIX,lan,DIRECT",
            "DOMAIN-SUFFIX,local,DIRECT",
            "DOMAIN-SUFFIX,aliyun.com,DIRECT",
            "DOMAIN-SUFFIX,aliyuncs.com,DIRECT",
            "DOMAIN-SUFFIX,ivolces.com,DIRECT",
            "DOMAIN-SUFFIX,volces.com,DIRECT",
            "DOMAIN-SUFFIX,daocloud.io,DIRECT",
            f"MATCH,{group}",
        ],
    }
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, help="本地 clash/mihomo 订阅 yaml")
    ap.add_argument("--match", help="节点 name 的匹配正则，如 '日本|Tokyo|JP'")
    ap.add_argument("--names", help="精确节点名，逗号分隔")
    ap.add_argument("--group", default="JP-Fallback", help="fallback 组名")
    ap.add_argument("--out", required=True, help="输出的服务端配置路径")
    a = ap.parse_args()
    if not a.match and not a.names:
        sys.exit("需提供 --match 或 --names 之一")

    proxies = load_proxies(a.profile)
    chosen = pick(proxies, a.match, a.names)
    if not chosen:
        sys.exit("没有匹配到任何节点，检查 --match/--names")

    cfg = build(chosen, a.group)
    with open(a.out, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"已写出 {a.out}，包含 {len(chosen)} 个节点:")
    for p in chosen:
        print("  -", p["name"])


if __name__ == "__main__":
    main()
