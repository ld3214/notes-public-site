"use strict";

const EXCLUDED_DIRS = new Set([".git", ".vscode", ".public-build", "site", "__pycache__", "node_modules"]);
const MARKDOWN_EXTENSIONS = [".md", ".markdown"];
const THEME_KEY = "obsidian-workbench-theme";

const state = {
  directoryHandle: null,
  files: [],
  activeFile: null,
  markdown: "",
  savedMarkdown: "",
  blocks: [],
  mode: "split",
  renderTimer: 0,
  draggedIndex: null,
};

const els = {
  body: document.documentElement,
  openFolderButton: document.getElementById("openFolderButton"),
  themeButton: document.getElementById("themeButton"),
  fileSearch: document.getElementById("fileSearch"),
  fileTree: document.getElementById("fileTree"),
  fileTitle: document.getElementById("fileTitle"),
  filePath: document.getElementById("filePath"),
  dirtyDot: document.getElementById("dirtyDot"),
  saveButton: document.getElementById("saveButton"),
  revertButton: document.getElementById("revertButton"),
  editorLayout: document.getElementById("editorLayout"),
  markdownEditor: document.getElementById("markdownEditor"),
  previewPane: document.getElementById("previewPane"),
  blocksPane: document.getElementById("blocksPane"),
  blockList: document.getElementById("blockList"),
  blockTemplate: document.getElementById("blockTemplate"),
  blockCount: document.getElementById("blockCount"),
  addBlockButton: document.getElementById("addBlockButton"),
  outlineList: document.getElementById("outlineList"),
  statFiles: document.getElementById("statFiles"),
  statBlocks: document.getElementById("statBlocks"),
  statChars: document.getElementById("statChars"),
  statusText: document.getElementById("statusText"),
  apiNotice: document.getElementById("apiNotice"),
};

init();

function init() {
  initTheme();
  initApiNotice();
  bindEvents();
  renderFileTree();
  setMarkdown("", { updateEditor: true });
  setStatus("Ready");
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "dark" || saved === "light") {
    els.body.dataset.theme = saved;
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    els.body.dataset.theme = "dark";
  }
}

function initApiNotice() {
  els.apiNotice.hidden = "showDirectoryPicker" in window;
  if (!("showDirectoryPicker" in window)) {
    els.openFolderButton.disabled = true;
  }
}

function bindEvents() {
  els.openFolderButton.addEventListener("click", openNotebookFolder);
  els.themeButton.addEventListener("click", toggleTheme);
  els.fileSearch.addEventListener("input", renderFileTree);
  els.saveButton.addEventListener("click", saveActiveFile);
  els.revertButton.addEventListener("click", revertActiveFile);
  els.addBlockButton.addEventListener("click", addBlock);

  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });

  els.markdownEditor.addEventListener("input", () => {
    state.markdown = els.markdownEditor.value;
    updateDirtyState();
    scheduleRender();
  });

  window.addEventListener("keydown", (event) => {
    const tag = document.activeElement ? document.activeElement.tagName : "";
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      if (state.activeFile) saveActiveFile();
    }
    if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey) {
      if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
        event.preventDefault();
        els.fileSearch.focus();
        els.fileSearch.select();
      }
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (!isDirty()) return;
    event.preventDefault();
    event.returnValue = "";
  });
}

async function openNotebookFolder() {
  if (!(await confirmDiscardChanges())) return;
  try {
    const directoryHandle = await window.showDirectoryPicker({
      id: "asic-dv-notes",
      mode: "readwrite",
    });
    state.directoryHandle = directoryHandle;
    setStatus("Scanning Markdown files...");
    state.files = await collectMarkdownFiles(directoryHandle);
    state.files.sort((a, b) => a.path.localeCompare(b.path, "zh-Hans-CN"));
    state.activeFile = null;
    state.savedMarkdown = "";
    setMarkdown("", { updateEditor: true });
    renderFileTree();
    updateStats();
    setStatus(`Loaded ${state.files.length} Markdown files`);
  } catch (error) {
    if (error && error.name === "AbortError") {
      setStatus("Folder selection canceled");
      return;
    }
    console.error(error);
    setStatus("Failed to open folder");
  }
}

async function collectMarkdownFiles(directoryHandle, basePath = "") {
  const found = [];
  for await (const [name, handle] of directoryHandle.entries()) {
    if (handle.kind === "directory") {
      if (!EXCLUDED_DIRS.has(name)) {
        const childPath = basePath ? `${basePath}/${name}` : name;
        found.push(...await collectMarkdownFiles(handle, childPath));
      }
      continue;
    }
    const lower = name.toLowerCase();
    if (!MARKDOWN_EXTENSIONS.some((ext) => lower.endsWith(ext))) continue;
    found.push({
      name,
      path: basePath ? `${basePath}/${name}` : name,
      handle,
    });
  }
  return found;
}

function renderFileTree() {
  els.fileTree.textContent = "";
  const query = normalizeSearch(els.fileSearch.value);
  const files = state.files.filter((file) => !query || normalizeSearch(file.path).includes(query));
  els.statFiles.textContent = String(state.files.length);

  if (!state.directoryHandle) {
    els.fileTree.appendChild(emptyNode("打开 notes 文件夹后，这里会显示 Markdown 文件树。"));
    return;
  }
  if (files.length === 0) {
    els.fileTree.appendChild(emptyNode("没有匹配的 Markdown 文件。"));
    return;
  }

  const tree = buildTree(files);
  appendTreeChildren(els.fileTree, tree, "");
}

function buildTree(files) {
  const root = { folders: new Map(), files: [] };
  files.forEach((file) => {
    const parts = file.path.split("/");
    let node = root;
    parts.slice(0, -1).forEach((part) => {
      if (!node.folders.has(part)) node.folders.set(part, { folders: new Map(), files: [] });
      node = node.folders.get(part);
    });
    node.files.push(file);
  });
  return root;
}

function appendTreeChildren(parent, node, pathPrefix) {
  Array.from(node.folders.entries())
    .sort(([a], [b]) => a.localeCompare(b, "zh-Hans-CN"))
    .forEach(([folderName, child]) => {
      const details = document.createElement("details");
      details.className = "tree-folder";
      details.open = true;
      const summary = document.createElement("summary");
      summary.textContent = folderName;
      const children = document.createElement("div");
      children.className = "tree-children";
      appendTreeChildren(children, child, pathPrefix ? `${pathPrefix}/${folderName}` : folderName);
      details.append(summary, children);
      parent.appendChild(details);
    });

  node.files
    .sort((a, b) => a.name.localeCompare(b.name, "zh-Hans-CN"))
    .forEach((file) => {
      const button = document.createElement("button");
      button.className = "file-button";
      if (state.activeFile && state.activeFile.path === file.path) button.classList.add("active");
      button.type = "button";
      button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v5h5"/></svg><span></span>`;
      button.querySelector("span").textContent = file.name;
      button.title = file.path;
      button.addEventListener("click", () => openFile(file));
      parent.appendChild(button);
    });
}

function emptyNode(text) {
  const node = document.createElement("div");
  node.className = "empty-tree";
  node.textContent = text;
  return node;
}

async function openFile(file) {
  if (!(await confirmDiscardChanges())) return;
  try {
    setStatus("Reading file...");
    const blob = await file.handle.getFile();
    const text = await blob.text();
    state.activeFile = file;
    state.savedMarkdown = normalizeLineEndings(text);
    setMarkdown(state.savedMarkdown, { updateEditor: true, reparseBlocks: true });
    els.fileTitle.textContent = file.name;
    els.filePath.textContent = file.path;
    renderFileTree();
    updateDirtyState();
    setStatus("File loaded");
  } catch (error) {
    console.error(error);
    setStatus("Failed to read file");
  }
}

async function saveActiveFile() {
  if (!state.activeFile) return;
  try {
    setStatus("Saving...");
    if (!(await verifyPermission(state.activeFile.handle, true))) {
      setStatus("Save permission was not granted");
      return;
    }
    const writable = await state.activeFile.handle.createWritable();
    await writable.write(state.markdown);
    await writable.close();
    state.savedMarkdown = state.markdown;
    updateDirtyState();
    setStatus("Saved");
  } catch (error) {
    console.error(error);
    setStatus("Failed to save file");
  }
}

async function verifyPermission(handle, readWrite) {
  const options = readWrite ? { mode: "readwrite" } : {};
  if ((await handle.queryPermission(options)) === "granted") return true;
  return (await handle.requestPermission(options)) === "granted";
}

async function revertActiveFile() {
  if (!state.activeFile || !isDirty()) return;
  if (!window.confirm("恢复到上次保存的内容？当前未保存修改会被丢弃。")) return;
  setMarkdown(state.savedMarkdown, { updateEditor: true, reparseBlocks: true });
  updateDirtyState();
  setStatus("Reverted");
}

async function confirmDiscardChanges() {
  if (!isDirty()) return true;
  return window.confirm("当前文件有未保存修改，继续会丢弃这些修改。");
}

function toggleTheme() {
  const next = els.body.dataset.theme === "dark" ? "light" : "dark";
  els.body.dataset.theme = next;
  localStorage.setItem(THEME_KEY, next);
}

function setMode(mode) {
  state.mode = mode;
  els.editorLayout.dataset.mode = mode;
  els.blocksPane.hidden = mode !== "blocks";
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  if (mode === "blocks") {
    state.blocks = parseBlocks(state.markdown);
    renderBlocks();
  }
}

function setMarkdown(text, options = {}) {
  state.markdown = normalizeLineEndings(text);
  if (options.updateEditor) {
    els.markdownEditor.value = state.markdown;
  }
  if (options.reparseBlocks || state.mode === "blocks") {
    state.blocks = parseBlocks(state.markdown);
    if (state.mode === "blocks") renderBlocks();
  }
  updateDirtyState();
  scheduleRender();
}

function scheduleRender() {
  window.clearTimeout(state.renderTimer);
  state.renderTimer = window.setTimeout(() => {
    renderPreview();
    renderOutline();
    updateStats();
  }, 80);
}

function renderPreview() {
  if (!state.markdown.trim()) {
    els.previewPane.innerHTML = `<div class="empty-pane">没有可预览的内容。</div>`;
    return;
  }
  els.previewPane.innerHTML = renderMarkdown(state.markdown);
}

function renderOutline() {
  els.outlineList.textContent = "";
  const headings = extractHeadings(state.markdown).filter((heading) => heading.level <= 3);
  if (headings.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-pane";
    empty.textContent = "No headings";
    els.outlineList.appendChild(empty);
    return;
  }
  headings.forEach((heading) => {
    const link = document.createElement("a");
    link.href = `#${heading.id}`;
    link.className = heading.level === 3 ? "outline-h3" : "";
    link.textContent = heading.text;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      setMode("preview");
      window.setTimeout(() => {
        const target = els.previewPane.querySelector(`#${CSS.escape(heading.id)}`);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 30);
    });
    els.outlineList.appendChild(link);
  });
}

function updateDirtyState() {
  const dirty = isDirty();
  els.dirtyDot.classList.toggle("active", dirty);
  els.saveButton.disabled = !state.activeFile || !dirty;
  els.revertButton.disabled = !state.activeFile || !dirty;
}

function updateStats() {
  const blocks = parseBlocks(state.markdown);
  els.statBlocks.textContent = String(blocks.length);
  els.statChars.textContent = String(state.markdown.length);
  els.blockCount.textContent = `${blocks.length} blocks`;
}

function isDirty() {
  return state.activeFile && state.markdown !== state.savedMarkdown;
}

function setStatus(text) {
  els.statusText.textContent = text;
}

function parseBlocks(markdown) {
  const lines = normalizeLineEndings(markdown).split("\n");
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    if (!lines[i].trim()) {
      i += 1;
      continue;
    }

    const line = lines[i];
    const trimmed = line.trim();

    if (/^(```|~~~)/.test(trimmed)) {
      const fence = trimmed.slice(0, 3);
      const start = i;
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith(fence)) i += 1;
      if (i < lines.length) i += 1;
      blocks.push(makeBlock(lines.slice(start, i).join("\n")));
      continue;
    }

    if (/^#{1,6}\s+/.test(line) || /^<a\s+id="[^"]+"\s*><\/a>\s*$/i.test(trimmed)) {
      blocks.push(makeBlock(line));
      i += 1;
      continue;
    }

    if (isTableStart(lines, i)) {
      const start = i;
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) i += 1;
      blocks.push(makeBlock(lines.slice(start, i).join("\n")));
      continue;
    }

    if (isListStart(line)) {
      const start = i;
      i += 1;
      while (i < lines.length) {
        if (!lines[i].trim()) break;
        if (isListStart(lines[i])) break;
        if (/^#{1,6}\s+/.test(lines[i])) break;
        i += 1;
      }
      blocks.push(makeBlock(lines.slice(start, i).join("\n")));
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      const start = i;
      i += 1;
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) i += 1;
      blocks.push(makeBlock(lines.slice(start, i).join("\n")));
      continue;
    }

    const start = i;
    i += 1;
    while (i < lines.length) {
      if (!lines[i].trim()) break;
      if (/^(```|~~~)/.test(lines[i].trim())) break;
      if (/^#{1,6}\s+/.test(lines[i])) break;
      if (isListStart(lines[i])) break;
      if (isTableStart(lines, i)) break;
      i += 1;
    }
    blocks.push(makeBlock(lines.slice(start, i).join("\n")));
  }
  return blocks;
}

function makeBlock(raw) {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()),
    raw: raw.trimEnd(),
    type: classifyBlock(raw),
  };
}

function classifyBlock(raw) {
  const first = raw.trimStart().split("\n")[0] || "";
  if (/^(```|~~~)/.test(first)) return "code";
  if (/^#{1}\s+/.test(first)) return "h1";
  if (/^#{2}\s+/.test(first)) return "h2";
  if (/^#{3}\s+/.test(first)) return "h3";
  if (/^#{4,6}\s+/.test(first)) return "heading";
  if (/^<a\s+id="[^"]+"\s*><\/a>\s*$/i.test(first)) return "anchor";
  if (/^\s*[-*+]\s+/.test(first)) return "bullet";
  if (/^\s*\d+[.)]\s+/.test(first)) return "ordered";
  if (/^\s*>\s?/.test(first)) return "quote";
  if (raw.includes("\n") && isTableStart(raw.split("\n"), 0)) return "table";
  return "paragraph";
}

function renderBlocks() {
  els.blockList.textContent = "";
  if (state.blocks.length === 0) {
    els.blockList.appendChild(emptyNode("当前文件还没有可整理的块。"));
    updateStats();
    return;
  }
  state.blocks.forEach((block, index) => {
    const node = els.blockTemplate.content.firstElementChild.cloneNode(true);
    const typeNode = node.querySelector(".block-type");
    const editor = node.querySelector(".block-editor");
    typeNode.textContent = block.type;
    node.dataset.index = String(index);
    editor.value = block.raw;
    resizeBlockEditor(editor);

    node.addEventListener("dragstart", (event) => {
      state.draggedIndex = index;
      node.classList.add("dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(index));
    });
    node.addEventListener("dragend", () => {
      node.classList.remove("dragging");
      state.draggedIndex = null;
      clearDropTargets();
    });
    node.addEventListener("dragover", (event) => {
      event.preventDefault();
      node.classList.add("drop-target");
    });
    node.addEventListener("dragleave", () => node.classList.remove("drop-target"));
    node.addEventListener("drop", (event) => {
      event.preventDefault();
      const from = state.draggedIndex;
      const to = Number(node.dataset.index);
      clearDropTargets();
      if (Number.isInteger(from) && from !== to) moveBlock(from, to);
    });

    editor.addEventListener("input", () => {
      block.raw = editor.value;
      block.type = classifyBlock(block.raw);
      typeNode.textContent = block.type;
      syncFromBlocks({ render: false });
      resizeBlockEditor(editor);
      updateFormatButtons(node, block);
    });

    node.querySelectorAll("[data-format]").forEach((button) => {
      button.addEventListener("click", () => {
        convertBlock(block, button.dataset.format);
        syncFromBlocks({ render: true });
      });
    });
    node.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.action;
        if (action === "up") moveBlock(index, Math.max(index - 1, 0));
        if (action === "down") moveBlock(index, Math.min(index + 1, state.blocks.length - 1));
        if (action === "delete") deleteBlock(index);
      });
    });

    updateFormatButtons(node, block);
    els.blockList.appendChild(node);
  });
  updateStats();
}

function clearDropTargets() {
  els.blockList.querySelectorAll(".drop-target").forEach((node) => node.classList.remove("drop-target"));
}

function updateFormatButtons(node, block) {
  node.querySelectorAll("[data-format]").forEach((button) => {
    button.classList.toggle("active", button.dataset.format === block.type);
  });
}

function resizeBlockEditor(editor) {
  editor.style.height = "auto";
  editor.style.height = `${Math.max(84, editor.scrollHeight + 2)}px`;
}

function moveBlock(from, to) {
  if (from === to) return;
  const [block] = state.blocks.splice(from, 1);
  state.blocks.splice(to, 0, block);
  syncFromBlocks({ render: true });
  setStatus("Block moved");
}

function deleteBlock(index) {
  state.blocks.splice(index, 1);
  syncFromBlocks({ render: true });
  setStatus("Block removed");
}

function addBlock() {
  state.blocks.push(makeBlock("新段落"));
  syncFromBlocks({ render: true });
  setStatus("Block added");
}

function syncFromBlocks(options = {}) {
  const text = serializeBlocks(state.blocks);
  state.markdown = text;
  els.markdownEditor.value = text;
  updateDirtyState();
  scheduleRender();
  if (options.render) renderBlocks();
}

function serializeBlocks(blocks) {
  let orderedRun = 1;
  return blocks.map((block, index) => {
    const previous = blocks[index - 1];
    if (!previous || block.type !== "ordered" || previous.type !== "ordered") orderedRun = 1;
    const text = formattedBlockRaw(block, orderedRun);
    if (block.type === "ordered") orderedRun += 1;
    return text;
  }).reduce((output, text, index) => {
    if (index === 0) return text;
    const previous = blocks[index - 1];
    const current = blocks[index];
    const tightList = isListType(previous.type) && isListType(current.type);
    return `${output}${tightList ? "\n" : "\n\n"}${text}`;
  }, "");
}

function formattedBlockRaw(block, orderedNumber) {
  if (block.type !== "ordered") return block.raw.trimEnd();
  return block.raw.replace(/^(\s*)\d+[.)](\s+)/, `$1${orderedNumber}.$2`).trimEnd();
}

function convertBlock(block, format) {
  const text = plainBlockText(block).trim();
  if (!text) {
    block.raw = "";
    block.type = "paragraph";
    return;
  }
  if (format === "paragraph") block.raw = text;
  if (format === "bullet") block.raw = `- ${indentContinuation(text, "  ")}`;
  if (format === "ordered") block.raw = `1. ${indentContinuation(text, "   ")}`;
  if (format === "quote") block.raw = text.split("\n").map((line) => `> ${line}`).join("\n");
  if (format === "h2") block.raw = `## ${text.split("\n")[0]}`;
  if (format === "h3") block.raw = `### ${text.split("\n")[0]}`;
  block.type = classifyBlock(block.raw);
}

function plainBlockText(block) {
  const raw = block.raw.trim();
  if (block.type === "h1" || block.type === "h2" || block.type === "h3" || block.type === "heading") {
    return raw.replace(/^#{1,6}\s+/, "");
  }
  if (block.type === "bullet") {
    return raw.replace(/^\s*[-*+]\s+/, "").replace(/\n\s{2}/g, "\n");
  }
  if (block.type === "ordered") {
    return raw.replace(/^\s*\d+[.)]\s+/, "").replace(/\n\s{3}/g, "\n");
  }
  if (block.type === "quote") {
    return raw.split("\n").map((line) => line.replace(/^\s*>\s?/, "")).join("\n");
  }
  return raw;
}

function indentContinuation(text, spaces) {
  return text.split("\n").map((line, index) => index === 0 ? line : `${spaces}${line}`).join("\n");
}

function isListType(type) {
  return type === "bullet" || type === "ordered";
}

function renderMarkdown(markdown) {
  const lines = normalizeLineEndings(markdown).split("\n");
  const headings = new Map();
  const htmlParts = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) {
      i += 1;
      continue;
    }

    const anchor = trimmed.match(/^<a\s+id="([^"]+)"\s*><\/a>\s*$/i);
    if (anchor) {
      htmlParts.push(`<a id="${escapeAttr(anchor[1])}"></a>`);
      i += 1;
      continue;
    }

    if (/^(```|~~~)/.test(trimmed)) {
      const fence = trimmed.slice(0, 3);
      const language = trimmed.slice(3).trim();
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith(fence)) {
        code.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      htmlParts.push(`<pre><code data-lang="${escapeAttr(language)}">${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const text = stripInlineMarkdown(heading[2]);
      const id = uniqueSlug(text, headings);
      htmlParts.push(`<h${level} id="${escapeAttr(id)}">${formatInline(heading[2])}</h${level}>`);
      i += 1;
      continue;
    }

    if (isTableStart(lines, i)) {
      const tableLines = [lines[i], lines[i + 1]];
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        tableLines.push(lines[i]);
        i += 1;
      }
      htmlParts.push(renderTable(tableLines));
      continue;
    }

    if (isListStart(line)) {
      const ordered = /^\s*\d+[.)]\s+/.test(line);
      const tag = ordered ? "ol" : "ul";
      const items = [];
      while (i < lines.length && lines[i].trim()) {
        if (!isListStart(lines[i])) break;
        const itemLines = [lines[i].replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "")];
        i += 1;
        while (i < lines.length && lines[i].trim() && !isListStart(lines[i])) {
          itemLines.push(lines[i].replace(/^\s{2,4}/, ""));
          i += 1;
        }
        items.push(`<li>${formatInline(itemLines.join("\n"))}</li>`);
      }
      htmlParts.push(`<${tag}>${items.join("")}</${tag}>`);
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      const quote = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        quote.push(lines[i].replace(/^\s*>\s?/, ""));
        i += 1;
      }
      htmlParts.push(`<blockquote>${renderMarkdown(quote.join("\n"))}</blockquote>`);
      continue;
    }

    const paragraph = [line];
    i += 1;
    while (i < lines.length && lines[i].trim() && !isSpecialMarkdownStart(lines, i)) {
      paragraph.push(lines[i]);
      i += 1;
    }
    htmlParts.push(`<p>${formatInline(paragraph.join(" "))}</p>`);
  }

  return htmlParts.join("\n");
}

function renderTable(lines) {
  const rows = lines.map((line) => splitTableRow(line));
  const header = rows[0] || [];
  const body = rows.slice(2);
  const headHtml = `<thead><tr>${header.map((cell) => `<th>${formatInline(cell.trim())}</th>`).join("")}</tr></thead>`;
  const bodyHtml = `<tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${formatInline(cell.trim())}</td>`).join("")}</tr>`).join("")}</tbody>`;
  return `<table>${headHtml}${bodyHtml}</table>`;
}

function splitTableRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|");
}

function extractHeadings(markdown) {
  const counts = new Map();
  return normalizeLineEndings(markdown).split("\n").flatMap((line) => {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (!match) return [];
    const text = stripInlineMarkdown(match[2]);
    return [{ level: match[1].length, text, id: uniqueSlug(text, counts) }];
  });
}

function uniqueSlug(text, counts) {
  const base = slugify(text) || "section";
  const count = counts.get(base) || 0;
  counts.set(base, count + 1);
  return count === 0 ? base : `${base}-${count}`;
}

function slugify(text) {
  return stripInlineMarkdown(text)
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-");
}

function isSpecialMarkdownStart(lines, index) {
  const line = lines[index] || "";
  return /^(```|~~~)/.test(line.trim()) ||
    /^#{1,6}\s+/.test(line) ||
    /^<a\s+id="[^"]+"\s*><\/a>\s*$/i.test(line.trim()) ||
    isListStart(line) ||
    /^\s*>\s?/.test(line) ||
    isTableStart(lines, index);
}

function isListStart(line) {
  return /^\s*(?:[-*+]\s+|\d+[.)]\s+)/.test(line);
}

function isTableStart(lines, index) {
  const current = lines[index] || "";
  const next = lines[index + 1] || "";
  return current.includes("|") && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(next);
}

function formatInline(text) {
  const placeholders = [];
  const token = (html) => {
    const key = `\u0000${placeholders.length}\u0000`;
    placeholders.push(html);
    return key;
  };

  let working = text.replace(/`([^`]+)`/g, (_match, code) => token(`<code>${escapeHtml(code)}</code>`));
  working = escapeHtml(working);
  working = working.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_match, alt, src) => {
    return `<img src="${escapeAttr(src)}" alt="${escapeAttr(alt)}">`;
  });
  working = working.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, href) => {
    return `<a href="${escapeAttr(href)}">${label}</a>`;
  });
  working = working.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  working = working.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  placeholders.forEach((html, index) => {
    working = working.replaceAll(`\u0000${index}\u0000`, html);
  });
  return working.replace(/\n/g, "<br>");
}

function stripInlineMarkdown(text) {
  return text
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_~]/g, "")
    .replace(/<[^>]+>/g, "")
    .trim();
}

function normalizeLineEndings(text) {
  return String(text || "").replace(/\r\n?/g, "\n");
}

function normalizeSearch(text) {
  return String(text || "").trim().toLowerCase();
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(text) {
  return escapeHtml(text).replace(/`/g, "&#096;");
}
