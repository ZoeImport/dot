/**
 * DOCX Generator - 深入演示 docx 本质是 zip+XML 的概念
 *
 * 用 docxtemplater + PizZip 从零构建一个完整的 DOCX 文件，
 * 包含：各级标题、多种字体样式、目录(TOC)
 *
 * 核心理论：
 *   .docx = ZIP 压缩包
 *   ├── [Content_Types].xml     (内容类型声明)
 *   ├── _rels/.rels             (顶层关系)
 *   ├── word/
 *   │   ├── document.xml        (正文内容)
 *   │   ├── styles.xml          (样式定义)
 *   │   ├── numbering.xml       (编号定义)
 *   │   ├── fontTable.xml       (字体表)
 *   │   └── _rels/document.xml.rels (文档关系)
 *   └── docProps/
 *       ├── core.xml
 *       └── app.xml
 *
 * 所有 XML 都可以直接操作——这就是"原生支持"的含义。
 */

const PizZip = require("pizzip");
const Docxtemplater = require("docxtemplater");
const fs = require("fs");
const path = require("path");

// ============================================================
// 1. 从零构建一个可用的 DOCX 模板 (纯 XML + ZIP)
// ============================================================
// 我们手动创建每一个 XML 文件，演示 DOCX 的内部结构。

function buildTemplate() {
  const zip = new PizZip();

  // ----------------------------------------------------------
  // [Content_Types].xml — 声明包内所有文件类型
  // ----------------------------------------------------------
  zip.file(
    "[Content_Types].xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>`
  );

  // ----------------------------------------------------------
  // _rels/.rels — 顶层关系，指向文档主入口
  // ----------------------------------------------------------
  zip.file(
    "_rels/.rels",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`
  );

  // ----------------------------------------------------------
  // word/_rels/document.xml.rels — 文档内部资源关系
  // ----------------------------------------------------------
  zip.file(
    "word/_rels/document.xml.rels",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
</Relationships>`
  );

  // ----------------------------------------------------------
  // word/fontTable.xml — 声明文档中使用的字体
  // ----------------------------------------------------------
  zip.file(
    "word/fontTable.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
         xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:font w:name="SimHei"><w:altName w:val="黑体"/></w:font>
  <w:font w:name="SimSun"><w:altName w:val="宋体"/></w:font>
  <w:font w:name="KaiTi"><w:altName w:val="楷体"/></w:font>
  <w:font w:name="FangSong"><w:altName w:val="仿宋"/></w:font>
  <w:font w:name="Microsoft YaHei"><w:altName w:val="微软雅黑"/></w:font>
  <w:font w:name="Calibri"><w:altName w:val="Calibri"/></w:font>
  <w:font w:name="Times New Roman"><w:altName w:val="Times New Roman"/></w:font>
  <w:font w:name="Arial"><w:altName w:val="Arial"/></w:font>
  <w:font w:name="Courier New"><w:altName w:val="Courier New"/></w:font>
</w:fonts>`
  );

  // ----------------------------------------------------------
  // word/styles.xml — 定义所有样式 (标题、正文、字体、颜色)
  // ----------------------------------------------------------
  zip.file(
    "word/styles.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
          xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">

  <!-- ===== 段落样式 ===== -->

  <!-- Normal - 正文默认 -->
  <w:style w:type="paragraph" w:styleId="Normal" w:default="true">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="200" w:line="360" w:lineRule="auto"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/>
      <w:sz w:val="24"/>     <!-- 12pt -->
      <w:szCs w:val="24"/>
    </w:rPr>
  </w:style>

  <!-- Heading 1 - 一级标题：黑体 28pt 红色 -->
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="480" w:after="240"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="SimHei" w:hAnsi="SimHei" w:eastAsia="SimHei"/>
      <w:b/>
      <w:sz w:val="56"/>     <!-- 28pt -->
      <w:szCs w:val="56"/>
      <w:color w:val="C00000"/>  <!-- 深红色 -->
    </w:rPr>
  </w:style>

  <!-- Heading 2 - 二级标题：宋体 22pt 蓝色 -->
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="360" w:after="180"/>
      <w:outlineLvl w:val="1"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
      <w:b/>
      <w:sz w:val="44"/>     <!-- 22pt -->
      <w:szCs w:val="44"/>
      <w:color w:val="2E75B6"/>  <!-- 蓝色 -->
    </w:rPr>
  </w:style>

  <!-- Heading 3 - 三级标题：楷体 18pt 绿色 -->
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="280" w:after="140"/>
      <w:outlineLvl w:val="2"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="KaiTi" w:hAnsi="KaiTi" w:eastAsia="KaiTi"/>
      <w:b/>
      <w:sz w:val="36"/>     <!-- 18pt -->
      <w:szCs w:val="36"/>
      <w:color w:val="548235"/>  <!-- 绿色 -->
    </w:rPr>
  </w:style>

  <!-- Heading 4 - 四级标题：仿宋 16pt 紫色 -->
  <w:style w:type="paragraph" w:styleId="Heading4">
    <w:name w:val="heading 4"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:keepNext/>
      <w:keepLines/>
      <w:spacing w:before="200" w:after="100"/>
      <w:outlineLvl w:val="3"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="FangSong" w:hAnsi="FangSong" w:eastAsia="FangSong"/>
      <w:b/>
      <w:i/>
      <w:sz w:val="32"/>     <!-- 16pt -->
      <w:szCs w:val="32"/>
      <w:color w:val="7030A0"/>  <!-- 紫色 -->
    </w:rPr>
  </w:style>

  <!-- ===== 字符样式 ===== -->

  <!-- 粗体红色 -->
  <w:style w:type="character" w:styleId="BoldRed">
    <w:name w:val="BoldRed"/>
    <w:rPr>
      <w:b/>
      <w:color w:val="FF0000"/>
    </w:rPr>
  </w:style>

  <!-- 斜体蓝色 -->
  <w:style w:type="character" w:styleId="ItalicBlue">
    <w:name w:val="ItalicBlue"/>
    <w:rPr>
      <w:i/>
      <w:color w:val="0070C0"/>
    </w:rPr>
  </w:style>

  <!-- 下划线 -->
  <w:style w:type="character" w:styleId="Underline">
    <w:name w:val="Underline"/>
    <w:rPr>
      <w:u w:val="single"/>
    </w:rPr>
  </w:style>

  <!-- Courier New 等宽字体 -->
  <w:style w:type="character" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:rPr>
      <w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>
      <w:sz w:val="20"/>
      <w:szCs w:val="20"/>
    </w:rPr>
  </w:style>
</w:styles>`
  );

  // ----------------------------------------------------------
  // word/numbering.xml — 编号/列表定义
  // ----------------------------------------------------------
  zip.file(
    "word/numbering.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="multilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1."/>
    </w:lvl>
    <w:lvl w:ilvl="1">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1.%2"/>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1">
    <w:abstractNumId w:val="0"/>
  </w:num>
</w:numbering>`
  );

  // ----------------------------------------------------------
  // docProps/core.xml — 文档元数据
  // ----------------------------------------------------------
  zip.file(
    "docProps/core.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/">
  <dc:title>DOCX 格式深度演示</dc:title>
  <dc:creator>Sisyphus</dc:creator>
  <dc:description>演示 docx 本质是 zip + xml 的组合体</dc:description>
  <dcterms:created>2026-06-01T00:00:00Z</dcterms:created>
</cp:coreProperties>`
  );

  // ----------------------------------------------------------
  // docProps/app.xml — 应用程序属性
  // ----------------------------------------------------------
  zip.file(
    "docProps/app.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Sisyphus DOCX Demo</Application>
  <DocSecurity>0</DocSecurity>
  <Lines>1</Lines>
  <Paragraphs>1</Paragraphs>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
               size="4" baseType="variant">
      <vt:variant><vt:lpath>标题</vt:lpath></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
               size="1" baseType="lpstr">
      <vt:lpstr>DOCX 格式深度演示</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
</Properties>`
  );

  // ----------------------------------------------------------
  // word/document.xml — ★ 核心：正文内容
  //
  // 这里我们在模板中嵌入 docxtemplater 标签 { }
  // 同时嵌入 TOC 域代码(目录)
  //
  // TOC 域代码结构:
  //   <w:fldChar w:fldCharType="begin"/>
  //   <w:instrText> TOC \o "1-3" \h \z \u </w:instrText>
  //   <w:fldChar w:fldCharType="separate"/>
  //   ... 占位文字 (Word 打开后自动更新)
  //   <w:fldChar w:fldCharType="end"/>
  // ----------------------------------------------------------
  zip.file(
    "word/document.xml",
    `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
            xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">

  <w:body>

    <!-- ===== 文档标题 (不加入 TOC 目录) ===== -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="600" w:after="400"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Microsoft YaHei" w:hAnsi="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/>
          <w:b/>
          <w:sz w:val="72"/>     <!-- 36pt -->
          <w:szCs w:val="72"/>
          <w:color w:val="1F3864"/>
        </w:rPr>
        <w:t>{docTitle}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="600"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
          <w:i/>
          <w:sz w:val="28"/>
          <w:color w:val="404040"/>
        </w:rPr>
        <w:t>{docSubtitle}</w:t>
      </w:r>
    </w:p>

    <!-- ===== 目录 (TOC) - 通过 Word XML 域代码实现 ===== -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
        <w:spacing w:before="600" w:after="400"/>
      </w:pPr>
      <w:r>
        <w:t>目录</w:t>
      </w:r>
    </w:p>

    <!-- Table of Contents field code: levels 1-3, hyperlinks, use paragraph styles -->
    <w:p>
      <w:r>
        <w:fldChar w:fldCharType="begin"/>
      </w:r>
      <w:r>
        <w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText>
      </w:r>
      <w:r>
        <w:fldChar w:fldCharType="separate"/>
      </w:r>
      <w:r>
        <w:rPr>
          <w:color w:val="808080"/>
          <w:i/>
        </w:rPr>
        <w:t>[ 请在 Word 中右键点击此处 → 更新域 以生成目录 ]</w:t>
      </w:r>
      <w:r>
        <w:fldChar w:fldCharType="end"/>
      </w:r>
    </w:p>

    <!-- 分页 -->
    <w:p>
      <w:r>
        <w:br w:type="page"/>
      </w:r>
    </w:p>

    <!-- ===== 正文开始 - 使用 docxtemplater 循环 ===== -->

    <!-- 第一章 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
        <w:spacing w:before="480" w:after="240"/>
      </w:pPr>
      <w:r>
        <w:t>{chapter1Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:pPr><w:spacing w:after="200"/></w:pPr>
      <w:r>
        <w:t>{chapter1Intro}</w:t>
      </w:r>
    </w:p>

    <!-- 1.1 节 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading2"/>
      </w:pPr>
      <w:r>
        <w:t>{section1_1Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:pPr><w:spacing w:after="200"/></w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
        </w:rPr>
        <w:t>{section1_1Body}</w:t>
      </w:r>
    </w:p>

    <!-- 1.1.1 小节 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading3"/>
      </w:pPr>
      <w:r>
        <w:t>{subsection1_1_1Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:pPr><w:spacing w:after="200"/></w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="KaiTi" w:hAnsi="KaiTi" w:eastAsia="KaiTi"/>
          <w:sz w:val="24"/>
        </w:rPr>
        <w:t>{subsection1_1_1Body}</w:t>
      </w:r>
    </w:p>

    <!-- 四级标题 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading4"/>
      </w:pPr>
      <w:r>
        <w:t>{subsection1_1_2Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:pPr><w:spacing w:after="200"/></w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="FangSong" w:hAnsi="FangSong" w:eastAsia="FangSong"/>
          <w:i/>
        </w:rPr>
        <w:t>{subsection1_1_2Body}</w:t>
      </w:r>
    </w:p>

    <!-- 1.2 节 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading2"/>
      </w:pPr>
      <w:r>
        <w:t>{section1_2Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
        </w:rPr>
        <w:t>{section1_2Body}</w:t>
      </w:r>
    </w:p>

    <!-- 第二章 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
      </w:pPr>
      <w:r>
        <w:t>{chapter2Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:r>
        <w:t>{chapter2Intro}</w:t>
      </w:r>
    </w:p>

    <!-- 2.1 节 -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading2"/>
      </w:pPr>
      <w:r>
        <w:t>{section2_1Title}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
        </w:rPr>
        <w:t>{section2_1Body}</w:t>
      </w:r>
    </w:p>

    <!-- ===== 字体样式演示区 ===== -->

    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
        <w:spacing w:before="600" w:after="400"/>
      </w:pPr>
      <w:r>
        <w:t>{fontDemoTitle}</w:t>
      </w:r>
    </w:p>

    <!-- 各种字体演示 -->
    <w:p><w:r><w:t>【以下演示各种字体和样式】</w:t></w:r></w:p>

    <!-- 宋体 - 常规 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>宋体 - 这是中文排版中最常用的字体 (SimSun 12pt 常规)</w:t>
      </w:r>
    </w:p>

    <!-- 黑体 - 粗体 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimHei" w:hAnsi="SimHei" w:eastAsia="SimHei"/>
          <w:b/>
          <w:sz w:val="32"/>
          <w:color w:val="1F3864"/>
        </w:rPr>
        <w:t>黑体 SimHei - 粗体 16pt 深蓝色 - 适合标题和强调</w:t>
      </w:r>
    </w:p>

    <!-- 楷体 - 斜体 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="KaiTi" w:hAnsi="KaiTi" w:eastAsia="KaiTi"/>
          <w:i/>
          <w:sz w:val="28"/>
          <w:color w:val="548235"/>
        </w:rPr>
        <w:t>楷体 KaiTi - 斜体 14pt 绿色 - 适合引文和注释</w:t>
      </w:r>
    </w:p>

    <!-- 仿宋 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="FangSong" w:hAnsi="FangSong" w:eastAsia="FangSong"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>仿宋 FangSong - 14pt - 常用于正式公文</w:t>
      </w:r>
    </w:p>

    <!-- 微软雅黑 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Microsoft YaHei" w:hAnsi="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/>
          <w:b/>
          <w:sz w:val="30"/>
          <w:color w:val="2E75B6"/>
        </w:rPr>
        <w:t>微软雅黑 Microsoft YaHei - 粗体 15pt - 现代感强</w:t>
      </w:r>
    </w:p>

    <!-- Calibri -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
          <w:color w:val="404040"/>
        </w:rPr>
        <w:t>Calibri - Default body font in Office 2007+ themes</w:t>
      </w:r>
    </w:p>

    <!-- Times New Roman -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
          <w:i/>
          <w:sz w:val="30"/>
          <w:color w:val="595959"/>
        </w:rPr>
        <w:t>Times New Roman - Classic serif font for academic papers</w:t>
      </w:r>
    </w:p>

    <!-- Courier New 代码字体 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>
          <w:sz w:val="24"/>
          <w:szCs w:val="24"/>
          <w:color w:val="2B579A"/>
        </w:rPr>
        <w:t>Courier New - Monospace font: const foo = (x) =&gt; x * 2;</w:t>
      </w:r>
    </w:p>

    <!-- Arial -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
          <w:b/>
          <w:i/>
          <w:sz w:val="28"/>
          <w:color w:val="C00000"/>
        </w:rPr>
        <w:t>Arial - Bold+Italic 14pt Red - Sans-serif alternative</w:t>
      </w:r>
    </w:p>

    <!-- 下划线演示 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun"/>
          <w:u w:val="single"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>这是带下划线的文字 (宋体 14pt 单下划线)</w:t>
      </w:r>
    </w:p>

    <!-- 双下划线 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimHei" w:hAnsi="SimHei"/>
          <w:u w:val="double"/>
          <w:sz w:val="28"/>
          <w:color w:val="C00000"/>
        </w:rPr>
        <w:t>这是带双下划线的文字 (黑体 14pt 双下划线)</w:t>
      </w:r>
    </w:p>

    <!-- 删除线 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun"/>
          <w:strike w:val="true"/>
          <w:sz w:val="28"/>
          <w:color w:val="808080"/>
        </w:rPr>
        <w:t>这是带删除线的文字</w:t>
      </w:r>
    </w:p>

    <!-- 上标和下标 -->
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>科学公式: E = mc</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="20"/>
          <w:vertAlign w:val="superscript"/>
        </w:rPr>
        <w:t>2</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>,  H</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="20"/>
          <w:vertAlign w:val="subscript"/>
        </w:rPr>
        <w:t>2</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>O</w:t>
      </w:r>
    </w:p>

    <!-- 多种颜色演示 -->
    <w:p>
      <w:r>
        <w:rPr><w:color w:val="FF0000"/><w:sz w:val="28"/></w:rPr>
        <w:t>红色 </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:color w:val="FF8C00"/><w:sz w:val="28"/></w:rPr>
        <w:t>橙色 </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:color w:val="FFFF00"/><w:sz w:val="28"/></w:rPr>
        <w:t>黄色 </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:color w:val="00B050"/><w:sz w:val="28"/></w:rPr>
        <w:t>绿色 </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:color w:val="0070C0"/><w:sz w:val="28"/></w:rPr>
        <w:t>蓝色 </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:color w:val="7030A0"/><w:sz w:val="28"/></w:rPr>
        <w:t>紫色</w:t>
      </w:r>
    </w:p>

    <!-- ===== 混合字体演示 ===== -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading2"/>
        <w:spacing w:before="480" w:after="240"/>
      </w:pPr>
      <w:r>
        <w:t>混合字体演示</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t>「同一段落中，</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimHei" w:hAnsi="SimHei" w:eastAsia="SimHei"/>
          <w:b/>
          <w:sz w:val="28"/>
          <w:color w:val="C00000"/>
        </w:rPr>
        <w:t>可以混用多种字体</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="KaiTi" w:hAnsi="KaiTi" w:eastAsia="KaiTi"/>
          <w:i/>
          <w:sz w:val="28"/>
          <w:color w:val="548235"/>
        </w:rPr>
        <w:t>、颜色、大小</w:t>
      </w:r>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
        </w:rPr>
        <w:t> and even English fonts in one paragraph!」</w:t>
      </w:r>
    </w:p>

    <!-- 分页 -->
    <w:p>
      <w:r>
        <w:br w:type="page"/>
      </w:r>
    </w:p>

    <!-- ===== 总结章节 ===== -->
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
      </w:pPr>
      <w:r>
        <w:t>{conclusionTitle}</w:t>
      </w:r>
    </w:p>

    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="SimSun" w:hAnsi="SimSun" w:eastAsia="SimSun"/>
          <w:sz w:val="26"/>
        </w:rPr>
        <w:t>{conclusionBody}</w:t>
      </w:r>
    </w:p>

  </w:body>
</w:document>`
  );

  return zip;
}

// ============================================================
// 2. 使用 docxtemplater 处理模板
// ============================================================

function generateDocx(zip, data) {
  const doc = new Docxtemplater(zip, {
    paragraphLoop: true,
  });

  try {
    doc.render(data);
  } catch (error) {
    console.error("❌ docxtemplater 渲染出错:");
    console.error(error);

    // 如果是模板错误,打印详细信息
    if (error.properties && error.properties.errors) {
      const errs = error.properties.errors;
      errs.forEach((e) => {
        console.error(`  [${e.name}] ${e.message}`);
        if (e.properties && e.properties.explanation) {
          console.error(`  解释: ${e.properties.explanation}`);
        }
      });
    }
    process.exit(1);
  }

  return doc.getZip().generate({
    type: "nodebuffer",
    compression: "DEFLATE",
    mimeType:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
}

// ============================================================
// 3. 数据 + 执行
// ============================================================

const data = {
  docTitle: "DOCX 格式深度解析",
  docSubtitle: "—— 基于 docxtemplater + XML 原生操作 ——",

  chapter1Title: "第一章 DOCX 文件格式概述",
  chapter1Intro:
    "DOCX 是 Office Open XML (OOXML) 格式的一种实现。本质上，一个 .docx 文件就是一个 ZIP 压缩包，里面包含了多个 XML 文件以及相关的资源文件（图片、字体等）。这种设计使得开发者可以直接操作文件内部结构来实现 Word 本身支持的任何功能。",
  section1_1Title: "1.1 核心结构",
  section1_1Body:
    "一个标准 DOCX 文件的核心是 word/document.xml，它存储了所有的正文内容。但仅靠这个文件还不够——还需要 word/styles.xml 定义样式、word/numbering.xml 定义编号、[Content_Types].xml 声明文件类型等等。所有这些 XML 文件协同工作，构成了一个完整的 Word 文档。",
  subsection1_1_1Title: "1.1.1 XML 命名空间体系",
  subsection1_1_1Body:
    "OOXML 使用大量的 XML 命名空间来区分不同用途的标签。最核心的是 w: 前缀（http://schemas.openxmlformats.org/wordprocessingml/2006/main），它定义了段落 <w:p>、文本 <w:t>、样式 <w:pPr> 等基础元素。理解这些命名空间是直接操作 DOCX 的关键。",
  subsection1_1_2Title: "1.1.2 关系文件 (.rels) 的作用",
  subsection1_1_2Body:
    ".rels 文件是 DOCX 的「路由表」。每一层目录都有自己的 _rels/.rels 文件，用来声明该层级的资源引用关系。例如 word/_rels/document.xml.rels 告诉 Word：样式文件在 styles.xml、字体定义在 fontTable.xml。这种松耦合的设计使得 DOCX 非常灵活。",
  section1_2Title: "1.2 基于模板的生成 vs 原生 XML 操作",
  section1_2Body:
    "docxtemplater 等模板引擎在预制的 DOCX 模板中插入占位符，适合结构化文档的批量生成。但如果你需要实现 Word 原生支持但模板引擎不支持的功能（如目录 TOC、复杂的域代码、自定义 XML 绑定），直接操作 ZIP 内部的 XML 文件是唯一可靠的方式。这就是本文所述理论的实际应用。",

  chapter2Title: "第二章 字体与样式系统",
  chapter2Intro:
    "Word 的样式系统非常丰富。每个段落可以引用一个段落样式（如 Heading1），其中定义了字体、大小、颜色、间距等属性。字符样式则可以精细控制段落中某一段文字的格式。本演示展示了多种中英文字体、大小、颜色和修饰效果的组合。",
  section2_1Title: "2.1 字体回退机制",
  section2_1Body:
    "在 fontTable.xml 中定义的字体可能在某些系统上不存在。Word 会在 <w:altName> 中指定的备选字体中查找。这就是为什么即使你的系统没有 SimHei，Word 仍然可以尝试用相近字体显示。对于跨平台文档分发，合理设置备选字体非常重要。",

  fontDemoTitle: "第三章 字体与样式效果演示",

  conclusionTitle: "总结",
  conclusionBody:
    "通过本演示可以看到：DOCX 格式的开放性使得程序化生成成为可能。docxtemplater 简化了基于模板的生成流程，而当需要原生功能时，直接操作 ZIP 内的 XML 文件是终极方案。理解了「DOCX = ZIP + XML」这一核心理念，你就可以实现 Word 支持的任何功能。",
};

// ============================================================
// 执行
// ============================================================

console.log("=".repeat(60));
console.log("📄 DOCX 生成器");
console.log("=".repeat(60));
console.log("\n🔨 第1步: 从零构建 DOCX 模板 (纯 XML + ZIP)...");
const templateZip = buildTemplate();
console.log("   ✅ 模板构建完成 (%d 个文件)", Object.keys(templateZip.files).length);

console.log("\n🔨 第2步: 使用 docxtemplater 处理模板...");
const output = generateDocx(templateZip, data);
console.log("   ✅ 渲染完成");

const outputPath = path.join(__dirname, "output-demo.docx");
fs.writeFileSync(outputPath, output);
console.log(`\n📁 输出文件: ${outputPath}`);
console.log(`   File size: ${(output.length / 1024).toFixed(1)} KB`);

console.log("\n🔍 DOCX 内部文件列表:");
const PizZip2 = require("pizzip");
const checkZip = new PizZip2(output);
Object.keys(checkZip.files)
  .filter((name) => !checkZip.files[name].dir)
  .forEach((name) => {
    const content = checkZip.files[name].asText();
    const size = Buffer.byteLength(content, "utf8");
    const ext = name.split(".").pop();
    console.log(
      `   📄 ${name} (${(size / 1024).toFixed(1)} KB)` +
        (ext === "xml" || ext === "rels" ? " - XML" : "")
    );
  });

console.log("\n" + "=".repeat(60));
console.log("✅ 完成! 请用 Word / WPS 打开 output-demo.docx");
console.log("   → 右键点击目录区域 → 选择「更新域」以生成目录");
console.log("=".repeat(60));
