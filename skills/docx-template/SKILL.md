---
name: docx-template
description: Use when generating Word (.docx) files programmatically via docxtemplater, or when needing to understand the internal structure of DOCX files (ZIP + XML architecture, OOXML namespaces, styles, fonts, TOC fields).
---

# DOCX Template Generation

Generate Word documents programmatically using [docxtemplater](https://docxtemplater.com/) + [PizZip](https://www.npmjs.com/package/pizzip).

## Core Concept

**A `.docx` file IS a ZIP archive containing XML files:**

```
.docx = ZIP
 ├── [Content_Types].xml          (MIME types for every file)
 ├── _rels/.rels                  (root relationships)
 ├── word/
 │   ├── document.xml             (BODY content + placeholders)
 │   ├── styles.xml               (paragraph + character styles)
 │   ├── numbering.xml            (list numbering definitions)
 │   ├── fontTable.xml            (font declarations)
 │   └── _rels/document.xml.rels  (document resource map)
 └── docProps/
     ├── core.xml                 (metadata: title, author)
     └── app.xml                  (application properties)
```

Understanding this structure means you can implement ANY Word feature by directly editing the XML — including Table of Contents, complex fields, custom XML binding, etc.

## When to Use This vs Other Approaches

| Approach | Best For | Limitation |
|----------|----------|------------|
| **docxtemplater** | Template-based batch generation with `{placeholders}` | TOC, complex fields need XML injection |
| **Raw XML + JSZip** | Features not supported by template engines | More verbose, need to understand OOXML schema |
| **officegen / docx** | Building documents from scratch in JS | Less control over low-level XML |

## Quick Start

```bash
npm install docxtemplater pizzip
```

### 1. Build Template (ZIP + XML)

```js
const PizZip = require("pizzip");
const Docxtemplater = require("docxtemplater");

const zip = new PizZip();

// Each XML file is added as a named entry in the ZIP
zip.file("[Content_Types].xml", `<Types xmlns="..."> ... </Types>`);
zip.file("_rels/.rels", `<Relationships ...> ... </Relationships>`);
zip.file("word/document.xml", `<w:document> ... {placeholder} ... </w:document>`);
zip.file("word/styles.xml", `<w:styles> ... </w:styles>`);
zip.file("word/fontTable.xml", `<w:fonts> ... </w:fonts>`);
zip.file("word/numbering.xml", `<w:numbering> ... </w:numbering>`);
zip.file("word/_rels/document.xml.rels", `<Relationships ...> ... </Relationships>`);
zip.file("docProps/core.xml", `<cp:coreProperties> ... </cp:coreProperties>`);
zip.file("docProps/app.xml", `<Properties> ... </Properties>`);
```

### 2. Add docxtemplater Placeholders

In `word/document.xml`, use `{tagName}` syntax:

```xml
<w:p>
  <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
  <w:r><w:t>{chapterTitle}</w:t></w:r>
</w:p>
```

### 3. Render

```js
const doc = new Docxtemplater(zip, { paragraphLoop: true });
doc.render({ chapterTitle: "Chapter 1" });
const buffer = doc.getZip().generate({
  type: "nodebuffer",
  compression: "DEFLATE",
});
```

## Headings & Styles

Define styles in `word/styles.xml`. Each heading has an `outlineLvl` for TOC hierarchy:

| Level | styleId | outlineLvl | Font | Size | Color |
|-------|---------|------------|------|------|-------|
| H1 | Heading1 | 0 | SimHei (黑体) | 28pt | C00000 |
| H2 | Heading2 | 1 | SimSun (宋体) | 22pt | 2E75B6 |
| H3 | Heading3 | 2 | KaiTi (楷体) | 18pt | 548235 |
| H4 | Heading4 | 3 | FangSong (仿宋) | 16pt | 7030A0 |
| Normal | Normal | — | Calibri / 宋体 | 12pt | — |

Run properties use `w:rPr` within `<w:r>`:
```xml
<w:r>
  <w:rPr>
    <w:rFonts w:ascii="SimHei" w:eastAsia="SimHei"/>
    <w:b/>                    <!-- bold -->
    <w:i/>                    <!-- italic -->
    <w:u w:val="single"/>     <!-- underline -->
    <w:strike/>               <!-- strikethrough -->
    <w:color w:val="FF0000"/> <!-- color -->
    <w:sz w:val="28"/>        <!-- font size in half-points -->
    <w:vertAlign w:val="superscript"/>  <!-- superscript -->
  </w:rPr>
  <w:t>text here</w:t>
</w:r>
```

## Table of Contents (TOC)

TOC is a **Word field code** injected directly into `word/document.xml` via XML:

```xml
<w:p>
  <!-- BEGIN field -->
  <w:r><w:fldChar w:fldCharType="begin"/></w:r>
  <!-- Field instruction: \o "1-3" = levels 1-3, \h = hyperlinks -->
  <w:r><w:instrText xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText></w:r>
  <!-- SEPARATE (placeholder display text) -->
  <w:r><w:fldChar w:fldCharType="separate"/></w:r>
  <w:r><w:t>[Right-click → Update Field in Word]</w:t></w:r>
  <!-- END field -->
  <w:r><w:fldChar w:fldCharType="end"/></w:r>
</w:p>
```

> **Note:** TOC populates only when the user opens the file in Word/WPS and right-clicks → "Update Field". This is standard Word behavior, not a limitation of this approach.

## Font Table

Declare fonts in `word/fontTable.xml` with optional `w:altName` fallbacks:

```xml
<w:fonts>
  <w:font w:name="SimHei"><w:altName w:val="黑体"/></w:font>
  <w:font w:name="Calibri"/>
  <w:font w:name="Courier New"/>
</w:fonts>
```

## Supporting Files

- **`generate.js`** — Complete working example: builds DOCX from scratch + renders with docxtemplater
- **`inspect.js`** — Analyzes any `.docx` file's internal XML structure (run: `node inspect.js <file.docx>`)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| TOC doesn't appear | Update fields in Word (right-click → Update Field) |
| Fonts not showing on other systems | Always set `w:altName` with localized font name |
| Placeholder `{tag}` not replaced | Ensure the tag exists in both template and data object |
| Heading not in TOC | Check `w:outlineLvl` matches the heading level |
| DOCX won't open in Word | Validate XML structure; run `node inspect.js` to check |
