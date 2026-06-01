/**
 * DOCX 内部结构分析工具
 *
 * 演示核心理论：.docx = ZIP 压缩包，内部全是 XML
 *
 * 使用方法: node inspect.js <路径到docx文件>
 * 如果未指定文件，默认分析刚刚生成的 output-demo.docx
 */

const PizZip = require("pizzip");
const fs = require("fs");
const path = require("path");

// ANSI 颜色
const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const DIM = "\x1b[2m";
const GREEN = "\x1b[32m";
const CYAN = "\x1b[36m";
const YELLOW = "\x1b[33m";
const MAGENTA = "\x1b[35m";

function inspectDocx(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`❌ 文件不存在: ${filePath}`);
    process.exit(1);
  }

  const buffer = fs.readFileSync(filePath);
  const zip = new PizZip(buffer);

  console.log(`\n${BOLD}${CYAN}📦 DOCX 内部结构分析${RESET}`);
  console.log(`${DIM}文件: ${filePath}${RESET}`);
  console.log(`${DIM}大小: ${(buffer.length / 1024).toFixed(1)} KB${RESET}`);
  console.log(
    `${DIM}内部文件数: ${Object.keys(zip.files).length}${RESET}\n`
  );

  const entries = Object.entries(zip.files).sort(([a], [b]) =>
    a.localeCompare(b)
  );

  for (const [name, file] of entries) {
    const isDir = file.dir;
    const rawSize = file._data?.binary?.length || 0;
    const sizeStr = rawSize > 1024
      ? `${(rawSize / 1024).toFixed(1)} KB`
      : `${rawSize} B`;

    if (isDir) {
      console.log(`  ${BOLD}${YELLOW}📁 ${name}${RESET}`);
    } else {
      const ext = path.extname(name).toLowerCase();
      let icon = "📄";
      if (ext === ".xml") icon = "📄";
      else if (ext === ".rels") icon = "🔗";
      else if (ext === ".png" || ext === ".jpg" || ext === ".jpeg")
        icon = "🖼️";
      else if (ext === ".wmf" || ext === ".emf") icon = "🎨";

      console.log(`  ${icon} ${name}  ${DIM}(${sizeStr})${RESET}`);

      // 打印 XML 文件的前几行
      if (ext === ".xml" || ext === ".rels") {
        try {
          const content = file.asText();
          const lines = content.split("\n");
          // 只显示根标签
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("<?")) continue; // 跳过 XML 声明
            if (trimmed.startsWith("<")) {
              const tagEnd = trimmed.indexOf(">");
              const tag = tagEnd > 0 ? trimmed.substring(0, tagEnd + 1) : trimmed;
              // 简化显示,只保留标签名+前2个属性
              const simplified = tag.length > 120 ? tag.substring(0, 120) + "…>" : tag;
              console.log(`    ${DIM}根元素: ${GREEN}${simplified}${RESET}`);
              break;
            }
          }
        } catch (e) {
          // binary or empty
        }
      }
    }
  }

  // 特定的关键 XML 内容预览
  console.log(`\n${BOLD}${CYAN}🔬 关键 XML 内容预览${RESET}`);

  // 1. document.xml — 正文
  if (zip.files["word/document.xml"]) {
    const docXml = zip.files["word/document.xml"].asText();
    console.log(`\n${BOLD}word/document.xml${RESET} ${DIM}(核心正文)${RESET}`);
    const titleMatch = docXml.match(/<w:t[^>]*>([^<]+)<\/w:t>/);
    if (titleMatch) {
      console.log(`  首段文字: "${titleMatch[1]}"`);
    }
    const headingCount = (docXml.match(/w:pStyle w:val="Heading1"/g) || []).length;
    const tocHasField = docXml.includes("TOC");
    console.log(`  Heading1 数量: ${headingCount}`);
    console.log(`  包含 TOC 域: ${tocHasField ? YELLOW + "✅ 是" : "❌ 否"}${RESET}`);
  }

  // 2. styles.xml — 样式
  if (zip.files["word/styles.xml"]) {
    const stylesXml = zip.files["word/styles.xml"].asText();
    console.log(`\n${BOLD}word/styles.xml${RESET} ${DIM}(样式定义)${RESET}`);
    const styleIds = [...stylesXml.matchAll(/w:styleId="([^"]+)"/g)].map(
      (m) => m[1]
    );
    console.log(`  定义的样式: ${styleIds.join(", ")}`);
  }

  // 3. fontTable.xml — 字体表
  if (zip.files["word/fontTable.xml"]) {
    const fontXml = zip.files["word/fontTable.xml"].asText();
    console.log(`\n${BOLD}word/fontTable.xml${RESET} ${DIM}(字体表)${RESET}`);
    const fonts = [...fontXml.matchAll(/w:font w:name="([^"]+)"/g)].map(
      (m) => m[1]
    );
    console.log(`  注册字体: ${fonts.join(", ")}`);
  }

  // 4. numbering.xml — 编号
  if (zip.files["word/numbering.xml"]) {
    console.log(`\n${BOLD}word/numbering.xml${RESET} ${DIM}(编号定义)${RESET} ✅ 存在`);
  }

  // 5. [Content_Types].xml — 内容类型
  if (zip.files["[Content_Types].xml"]) {
    const ctXml = zip.files["[Content_Types].xml"].asText();
    console.log(`\n${BOLD}[Content_Types].xml${RESET} ${DIM}(内容类型清单)${RESET}`);
    const overrides = [
      ...ctXml.matchAll(/PartName="([^"]+)".*?ContentType="([^"]+)"/g),
    ];
    for (const [, part, type] of overrides) {
      console.log(`  ${part.padEnd(30)} ${DIM}→${RESET} ${type}`);
    }
  }

  console.log(`\n${BOLD}${GREEN}✅ 分析完成${RESET}`);
  console.log(
    `${DIM}核心结论: DOCX 就是一个 ZIP 包, 内部全是 XML 文件协作构成文档${RESET}\n`
  );
}

// 如果命令行传入了文件路径则使用, 否则默认
const targetFile = process.argv[2] || path.join(__dirname, "output-demo.docx");
inspectDocx(targetFile);
