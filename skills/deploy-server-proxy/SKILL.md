---
name: deploy-server-proxy
description: 把本地 Clash/mihomo 订阅里的节点部署到远程服务器，让服务器自身能科学上网（网络代理访问）。当用户说"给服务器配代理""让服务器能科学上网""部署 clash/mihomo 到服务器""服务器走日本/某地区节点""服务器 IP 与本地一致"时触发。从本地 Clash Verge / mihomo 配置中按地区挑选节点，生成带 fallback 容灾的服务端配置，通过 SSH 部署为常驻 systemd 服务并验证出口 IP。
---

# 部署服务器网络代理 (deploy-server-proxy)

把本地代理订阅中的节点，部署到一台远程服务器上，使**服务器本身**通过这些节点科学上网。
典型用途：国内服务器需要访问被墙资源（google / go.dev / docker hub / github / Anthropic API 等），
通过指定地区（如东京）的节点出网，且出口 IP 区域与本地保持一致。

## 何时用

- 远程服务器在受限网络（如国内），需要稳定访问境外资源
- 需要服务器出口 IP 落在指定地区（与本人所在地一致，保证 IP "干净/趋同"）
- 已有本地 Clash Verge Rev / mihomo 订阅，想复用其中的节点

## 架构

```
远程服务器  ──mihomo(JP-Fallback组)──>  指定地区节点  ──>  境外资源
            127.0.0.1:7890 (http+socks)
            systemd 常驻 / 开机自启 / 崩溃自愈
```

mihomo 内核**支持 `fallback` 代理组**：按顺序健康检查，自动选用第一个可用节点，故障自动切换 —— 实现无感容灾。

## 工作流程

### 1. 确定输入
- **本地订阅文件**：Clash Verge Rev 配置在
  `%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\profiles\<id>.yaml`
  当前激活的 profile id 见同目录 `profiles.yaml` 的 `current:` 字段。
- **目标服务器**：SSH 别名或 `user@host`（需已配好免密登录，否则先配密钥）。
- **地区关键字**：默认按用户所在地选，如东京用 `日本|Tokyo|JP|🇯🇵`。
- 若用户指定了具体节点（按名称或行号），优先用用户指定的。

### 2. 生成服务端配置
用 `scripts/gen_config.py` 从本地 profile 抽取匹配节点，生成 mihomo 服务端配置：

```bash
python scripts/gen_config.py \
  --profile "<本地profile.yaml>" \
  --match "日本|Tokyo|JP" \
  --out /tmp/mihomo-server-config.yaml
```
- `--match` 是正则，匹配节点 `name`。
- `--names "名字1,名字2"` 可替代 `--match`，精确指定节点名。
- 生成的配置：`mixed-port: 7890` 仅监听 `127.0.0.1`；一个 `fallback` 组含所选节点；
  规则里国内镜像域名(aliyun/ivolces/daocloud 等)直连，其余全部走 fallback。

### 3. 部署到服务器
用 `scripts/deploy.sh`（在本地 bash 运行，通过 SSH 操作服务器）：

```bash
bash scripts/deploy.sh <ssh目标> /tmp/mihomo-server-config.yaml
```
它会：安装 mihomo 内核（若缺，经 gh-proxy.com 下载）→ 上传配置到 `/etc/mihomo/config.yaml`
→ 写 systemd 单元（`Restart=always` 开机自启）→ 启动并验证出口 IP。

### 4. 验证区域趋同
对比本地与服务器代理出口：
```bash
curl -s https://api.ip.sb/geoip                                   # 本地
ssh <目标> 'curl -s -x http://127.0.0.1:7890 https://api.ip.sb/geoip'  # 服务器
```
确认两者 `country` / `city` / `asn` 一致（同 ISP、同城市即为趋同）。

### 5. 让服务器其他程序用上代理（可选）
- **shell 全局**：写 `/etc/profile.d/proxy.sh` 导出 `http_proxy/https_proxy/all_proxy`，
  `no_proxy` 加内网与国内镜像域名。
- **Docker 守护进程**：`/etc/systemd/system/docker.service.d/http-proxy.conf` 设
  `HTTP_PROXY=http://127.0.0.1:7890`，`systemctl daemon-reload && systemctl restart docker`。
- **git/go**：`git config --global http.proxy ...`；Go 用 `GOPROXY=https://goproxy.cn,direct`。

## 关键注意

- **代理只监听 127.0.0.1**：不对公网开放，避免成为开放代理被滥用。
- **节点凭据敏感**：生成的配置含 uuid/password，注意权限 `chmod 600`，勿提交到 git。
- **fallback 健康检查 URL** 默认 `https://www.gstatic.com/generate_204`；节点全挂时服务器会失网，
  可通过 `curl http://127.0.0.1:9090/proxies/JP-Fallback` 查当前选中节点排障。
- **国内镜像直连**：apt/docker 国内镜像走直连更快，已在规则里放行；新增镜像域名同样加 `DIRECT` 规则。
- 服务器换地区/换订阅：重跑步骤 2-3 覆盖配置即可。
