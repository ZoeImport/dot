#!/usr/bin/env bash
set -euo pipefail
set +x
export LC_ALL=C

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
config_dir=${BARK_CONFIG_DIR:-"${HOME}/.config/bark-push"}

if [[ $# -gt 1 || ( $# -eq 1 && "$1" != '--check' ) ]]; then
  printf '%s\n' '用法：send.sh [--check]；发送时从标准输入读取 JSON。' >&2
  exit 2
fi
for dependency in node openssl xxd curl; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    printf '缺少依赖：%s\n' "$dependency" >&2
    exit 1
  fi
done
node "$script_dir/protocol.mjs" check-config "$config_dir"
if [[ ${1:-} == '--check' ]]; then
  printf '%s\n' '本地配置与依赖检查通过；未发送网络请求。'
  exit 0
fi
if [[ -t 0 ]]; then
  printf '%s\n' '请通过标准输入传入 JSON 推送参数。' >&2
  exit 2
fi

json=$(node "$script_dir/protocol.mjs" payload)
device_key=$(cat "$config_dir/device-key")
key=$(cat "$config_dir/encryption-key")
# Match the single optional CRLF accepted by the configuration validator.
device_key=${device_key%$'\r'}
key=${key%$'\r'}
key_hex=$(printf '%s' "$key" | xxd -ps -c 200)
# 12 random bytes encoded as 16 ASCII Base64 characters; the ASCII is the IV.
iv=$(openssl rand -base64 12)
iv_hex=$(printf '%s' "$iv" | xxd -ps -c 200)
ciphertext=$(printf '%s' "$json" | openssl enc -aes-128-cbc -K "$key_hex" -iv "$iv_hex" | openssl base64 -A)
unset key key_hex json

# Keep the device key out of curl's command-line URL and stdout.
if ! response=$(printf 'url = "https://api.day.app/%s"\n' "$device_key" |
  curl --config - --silent --show-error --fail --connect-timeout 10 --max-time 20 \
    --data-urlencode "ciphertext=$ciphertext" --data-urlencode "iv=$iv"); then
  printf '%s\n' '发送请求失败，可能已被服务接收；不要自动重发，请先核对手机。' >&2
  exit 1
fi
printf '%s' "$response" | node "$script_dir/protocol.mjs" response
