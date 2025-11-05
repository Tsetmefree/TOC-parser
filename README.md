# 📚 Document TOC Parser

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**智能文档目录提取器** - 将冗长的报告书自动结构化，让 AI 能够高效理解和处理大型文档。

[English](#) | [简体中文](#)

---

## 🎯 核心价值

在处理大型报告、技术文档时，你是否遇到过这些问题：

❌ **文档太长** - 九万字的环评报告，AI 根本处理不了  
❌ **结构混乱** - 几百页的内容，不知道从哪开始分析  
❌ **成本太高** - 全文喂给 AI，Token 消耗惊人  
❌ **效果不佳** - AI 在长文本中容易遗漏关键信息  

### ✅ TOC Parser 的解决方案

```
📄 大型文档 (90,000字)
    ↓
📋 自动提取目录结构
    ↓
🗂️ 结构化JSON输出
    ↓
🤖 按章节精准投喂AI
```

**核心优势：**
- 🚀 **提高效率**：将 90,000 字文档分解为 50+ 个可管理的章节
- 💰 **降低成本**：按需处理，Token 使用量减少 80%
- 🎯 **提升精度**：AI 专注于特定章节，回答更准确
- 📊 **完整洞察**：保留文档层级结构，不丢失上下文

---

## 🌟 应用场景

### 1️⃣ **AI 文档问答系统**
```python
# 提取目录 → 用户提问 → 定位相关章节 → AI 精准回答
parser = TOCParser("技术报告.docx")
toc = parser.parse()

# 用户问："第三章讲了什么？"
chapter_3 = find_chapter(toc, "3")
response = ai.ask(chapter_3['content'])
```

**适用于：**
- 📖 法律合同分析
- 🏗️ 工程技术报告
- 📊 研究论文检索
- 📋 企业规章制度查询

### 2️⃣ **大文档自动摘要**
```python
# 逐章生成摘要，最后汇总
for chapter in toc['chapters']:
    summary = ai.summarize(chapter['content'])
    chapter['summary'] = summary

# 生成完整报告摘要
full_summary = ai.merge_summaries(all_summaries)
```

**适用于：**
- 📝 会议纪要快速生成
- 📑 学术论文综述
- 📊 市场调研报告提炼
- 🔍 尽职调查文档分析

### 3️⃣ **文档智能对比**
```python
# 对比新旧版本变化
old_toc = TOCParser("2023版报告.docx").parse()
new_toc = TOCParser("2024版报告.docx").parse()

changes = compare_structure(old_toc, new_toc)
# → "第3.2节新增，第5.1节删除"
```

**适用于：**
- 📄 合同版本变更追踪
- 📚 标准文档修订对比
- 🔄 SOP 流程更新检查

### 4️⃣ **知识库构建**
```python
# 批量处理企业文档库
for doc in document_library:
    toc = TOCParser(doc).parse()
    knowledge_base.index(toc)

# 支持章节级别的语义搜索
results = knowledge_base.search("环境保护措施")
```

**适用于：**
- 🏢 企业知识管理系统
- 📚 数字图书馆建设
- 🎓 在线学习平台
- 🔬 科研资料管理

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Tsetmefree/toc-parser.git
cd toc-parser



**依赖包：**
```
python-docx>=0.8.11
pdfplumber>=0.9.0
pywin32>=305  # 可选，支持DOC格式（仅Windows）
```

### 基础使用

```python
from toc_parser import TOCParser

# 1. 解析文档
parser = TOCParser("环评报告.docx")
result = parser.parse()

# 2. 查看结构
parser.print_tree()

# 3. 保存为JSON
parser.save_json("output.json")
```

### 命令行使用

```bash
# 解析并显示
python toc_parser.py 报告书.docx

# 保存为JSON
python toc_parser.py 报告书.docx --output result.json

# 批量处理
python toc_parser.py *.docx --batch
```

---

## 📊 输出格式

### 树形结构（用于展示）
```
📁 1 总则 (第1页)
  📄 1.1 编制依据 (第1页)
  📄 1.2 环境功能区划 (第4页)
  📄 1.3 评价标准 (第5页)
📁 2 工程概况与工程分析 (第17页)
  📄 2.1 工程地理位置 (第17页)
  📄 2.2 项目建设方案比选 (第17页)
```

### JSON结构（用于程序处理）
```json
{
  "success": true,
  "metadata": {
    "filename": "报告书.docx",
    "total_sections": 58,
    "level_1_count": 8,
    "level_2_count": 50
  },
  "toc": [
    {
      "number": "1",
      "title": "总则",
      "page": 1,
      "level": 1,
      "children": [
        {
          "number": "1.1",
          "title": "编制依据",
          "page": 1,
          "level": 2,
          "children": []
        }
      ]
    }
  ],
  "flat_list": [
    {"number": "1", "title": "总则", "page": 1, "level": 1},
    {"number": "1.1", "title": "编制依据", "page": 1, "level": 2}
  ]
}
```

---

## 🎨 特性亮点

### ✨ 智能识别
- 🔢 **多种编号格式**：支持 `1.` `1.1` `1.1.1` 等多级编号
- 📐 **灵活分隔符**：自动识别 Tab、多空格等分隔方式
- 🎯 **精准定位**：自动检测"目录"起止位置

### 📁 格式支持
| 格式 | 支持程度 | 说明 |
|------|---------|------|
| `.docx` | ✅ 完整支持 | Word 2007+ 格式 |
| `.doc` | ✅ 支持 | 需要 Windows + Office |
| `.pdf` | ✅ 完整支持 | 基于文本的 PDF |

### 🛡️ 鲁棒性
- ✅ 自动过滤临时文件（`~$xxx.docx`）
- ✅ 异常处理完善，不会中断批量任务
- ✅ 支持不规范目录格式的容错处理

---

## 💡 进阶用法

### 与 LangChain 集成

```python
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS

# 1. 提取目录
toc = TOCParser("report.docx").parse()

# 2. 按章节构建向量库
for chapter in toc['flat_list']:
    text = extract_chapter_content(chapter)
    chunks = text_splitter.split_text(text)
    
    # 添加元数据
    metadata = {
        "chapter": chapter['number'],
        "title": chapter['title'],
        "page": chapter['page']
    }
    
    vectorstore.add_texts(chunks, metadatas=[metadata]*len(chunks))

# 3. 章节级别的检索增强
query = "环境保护措施有哪些？"
docs = vectorstore.similarity_search(query, k=3)
```

### 与 GPT API 配合

```python
import openai

def chunk_analysis(toc_json, model="gpt-4"):
    """逐章分析，避免超出 Token 限制"""
    
    results = []
    for chapter in toc_json['toc']:
        prompt = f"""
        请分析以下章节内容：
        章节：{chapter['number']} {chapter['title']}
        页码：第{chapter['page']}页
        
        内容：{chapter['content']}
        
        请总结要点：
        """
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        results.append({
            "chapter": chapter['number'],
            "summary": response.choices[0].message.content
        })
    
    return results
```

---

## 🔧 配置选项

创建 `config.json` 自定义识别规则：

```json
{
  "toc_patterns": [
    "^(\\d+)\\.\\s+([^\\t]+?)\\s+(\\d+)$",
    "^(\\d+\\.\\d+)\\s+([^\\t]+?)\\s+(\\d+)$"
  ],
  "toc_start_keywords": ["目录", "目  录", "CONTENTS"],
  "toc_end_keywords": ["附图", "附件", "附表", "正文"],
  "ignore_files": ["~$*", ".*"],
  "output_format": "json"
}
```

---



## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 提交 Bug
- 请在 [Issues](https://github.com/Tsetmefree/toc-parser/issues) 中详细描述问题
- 附上样本文档（脱敏后）和错误日志

### 功能建议
- 在 Issues 中打上 `enhancement` 标签
- 说明使用场景和期望效果

### Pull Request
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [python-docx](https://github.com/python-openxml/python-docx) - DOCX 文件处理
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF 文本提取
- 所有贡献者和使用者

---


## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 ⭐️ Star！

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/toc-parser&type=Date)](https://star-history.com/#yourusername/toc-parser&Date)

---

<div align="center">
Made with ❤️ by developers who hate reading long documents
</div>
