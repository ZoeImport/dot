# md-to-docx-with-mermaid 参考

## mermaid-filter 属性

在 fenced code block 后添加 `{.mermaid ...}` 控制渲染：

| 属性 | 说明 | 示例 |
|------|------|------|
| `format=svg` | 输出 SVG（默认 PNG） | `{.mermaid format=svg}` |
| `width=N` | 图片宽度像素 | `{.mermaid width=400}` |
| `caption="..."` | 图片标题 | `{.mermaid caption="流程图"}` |
| `theme=forest` | Mermaid 主题 | `{.mermaid theme=forest}` |
| `background=transparent` | 透明背景 | `{.mermaid background=transparent}` |
| `filename="..."` | 输出文件名 | `{.mermaid filename="my-diagram"}` |
| `loc=img` | 图片保存到 `img` 目录 | `{.mermaid loc=img}` |
| `#fig:id` | 配合 pandoc-crossref 引用 | `{.mermaid #fig:flow1}` |

## 环境变量

可用 `MERMAID_FILTER_` 前缀覆盖默认值：

- `MERMAID_FILTER_WIDTH`
- `MERMAID_FILTER_FORMAT`
- 等

## 配置文件

当前目录下可放置：

- `.mermaid-config.json`：Mermaid CLI 配置
- `.mermaid.css`：Mermaid 样式
- `.puppeteer.json`：Puppeteer 配置（mermaid-cli 使用）

## 多过滤器

若同时使用 pandoc-crossref，需**先**执行 mermaid-filter：

```bash
pandoc -F mermaid-filter -F pandoc-crossref input.md -o output.docx
```
