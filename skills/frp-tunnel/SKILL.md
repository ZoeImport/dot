---
name: frp-tunnel
description: 内网穿透 —— 在一台有公网 IP 的服务器上用 frp 快捷配置端口映射，把本地（内网）服务暴露到公网。当用户说"内网穿透""把本地端口映射到公网""frp 配置端口""让外网访问我本地的服务""frpc/frps 映射""暴露 3000/8080 端口"等时触发。frps 服务端已部署在公网服务器，本 skill 负责生成/追加 frpc 客户端映射、启动客户端，并提醒放行云安全组。
---

# 内网穿透 frp-tunnel

在一台**有公网 IP 的服务器**（已运行 frps 服务端）下，快捷配置指定端口的网络映射，
把**本地/内网的服务**（如 `127.0.0.1:3000`）暴露到公网 `公网IP:远程端口`。

```
公网用户 ──> 公网服务器:远程端口 ──frps──┐
                                        │ (frp 隧道, 7000)
本地内网服务:本地端口  <──frpc──────────┘
```

## 现成环境（Atlas 服务器）

- **frps 服务端**：已部署在 Atlas = `118.196.34.59`，`bindPort=7000`，控制台 `7500`。
  token 等敏感值见服务器 `/etc/frp/frps.toml`（勿写进 git）。详见记忆 [[atlas-server]]。
- **本地 frpc**：`C:\Users\Administrator\bin\frpc.exe`（v0.61.1，已在 PATH）。
- ⚠️ **云安全组**：火山引擎控制台必须放行 `7000`（隧道）+ 每个**远程端口**，否则公网访问不通。
  这一步只能在云厂商控制台手动做，CLI 改不了 —— 配完务必提醒用户。

## 工作流程

### 1. 收集映射参数
每条映射需要 4 项：
- **名称**：唯一标识，如 `web`、`ssh`。
- **类型**：`tcp`(默认) / `udp` / `http` / `https`。
- **本地** `localIP:localPort`：要暴露的内网服务，通常 `127.0.0.1:<端口>`。
- **远程端口** `remotePort`：公网上访问用的端口。须落在 frps `allowPorts` 放行段内
  （Atlas: 6000-7000 / 8000-9000 / 20000-50000），且已在云安全组放行。

### 2. 生成 frpc 配置
用 `scripts/gen_frpc.py` 生成或追加映射到 `frpc.toml`：

```bash
# 生成新配置（首条映射）
python scripts/gen_frpc.py --out frpc.toml \
  --server 118.196.34.59 --port 7000 --token "<frps_token>" \
  --name web --type tcp --local 127.0.0.1:3000 --remote 8080

# 往已有 frpc.toml 追加一条映射
python scripts/gen_frpc.py --out frpc.toml --append \
  --name ssh --type tcp --local 127.0.0.1:22 --remote 6022
```
token 从服务器读取：`ssh Atlas 'grep auth.token /etc/frp/frps.toml'`，**不要硬编码进 skill/git**。

### 3. 启动 frpc 客户端
本地（Windows bash）：
```bash
frpc.exe -c frpc.toml          # 前台测试
```
常驻运行（关掉终端也不断）：
- 临时后台：`frpc.exe -c frpc.toml &`（或 Bash 工具 run_in_background）。
- 开机自启：用 nssm 注册成 Windows 服务，或放进任务计划程序（开机触发）。

### 4. 验证
```bash
# 看 frpc 日志里 "start proxy success"
# 公网侧实测（换成真实远程端口）：
curl -v http://118.196.34.59:8080
```
连不通时排查顺序：frpc 日志 → frps 控制台 `http://118.196.34.59:7500` → **云安全组是否放行该端口**。

## 关键注意

- **远程端口必须同时满足**：① 在 frps `allowPorts` 段内；② 云安全组放行。漏一个都不通。
- **token 敏感**：每次从服务器现读，别写进 skill / 配置模板 / git。
- **http/https 类型**可用 `customDomains` 走 frps 的 vhost 端口做域名分发；纯端口转发用 `tcp`。
- 反向用途（把服务器服务映射到本地）不是本 skill 场景 —— 那直接 SSH 隧道 `ssh -L` 更简单。
