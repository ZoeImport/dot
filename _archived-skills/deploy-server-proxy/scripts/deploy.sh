#!/usr/bin/env bash
# 把 mihomo 服务端配置部署到远程服务器，装内核 + systemd 常驻 + 验证出口 IP。
# 用法: bash deploy.sh <ssh目标> <本地配置文件>
#   例: bash deploy.sh Atlas /tmp/mihomo-server-config.yaml
set -euo pipefail

TARGET="${1:?用法: deploy.sh <ssh目标> <配置文件>}"
CONF="${2:?用法: deploy.sh <ssh目标> <配置文件>}"
GHPROXY="${GHPROXY:-https://gh-proxy.com/}"
SSH="ssh -o BatchMode=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=10"

[ -f "$CONF" ] || { echo "找不到配置文件: $CONF" >&2; exit 1; }

echo "==> [1/4] 安装 mihomo 内核（若缺）"
$SSH "$TARGET" GHPROXY="$GHPROXY" 'bash -s' <<"REMOTE"
set -e
if command -v mihomo >/dev/null 2>&1; then
  echo "mihomo 已安装: $(mihomo -v | head -1)"
else
  cd /tmp
  VER=$(curl -fsSL "${GHPROXY}https://github.com/MetaCubeX/mihomo/releases/latest" -o /dev/null -w "%{redirect_url}" 2>/dev/null | grep -oE "v[0-9.]+$" || true)
  [ -z "$VER" ] && VER="v1.19.16"
  echo "下载 mihomo $VER ..."
  curl -fSL --retry 3 -o mihomo.gz "${GHPROXY}https://github.com/MetaCubeX/mihomo/releases/download/${VER}/mihomo-linux-amd64-${VER}.gz"
  gunzip -f mihomo.gz && install mihomo /usr/local/bin/mihomo && rm -f mihomo
  echo "已安装: $(mihomo -v | head -1)"
fi
mkdir -p /etc/mihomo
REMOTE

echo "==> [2/4] 上传配置到 /etc/mihomo/config.yaml"
scp -o BatchMode=yes "$CONF" "$TARGET:/etc/mihomo/config.yaml"
$SSH "$TARGET" 'chmod 600 /etc/mihomo/config.yaml'

echo "==> [3/4] 写 systemd 单元并启动（常驻/自启/自愈）"
$SSH "$TARGET" 'bash -s' <<"REMOTE"
set -e
cat > /etc/systemd/system/mihomo.service <<EOF
[Unit]
Description=mihomo proxy
After=network.target

[Service]
Type=simple
StartLimitIntervalSec=0
ExecStart=/usr/local/bin/mihomo -d /etc/mihomo
Restart=always
RestartSec=5
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable mihomo >/dev/null 2>&1 || true
systemctl restart mihomo
sleep 4
echo "开机自启: $(systemctl is-enabled mihomo) / 状态: $(systemctl is-active mihomo)"
REMOTE

echo "==> [4/4] 验证出口 IP"
echo "-- 服务器经代理出口:"
$SSH "$TARGET" 'curl -s -m 20 -x http://127.0.0.1:7890 https://api.ip.sb/geoip 2>/dev/null || echo "查询失败，查 journalctl -u mihomo"'
echo
echo "完成。本地对比: curl -s https://api.ip.sb/geoip"
