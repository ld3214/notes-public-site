# Obsidian Workbench

这是给当前 ASIC/DV Markdown 笔记准备的本地工作台。它不会替代 `tools/build_html.py` 生成的 `site/`，也不会把笔记上传到外部服务。

## 启动

在这个目录启动一个本地静态服务：

```powershell
cd C:\Users\28724\Desktop\notes\obsidian-workbench
.\serve.ps1
```

然后打开：

```text
http://127.0.0.1:4173/
```

## 用法

1. 点击 `打开笔记文件夹`。
2. 选择 `C:\Users\28724\Desktop\notes`。
3. 在左侧文件树打开 `.md` 文件。
4. 用 `源码` / `预览` / `分屏` / `整理` 切换视图。
5. 在 `整理` 里拖动块，或把块切成段落、无序要点、有序要点、引用、H2、H3。
6. 点击保存按钮写回原 Markdown 文件。

## 注意

- 需要新版 Chrome 或 Edge，因为它依赖浏览器的 File System Access API。
- `site/`、`.git/`、`.public-build/` 等生成或工程目录会被自动忽略。
- 保存前可以用恢复按钮回到上次保存内容。
