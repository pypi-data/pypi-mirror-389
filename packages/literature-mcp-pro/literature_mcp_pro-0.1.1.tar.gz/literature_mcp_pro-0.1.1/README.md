# 🚀 Literature MCP Pro

<div align="center">

**功能更强大的学术文献管理 MCP 服务器**

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://modelcontextprotocol.io)

</div>

## ✨ 核心特性

### 📚 多数据源集成
- **PubMed** - 生物医学文献
- **ArXiv** - 预印本论文
- **Europe PMC** - 欧洲生命科学文献
- **CrossRef** - 跨学科文献元数据
- **Google Scholar** (可选) - 广泛的学术搜索

### 🤖 AI 驱动的智能分析
- 📝 **智能摘要** - 自动生成文献摘要
- 🎯 **研究趋势分析** - 识别研究热点和趋势
- ⭐ **论文质量评估** - 多维度质量打分
- 💡 **相关文献推荐** - 基于内容和引用的智能推荐
- 🔍 **语义搜索** - 基于内容理解的深度搜索

### 📊 可视化与分析
- 🕸️ **引用网络图** - 可视化文献引用关系
- 📈 **趋势时间线** - 研究领域发展趋势
- 🗺️ **主题地图** - 主题分布和关联
- 📉 **统计分析** - 发表量、引用量等统计

### 🗄️ 文献库管理
- 📁 **本地文献库** - SQLite 数据库存储
- 🏷️ **标签系统** - 自定义标签分类
- 📝 **笔记功能** - 为文献添加笔记
- 🔄 **同步管理** - 文献状态跟踪

### 📤 多格式导出
- BibTeX
- EndNote (XML)
- RIS
- CSV
- JSON
- Markdown

### 🔔 实时监控
- 📬 **关键词监控** - 跟踪特定主题
- 🆕 **新文献推送** - 自动发现新发表文献
- 📊 **自定义提醒** - 基于条件的提醒

## 🏗️ 项目架构（现状）

```
literature_mcp_pro/
├─ main.py                         # MCP STDIO 入口（优先尝试 FastMCP）
├─ requirements.txt
├─ pyproject.toml
├─ .cloudmcp.yml
├─ tests/
│  ├─ run_unit_tests.py            # 轻量测试运行器
│  ├─ test_ai.py
│  ├─ test_services.py
│  └─ test_tools.py
└─ literature_mcp_pro/
  ├─ __init__.py
  ├─ config.py
  ├─ models/__init__.py
  ├─ ai/
  │  ├─ summarizer.py
  │  ├─ analyzer.py
  │  ├─ recommender.py
  │  └─ semantic_search.py
  ├─ tools/
  │  ├─ __init__.py               # 从 ai 暴露 Summarizer/TrendAnalyzer/Recommender
  │  ├─ analysis.py               # 包装 summarize/analyze_trends/recommend
  │  └─ search.py                 # 聚合 pubmed/arxiv/crossref + 语义
  └─ connectors/
    ├─ pubmed.py
    ├─ arxiv.py
    ├─ crossref.py
    ├─ europepmc.py              # 禁用（占位类）
    └─ scholar.py                # 禁用（占位类）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，添加必要的 API 密钥
```

### 3. 初始化数据库

```bash
uv run python scripts/setup_db.py
```

### 4. 启动服务器（本地）

```bash
# Windows（PowerShell）
python main.py
```

### 5. 在 VS Code Copilot Chat 中注册为 MCP 工具（实验特性）

有两种常见方式将本项目注册为 MCP 服务器（STDIO）：

方式 A：通过命令面板
- 打开 VS Code，按 Ctrl+Shift+P，输入并执行：Copilot: Add MCP Server（或类似“添加 MCP 服务器”的命令）。
- 按提示填写：
  - Label（名称）：Literature MCP Pro
  - Type（类型）：stdio
  - Command（命令）：你的 Python 可执行文件路径（例如：D:/GJ/python-3.13/python.exe）
  - Args（参数）：["${workspaceFolder}/main.py"]
  - Env（环境变量，建议）：{"PYTHONUNBUFFERED":"1"}
  - Auto Start：启用

方式 B：在 Settings(JSON) 手动添加（不同版本的 VS Code/Copilot 可能存在键名差异，请以实际为准）

```jsonc
// settings.json 片段（示例）
{
  "github.copilot.chat.modelContextProtocol.servers": [
    {
      "id": "literature-mcp-pro",
      "label": "Literature MCP Pro",
      "type": "stdio",
      "command": "D:/GJ/python-3.13/python.exe",
      "args": ["${workspaceFolder}/main.py"],
      "env": { "PYTHONUNBUFFERED": "1" },
      "autoStart": true
    }
  ]
}
```

提示：
- 需先安装依赖：`pip install -r requirements.txt`（已包含 fastmcp/httpx/pydantic 等）。
- 本项目在运行时会优先使用 FastMCP 提供标准 MCP 协议；若失败，会回退到最简 STDIO 循环（仅用于本地自测，不保证兼容所有 MCP 客户端）。
- 首次连接时，Copilot 可能会提示你授权该 MCP 服务器。

## 🛠️ 可用工具（当前实现）

以下工具在 MCP 中可调用（由 `main.py` 注册）：
- `search_literature`：多源文献搜索（pubmed / arxiv / crossref / semantic）
- `summarize_article`：对单篇文章进行简要摘要
- `analyze_trends`：基于多篇文章的趋势关键词统计
- `recommend_articles`：按引用量（简单规则）推荐文章

## 📖 使用示例

### 搜索文献

```python
# 在 Claude 中使用
"搜索关于机器学习在医学影像中应用的最新文献"

// 工具调用: search_literature（在 Copilot Chat 中由模型触发，或你可显式说明参数）
{
  "query": "machine learning medical imaging",
  "sources": ["pubmed", "arxiv", "semantic"],
  "max_results": 10
}
```

### AI 分析

```python
"分析这篇论文的质量和影响力"

// 工具调用: summarize_article
{
  "id": "id-1",
  "title": "Advances in ML for Medical Imaging",
  "abstract": "...",
  "source": "pubmed"
}
```

### 趋势与推荐

```python
"生成这个主题的引用网络图"

// 工具调用: analyze_trends
{
  "articles": [
    {"id": "1", "title": "Deep Learning in Medicine", "abstract": "deep learning applications", "source": "pubmed"},
    {"id": "2", "title": "Deep Learning for Images", "abstract": "deep image deep", "source": "arxiv"}
  ]
}

// 工具调用: recommend_articles
{
  "articles": [
    {"id": "1", "title": "A", "citation_count": 5, "source": "pubmed"},
    {"id": "2", "title": "B", "citation_count": 20, "source": "pubmed"}
  ],
  "top_k": 2
}
```

## 🔧 配置选项（节选）

更多详见 `literature_mcp_pro/config.py`：

| 配置项 | 说明 | 示例/默认 |
|--------|------|-----------|
| `PUBMED_BASE_URL` | NCBI eutils 基础地址 | https://eutils.ncbi.nlm.nih.gov/entrez/eutils |
| `ARXIV_BASE_URL` | arXiv API 基础地址 | https://export.arxiv.org/api |
| `CROSSREF_BASE_URL` | CrossRef API 基础地址 | https://api.crossref.org |
| `REQUEST_TIMEOUT` | 请求超时（秒） | 15 |
| `USER_AGENT` | HTTP UA | Literature-MCP-Pro/1.0 |

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

MIT License

## 🙏 致谢

注意：README 中未勾选的扩展特性（如可视化/数据库/导出/监控等）目前为规划项，或以占位实现存在，后续版本逐步补全。

---

<div align="center">
Made with ❤️ for researchers worldwide
</div>
