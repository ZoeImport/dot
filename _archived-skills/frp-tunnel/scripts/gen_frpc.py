#!/usr/bin/env python3
"""生成 / 追加 frpc 客户端端口映射配置（frp >= 0.52 TOML 格式）。

首条映射（含服务端连接信息）:
  python gen_frpc.py --out frpc.toml \
    --server 118.196.34.59 --port 7000 --token "<token>" \
    --name web --type tcp --local 127.0.0.1:3000 --remote 8080

追加映射（复用已有 frpc.toml 的服务端配置，仅加 [[proxies]]）:
  python gen_frpc.py --out frpc.toml --append \
    --name ssh --type tcp --local 127.0.0.1:22 --remote 6022
"""
import argparse, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def split_local(s):
    if ":" not in s:
        sys.exit(f"--local 需为 ip:port，如 127.0.0.1:3000（收到 {s!r}）")
    ip, port = s.rsplit(":", 1)
    if not port.isdigit():
        sys.exit(f"--local 端口非数字: {port!r}")
    return ip or "127.0.0.1", int(port)


def proxy_block(name, ptype, local_ip, local_port, remote_port):
    return (
        "\n[[proxies]]\n"
        f'name = "{name}"\n'
        f'type = "{ptype}"\n'
        f'localIP = "{local_ip}"\n'
        f"localPort = {local_port}\n"
        f"remotePort = {remote_port}\n"
    )


def header(server, port, token):
    h = (
        f'serverAddr = "{server}"\n'
        f"serverPort = {port}\n"
    )
    if token:
        h += f'auth.method = "token"\nauth.token = "{token}"\n'
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="输出 frpc.toml 路径")
    ap.add_argument("--append", action="store_true", help="追加映射到已有文件")
    ap.add_argument("--server", help="frps 公网地址（非 --append 时必填）")
    ap.add_argument("--port", type=int, default=7000, help="frps bindPort，默认 7000")
    ap.add_argument("--token", default="", help="frps auth.token")
    ap.add_argument("--name", required=True, help="映射名称（唯一）")
    ap.add_argument("--type", default="tcp", choices=["tcp", "udp", "http", "https"])
    ap.add_argument("--local", required=True, help="本地服务 ip:port，如 127.0.0.1:3000")
    ap.add_argument("--remote", type=int, required=True, help="公网远程端口")
    a = ap.parse_args()

    local_ip, local_port = split_local(a.local)
    block = proxy_block(a.name, a.type, local_ip, local_port, a.remote)

    if a.append:
        if not os.path.exists(a.out):
            sys.exit(f"--append 但文件不存在: {a.out}")
        with open(a.out, "r", encoding="utf-8") as f:
            if f'name = "{a.name}"' in f.read():
                sys.exit(f"映射名 {a.name!r} 已存在，换个 --name 或先删旧条目")
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(block)
        print(f"已追加映射 [{a.name}] -> {a.server or '(已有服务端)'}:{a.remote}  ->  {a.local}")
    else:
        if not a.server:
            sys.exit("首次生成需 --server 指定 frps 公网地址")
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(header(a.server, a.port, a.token) + block)
        print(f"已写出 {a.out}")
        print(f"映射 [{a.name}] {a.server}:{a.remote}  ->  {a.local}")

    print("下一步: frpc.exe -c", a.out, " 并确认云安全组放行端口", a.remote)


if __name__ == "__main__":
    main()
