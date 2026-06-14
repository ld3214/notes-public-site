# ASIC/DV Job Notebook

这是 ASIC、Design Verification、UVM 项目和面试复盘笔记本。日常使用时先打开 [index.md](index.md)。

## 文件结构

| 路径 | 用途 |
| --- | --- |
| [index.md](index.md) | 总入口和复习路线 |
| [actual-interviews/](actual-interviews/README.md) | 自己真实被问到的问题，优先级最高 |
| [knowledge-base/](knowledge-base/README.md) | 系统知识正文：ASIC / DV / SV-UVM / Protocol |
| [question-bank/](question-bank/README.md) | 通用刷题表和网上面经 |
| [projects-hr/](projects-hr/README.md) | 项目 STAR、技术细节、HR/英文回答 |
| [company-sites.md](company-sites.md) | 投递公司和城市 site 清单，成都 site 单独标注 |
| [glossary.md](glossary.md) | 术语和缩写速查 |
| [inbox.md](inbox.md) | 还没分类的临时材料 |

## 记录规则

- 真实被问到的问题放 `actual-interviews/`，保留原始问法。
- 成体系知识点放 `knowledge-base/`，并加稳定 anchor。
- 可刷题的问法同步到 `question-bank/question-bank.md`。
- 项目经历、STAR、英文表达放 `projects-hr/`。
- 投递目标公司、城市 site、申请状态放 `company-sites.md`。
- 可复用术语补到 `glossary.md`。

## HTML 预览

在 PowerShell 里运行：

```powershell
.\view-notes-html.ps1
```

只生成不打开浏览器：

```powershell
.\view-notes-html.ps1 -NoOpen
```

生成内容在 `site/`，它是自动产物，不直接编辑。
