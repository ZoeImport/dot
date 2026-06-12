---
name: network-domain-debug
description: 排查域名网络问题并优化 Clash/Mihomo 规则的完整流程。当用户遇到域名访问慢、API超时、网络延迟等问题时使用。
---

# Network Domain Debug Skill

排查域名网络问题并优化 Clash/Mihomo 规则的完整流程。

##触发场景

当用户遇到以下情况时使用此 skill：
- "某个域名/API 访问慢"
- "排查域名网络问题"
- "检查接口延迟"
- "优化 Clash/Mihomo 规则"
- "域名解析有问题"
- "接口经常超时报错"

## 排查流程

### Phase 1:信息收集

**必须先获取准确信息：**

1. **询问用户目标域名**
   - 具体域名是什么？（如 `api.example.com`）
   - 是什么用途？（AI API、网站、自建服务等）
   - 用户期望的响应时间？

2. **确认 Clash/Mihomo 配置位置**
```bash
# 查找配置文件
find ~/.config -name "mihomo*.yaml" -o -name "clash*.yaml" 2>/dev/null | head -20
ls -la ~/.config/mihomo-party/ ~/.config/clash/ 2>/dev/null
```

### Phase 2: 网络诊断

**必须按顺序执行以下诊断：**

#### 1. DNS 解析检查

```bash
# 检查是否返回 fake-ip (198.18.x.x 表示被 Clash接管)
nslookup <domain> 2>&1
dig <domain> +short 2>/dev/null
```

**判断标准：**
- 返回 `198.18.x.x` → fake-ip 模式，流量经TUN
- 返回真实IP → 直连或已配置 fake-ip-filter

#### 2. 网络延迟测试

```bash
# 多次测试连接延迟
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "DNS:%{time_namelookup}s Connect:%{time_connect}s TLS:%{time_appconnect}s Total:%{time_total}s\n" \
    --connect-timeout 15 https://<domain> 2>&1
done
```

#### 3. 对比测试（关键）

```bash
# 直接绕过代理 vs经过 Clash
echo "=== 直接连接 (bypass) ==="
curl -s -o /dev/null -w "Total:%{time_total}s\n" --connect-timeout 10 --noproxy '*' https://<domain>

echo "=== 经 Clash (当前) ==="
curl -s -o /dev/null -w "Total:%{time_total}s\n" --connect-timeout 10 https://<domain>
```

**判断标准：**
- 直连明显快 → 需要配置DIRECT规则
- 两者差不多 → 可能不是网络问题，检查服务端

#### 4. Clash 规则检查

```bash
# 查看运行时规则顺序
curl -s --unix-socket <mihomo-socket> 'http://localhost/rules' | python3 -c "
import json,sys
data = json.load(sys.stdin)
rules = data.get('rules', [])
print(f'Total rules: {len(rules)}')
for i, r in enumerate(rules[:50]):
    payload = r.get('payload', '')
    if '<domain关键字>' in payload.lower():
        print(f'[{i}] {r}')
"

# 查找 socket文件
ls /tmp/mihomo-party*.sock /tmp/clash*.sock 2>/dev/null
```

### Phase 3: 问题诊断与方案

**根据诊断结果选择方案：**

#### 场景 A: DNS返回 fake-ip，直连明显更快

**问题：**域名被 Clash fake-ip拦截，路由走代理或不必要的 TUN路径

**解决方案：两步配置**

1. **添加 DIRECT 规则** 到 rules 文件：
```yaml
prepend:
  - DOMAIN-SUFFIX,<domain>,DIRECT
  - DOMAIN,<domain>,DIRECT  # 如果需要精确匹配
```

2. **添加 fake-ip-filter** 到 mihomo.yaml：
```yaml
fake-ip-filter:
  - +.<domain>      # 子域名通配  - +.<parent-domain>  # 父域名通配
```

**配置文件位置：**
- Rules: `~/.config/mihomo-party/rules/*.yaml` 或订阅对应的规则文件
- fake-ip-filter: `~/.config/mihomo-party/mihomo.yaml`

#### 场景 B:DNS 返回真实IP，但延迟仍然高

**问题：**服务端响应慢或网络波动大

**解决方案：**
- 检查服务端是否在海外（可能需要加速）
- 检查 WiFi/网络稳定性
- 检查是不是API 本身处理慢（AI推理等）

#### 场景 C: 规则已存在但未生效

**问题：** Mihomo未重新加载配置

**解决方案：**
- 在 Mihomo Party GUI 中"重载配置"
- 或重启 Mihomo内核

### Phase 4:配置修改

**修改原则：**

1. **先读取现有配置**
```bash
cat <config-file> | grep -A 20 "fake-ip-filter:"
cat <rules-file> | head -30
```

2. **使用Edit工具精确修改**
   - 不要覆盖整个文件
   - 只修改需要的那几行

3. **格式规范**
```yaml
# Rules文件格式
prepend:
  - DOMAIN-SUFFIX,example.com,DIRECT
  - DOMAIN-KEYWORD,keyword,DIRECTappend: []
delete: []

# fake-ip-filter 格式（注意缩进）
fake-ip-filter:
  - +.lan- +.example.com    # 新添加的
```

### Phase 5: 验证生效

**必须执行验证：**

```bash
# 1. 检查 DNS 是否变成真实IP
nslookup <domain> | grep Address

# 2. 再次测试延迟
for i in 1 2 3; do
  curl -s -o /dev/null -w "Total:%{time_total}s\n" --connect-timeout 10 https://<domain>
done

# 3. 检查规则顺序
curl -s --unix-socket <socket> 'http://localhost/rules' | python3 -c "..."
```

**成功标准：**
- DNS返回真实IP（不是198.18.x.x）
- 延迟稳定且与直连相近
- 规则在列表前几项

## 输出格式要求

**诊断报告必须包含：**

```markdown
## 📊 域名网络诊断报告

### 基本信息
-域名：<domain>
- 当前DNS解析：<ip-address>
- 解析类型：fake-ip /真实IP

### 延迟测试结果
| 测试 | DNS | Connect | TLS | Total |
|------|------|---------|-----|-------|
| 1| xxx | xxx | xxx | xxx |
...

### 对比测试
| 方式 | 延迟 |
|------|------|
| 直连 (bypass) | xxx |
| 经 Clash | xxx |

### 问题诊断
- 问题类型：<描述>
- 原因分析：<详细分析>

### 解决方案
- 已添加DIRECT 规则：<文件路径>
- 已添加fake-ip-filter：<文件路径>

### 验证结果
- DNS：<变化>
- 延迟改善：<对比数据>
```

## 注意事项

1. **不要盲目修改配置**
   - 必须先诊断确认问题
   - 必须对比直连 vs经 Clash 的差异

2. **fake-ip-filter 缩进**
   - YAML 缩进必须正确（2空格）
   - 使用 `- +.` 格式匹配子域名

3. **规则优先级**
   - prepend 规则在最前面
   - 确保 DIRECT 规则在 MATCH 之前

4. **必须验证生效**
   - Mihomo 需要重载配置
   - DNS缓存可能导致延迟生效，多测几次

## 常用域名模板

根据用途提供规则模板：

```yaml
# 国内AI API
- DOMAIN-SUFFIX,dashscope.aliyuncs.com,DIRECT    # 阿里通义- DOMAIN-SUFFIX,qianfan.baidubce.com,DIRECT     # 百度千帆
- DOMAIN-SUFFIX,hunyuan.tencentcloudapi.com,DIRECT # 腾讯混元
- DOMAIN-SUFFIX,bigmodel.cn,DIRECT               # 智谱GLM
- DOMAIN-SUFFIX,deepseek.com,DIRECT              # DeepSeek
- DOMAIN-SUFFIX,moonshot.cn,DIRECT               # Moonshot

# 自建服务
- DOMAIN-SUFFIX,<your-domain>,DIRECT

# fake-ip-filter 对应
fake-ip-filter:
  - +.dashscope.aliyuncs.com
  - +.qianfan.baidubce.com
  - +.<your-domain>
```