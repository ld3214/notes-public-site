from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

try:
    import markdown
except ModuleNotFoundError as exc:
    raise SystemExit("Missing Python package: markdown. Install it with: python -m pip install markdown") from exc

try:
    from pygments.formatters import HtmlFormatter
except ModuleNotFoundError:
    HtmlFormatter = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "site"
SKIP_DIRS = {".git", ".vscode", "site", ".public-build", "__pycache__", "obsidian-workbench"}
ASSET_SUFFIXES = {
    ".apng",
    ".avif",
    ".bmp",
    ".gif",
    ".html",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
}
PYGMENTS_STYLE = "github-dark"
FENCE_RE = re.compile(r"(?ms)^(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n]*)\n.*?^\s*(?P=fence)[ \t]*$")
LANGUAGE_LABELS = {
    "bash": "Bash",
    "c": "C",
    "cpp": "C++",
    "json": "JSON",
    "make": "Make",
    "python": "Python",
    "sv": "SystemVerilog",
    "systemverilog": "SystemVerilog",
    "tcl": "Tcl",
    "text": "Text",
    "verilog": "Verilog",
    "vhdl": "VHDL",
}


@dataclass(frozen=True)
class Page:
    source: Path
    source_rel: Path
    output_rel: Path
    title: str
    section: str


def posix(path: Path) -> str:
    return path.as_posix()


def is_external_url(url: str) -> bool:
    lowered = url.lower()
    return (
        not url
        or lowered.startswith("#")
        or lowered.startswith(("http://", "https://", "mailto:", "tel:", "data:"))
    )


def output_path_for(source_rel: Path) -> Path:
    name = source_rel.name.lower()
    if name == "readme.md" and source_rel.parent != Path("."):
        return source_rel.parent / "index.html"
    if name == "readme.md":
        return Path("README.html")
    if name == "index.md":
        return source_rel.with_name("index.html")
    return source_rel.with_suffix(".html")


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return any(part in SKIP_DIRS for part in rel.parts)


def iter_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if path.is_file() and not should_skip(path)
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def title_from_markdown(path: Path) -> str:
    text = read_text(path)
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return re.sub(r"<[^>]+>|[`*_]", "", match.group(1)).strip()
    rel = path.relative_to(ROOT)
    return rel.stem.replace("-", " ").replace("_", " ").title()


def section_for(source_rel: Path) -> str:
    if len(source_rel.parts) == 1:
        return "Notebook"
    first = source_rel.parts[0]
    labels = {
        "actual-interviews": "Actual Interviews",
        "knowledge-base": "Knowledge Base",
        "projects-hr": "Projects / HR",
        "question-bank": "Question Bank",
        "templates": "Templates",
    }
    return labels.get(first, first.replace("-", " ").title())


def page_sort_key(page: Page) -> tuple[int, str, str]:
    section_order = {
        "Notebook": 0,
        "Actual Interviews": 1,
        "Knowledge Base": 2,
        "Question Bank": 3,
        "Projects / HR": 4,
        "Templates": 5,
    }
    root_order = {
        "index.md": 0,
        "README.md": 1,
        "inbox.md": 2,
        "glossary.md": 3,
    }
    root_rank = root_order.get(posix(page.source_rel), 20)
    return (section_order.get(page.section, 50), f"{root_rank:02d}", posix(page.source_rel))


def relative_url(from_output: Path, to_output: Path) -> str:
    start = posix(from_output.parent) if from_output.parent != Path(".") else "."
    rel = posixpath.relpath(posix(to_output), start=start)
    return quote(rel, safe="/#.-_%")


def root_prefix(from_output: Path) -> str:
    if from_output.parent == Path("."):
        return ""
    depth = len(from_output.parent.parts)
    return "../" * depth


def build_pages(markdown_files: list[Path]) -> list[Page]:
    pages = []
    for source in markdown_files:
        source_rel = source.relative_to(ROOT)
        pages.append(
            Page(
                source=source,
                source_rel=source_rel,
                output_rel=output_path_for(source_rel),
                title=title_from_markdown(source),
                section=section_for(source_rel),
            )
        )
    return sorted(pages, key=page_sort_key)


def rewrite_local_href(
    href: str,
    source_rel: Path,
    output_rel: Path,
    md_to_html: dict[Path, Path],
) -> str:
    if is_external_url(href):
        return href

    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return href

    raw_path = unquote(parsed.path)
    if not raw_path:
        return href

    target_md: Path | None = None
    raw_parts = [part for part in raw_path.split("/") if part]
    raw_path_obj = Path(*raw_parts) if raw_parts else Path(".")

    if raw_path.endswith(".md"):
        resolved = (ROOT / source_rel.parent / raw_path_obj).resolve()
        try:
            target_md = resolved.relative_to(ROOT)
        except ValueError:
            return href
    elif raw_path.endswith("/"):
        candidate = source_rel.parent / raw_path_obj / "README.md"
        resolved = (ROOT / candidate).resolve()
        if resolved.exists() and ROOT in resolved.parents:
            target_md = resolved.relative_to(ROOT)

    if target_md is None or target_md not in md_to_html:
        return href

    rewritten_path = relative_url(output_rel, md_to_html[target_md])
    return urlunsplit(("", "", rewritten_path, parsed.query, parsed.fragment))


def rewrite_links(
    body_html: str,
    source_rel: Path,
    output_rel: Path,
    md_to_html: dict[Path, Path],
) -> str:
    def replace(match: re.Match[str]) -> str:
        attr, quote_char, value = match.groups()
        if attr != "href":
            return match.group(0)
        rewritten = rewrite_local_href(value, source_rel, output_rel, md_to_html)
        return f'{attr}={quote_char}{html.escape(rewritten, quote=True)}{quote_char}'

    return re.sub(r'\b(href|src)=(["\'])(.*?)\2', replace, body_html)


def display_language(language: str) -> str:
    normalized = language.strip().lower().lstrip(".")
    if not normalized:
        return "Code"
    return LANGUAGE_LABELS.get(normalized, normalized.replace("-", " ").title())


def fenced_code_languages(text: str) -> list[str]:
    languages: list[str] = []
    for match in FENCE_RE.finditer(text):
        info = match.group("info").strip()
        language = info.split()[0].lstrip(".") if info else ""
        languages.append(display_language(language))
    return languages


def annotate_code_blocks(body_html: str, languages: list[str]) -> str:
    language_iter = iter(languages)
    skip_next_pre = False

    def next_language() -> str:
        return next(language_iter, "Code")

    def replace(match: re.Match[str]) -> str:
        nonlocal skip_next_pre
        original = match.group(0)
        if original.startswith('<div class="codehilite"'):
            skip_next_pre = True
            return original[:-1] + f' data-lang="{html.escape(next_language(), quote=True)}">'
        if original.startswith("<pre"):
            if skip_next_pre:
                skip_next_pre = False
                return original
            return original[:-1] + f' data-lang="{html.escape(next_language(), quote=True)}">'
        return original

    return re.sub(r'<div class="codehilite">|<pre>', replace, body_html)


def pygments_css() -> str:
    if HtmlFormatter is None:
        return ""
    return HtmlFormatter(style=PYGMENTS_STYLE).get_style_defs(".codehilite")


def render_markdown(text: str) -> str:
    extensions = [
        "extra",
        "fenced_code",
        "sane_lists",
        "tables",
        "toc",
    ]
    extension_configs: dict[str, dict[str, object]] = {
        "toc": {
            "permalink": False,
        }
    }
    if HtmlFormatter is not None:
        extensions.append("codehilite")
        extension_configs["codehilite"] = {
            "guess_lang": False,
            "noclasses": False,
            "pygments_style": PYGMENTS_STYLE,
            "use_pygments": True,
        }

    return markdown.markdown(
        text,
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html5",
    )


def nav_html(pages: list[Page], current: Page) -> str:
    sections: dict[str, list[Page]] = {}
    for page in pages:
        sections.setdefault(page.section, []).append(page)

    parts: list[str] = []
    for section, section_pages in sections.items():
        parts.append(f'<div class="nav-section"><div class="nav-heading">{html.escape(section)}</div>')
        for page in section_pages:
            active = " active" if page.output_rel == current.output_rel else ""
            href = relative_url(current.output_rel, page.output_rel)
            label = html.escape(page.title)
            meta = html.escape(posix(page.source_rel))
            parts.append(
                f'<a class="nav-link{active}" href="{href}" data-search="{label.lower()} {meta.lower()}">'
                f"<span>{label}</span><small>{meta}</small></a>"
            )
        parts.append("</div>")
    return "\n".join(parts)


def strip_markdown_for_search(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*_\-|]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def page_template(page: Page, pages: list[Page], body_html: str) -> str:
    prefix = root_prefix(page.output_rel)
    title = html.escape(page.title)
    source = html.escape(posix(page.source_rel))
    nav = nav_html(pages, page)
    return f"""<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - ASIC/DV Notebook</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
  <div class="progress-bar" id="progress-bar"></div>
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <a class="brand" href="{prefix}index.html">
        <span class="brand-mark">DV</span>
        <span><strong>ASIC/DV Notebook</strong><small>面试笔记</small></span>
      </a>
      <button class="theme-toggle" id="theme-toggle" aria-label="切换主题" title="深色 / 浅色">
        <span class="icon-moon">🌙</span>
        <span class="icon-sun">☀</span>
      </button>
    </div>
    <div class="sidebar-inner">
      <label class="search-box">
        <div class="search-box-label"><span>搜索</span><kbd>/</kbd></div>
        <input id="site-search" type="search" autocomplete="off" placeholder="搜索笔记…">
      </label>
      <div id="search-results" class="search-results" hidden></div>
      <nav class="nav-list" aria-label="Notebook pages">
        {nav}
      </nav>
    </div>
  </aside>
  <div class="sidebar-overlay" id="sidebar-overlay"></div>
  <main class="content">
    <div class="content-header">
      <button class="menu-toggle" id="menu-toggle" aria-label="打开菜单">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <div class="page-meta">{source}</div>
    </div>
    <article class="markdown-body" id="markdown-body">
      {body_html}
    </article>
  </main>
  <nav class="toc-panel" id="toc-panel" aria-label="页面目录" hidden>
    <div class="toc-heading">目录</div>
    <div id="toc-links" class="toc-links"></div>
  </nav>
  <button class="back-to-top" id="back-to-top" aria-label="返回顶部" hidden>↑</button>
  <script>window.NOTEBOOK_ROOT = {json.dumps(prefix)};</script>
  <script src="{prefix}assets/search-data.js"></script>
  <script src="{prefix}assets/search.js"></script>
</body>
</html>
"""


def write_site_css(out_dir: Path) -> None:
    css = """
:root {
  --bg: #f0f4f8;
  --paper: #ffffff;
  --paper-soft: #f7f9fc;
  --ink: #1e2b3c;
  --muted: #637282;
  --line: #d1dce8;
  --accent: #0f766e;
  --accent-strong: #0b5e57;
  --accent-soft: #e0f5f2;
  --warm-soft: #fff8ed;
  --code-bg: #0d1117;
  --code-panel: #161b22;
  --code-border: #30363d;
  --code-ink: #e6edf3;
  --shadow: 0 4px 20px rgba(20, 35, 55, 0.08);
  --shadow-lg: 0 8px 40px rgba(20, 35, 55, 0.12);
  --radius: 10px;
  --sidebar-w: 280px;
  --toc-w: 224px;
  --transition: 0.18s ease;
}

[data-theme="dark"] {
  --bg: #0f1117;
  --paper: #1a1f2e;
  --paper-soft: #141824;
  --ink: #dde4ee;
  --muted: #8899aa;
  --line: #252d3d;
  --accent: #14b8a6;
  --accent-strong: #5eead4;
  --accent-soft: #0a1f1c;
  --warm-soft: #1a150a;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.4);
}


* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.78;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  transition: background var(--transition), color var(--transition);
}

a {
  color: var(--accent);
  font-weight: 500;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* ── Progress bar ── */
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 0%;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), #34d399);
  z-index: 2000;
  transition: width 0.08s linear;
  border-radius: 0 2px 2px 0;
  pointer-events: none;
}

/* ── Sidebar ── */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-w);
  overflow-y: auto;
  border-right: 1px solid var(--line);
  background: var(--paper-soft);
  z-index: 100;
  transition: transform var(--transition), background var(--transition), border-color var(--transition);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 14px 12px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 4px;
  position: sticky;
  top: 0;
  background: var(--paper-soft);
  z-index: 1;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  color: var(--ink);
  min-width: 0;
}

.brand:hover {
  text-decoration: none;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 8px;
  background: var(--accent);
  color: white;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0;
}

.brand strong,
.brand small {
  display: block;
}

.brand strong {
  font-size: 13.5px;
  font-weight: 650;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand small {
  color: var(--muted);
  font-size: 11px;
  margin-top: 1px;
}

/* Theme toggle */
.theme-toggle {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  color: var(--muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 15px;
  line-height: 1;
  transition: border-color var(--transition), color var(--transition), background var(--transition);
}

.theme-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.icon-sun {
  display: none;
}

[data-theme="dark"] .icon-sun {
  display: block;
}

[data-theme="dark"] .icon-moon {
  display: none;
}

.sidebar-inner {
  padding: 10px 14px 40px;
}

/* Search */
.search-box {
  display: grid;
  gap: 5px;
  margin-bottom: 14px;
}

.search-box-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--muted);
  font-size: 12px;
  padding: 0 2px;
}

kbd {
  display: inline-block;
  padding: 1px 5px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--paper);
  color: var(--muted);
  font-family: inherit;
  font-size: 11px;
  line-height: 1.5;
}

.search-box input {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 7px 11px;
  color: var(--ink);
  background: var(--paper);
  font: inherit;
  font-size: 14px;
  transition: border-color var(--transition), box-shadow var(--transition), background var(--transition);
}

.search-box input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
  outline: none;
}

[data-theme="dark"] .search-box input {
  background: var(--paper);
  color: var(--ink);
}

.search-results {
  margin: 0 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background: var(--paper);
}

.search-results a {
  display: block;
  padding: 9px 11px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  font-weight: 400;
  transition: background var(--transition);
}

.search-results a:last-child {
  border-bottom: 0;
}

.search-results a:hover {
  background: var(--accent-soft);
  text-decoration: none;
}

.search-results strong,
.search-results small {
  display: block;
}

.search-results strong {
  font-size: 13.5px;
}

.search-results small {
  color: var(--muted);
  margin-top: 2px;
  font-size: 11px;
  font-family: "Cascadia Code", Consolas, monospace;
}

/* Nav */
.nav-section {
  margin-bottom: 18px;
}

.nav-heading {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 12px 0 5px;
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 0 4px;
}

.nav-link {
  display: block;
  margin: 1px 0;
  padding: 7px 10px;
  border-radius: 7px;
  color: var(--ink);
  font-size: 13.5px;
  transition: background var(--transition), color var(--transition);
}

.nav-link span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-link small {
  display: none;
}

.nav-link.active {
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 600;
}

.nav-link:hover {
  background: var(--line);
  text-decoration: none;
}

[data-theme="dark"] .nav-link:hover {
  background: rgba(255, 255, 255, 0.06);
}

/* ── Layout ── */
.content {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  padding: 32px min(5vw, 64px) 88px;
}

.content-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.menu-toggle {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color var(--transition);
}

.menu-toggle:hover {
  border-color: var(--accent);
}

.page-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--paper);
  padding: 4px 12px;
  color: var(--muted);
  font-size: 12px;
  font-family: "Cascadia Code", Consolas, monospace;
  transition: background var(--transition), border-color var(--transition);
}

/* ── Article ── */
.markdown-body {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: min(5vw, 52px);
  box-shadow: var(--shadow-lg);
  max-width: 880px;
  transition: background var(--transition), border-color var(--transition), box-shadow var(--transition);
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  line-height: 1.3;
  margin: 1.5em 0 0.55em;
  letter-spacing: -0.01em;
}

.markdown-body h1 {
  margin-top: 0;
  font-size: 34px;
  color: var(--ink);
}

.markdown-body h2 {
  padding-top: 18px;
  border-top: 2px solid var(--line);
  font-size: 24px;
  color: var(--ink);
}

.markdown-body h3 {
  font-size: 19px;
  color: var(--ink);
}

.markdown-body h4 {
  font-size: 14px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.markdown-body p,
.markdown-body ul,
.markdown-body ol,
.markdown-body table,
.markdown-body .codehilite,
.markdown-body pre {
  margin: 0.85em 0;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  border: 1px solid var(--line);
  border-radius: 8px;
  font-size: 14.5px;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid var(--line);
  padding: 9px 12px;
  vertical-align: top;
}

.markdown-body th {
  background: var(--accent-soft);
  color: var(--ink);
  font-weight: 700;
  font-size: 13px;
}

.markdown-body tr:nth-child(even) td {
  background: var(--paper-soft);
}

.markdown-body tr:hover td {
  background: rgba(15, 118, 110, 0.04);
}

[data-theme="dark"] .markdown-body tr:hover td {
  background: rgba(20, 184, 166, 0.06);
}

.markdown-body :not(pre) > code {
  border-radius: 5px;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 0.1em 0.38em;
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 0.9em;
  white-space: break-spaces;
}

[data-theme="dark"] .markdown-body :not(pre) > code {
  background: rgba(20, 184, 166, 0.12);
  color: var(--accent-strong);
}

.markdown-body .codehilite {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--code-border);
  border-radius: 8px;
  background: var(--code-bg);
  box-shadow: 0 8px 28px rgba(13, 17, 23, 0.2);
}

.markdown-body .code-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 36px;
  border-bottom: 1px solid var(--code-border);
  background: var(--code-panel);
  padding: 0 10px 0 14px;
  color: #9da7b3;
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 12px;
}

.markdown-body .code-lang {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-body .code-copy-button {
  flex: 0 0 auto;
  min-width: 56px;
  min-height: 26px;
  border: 1px solid #3b4552;
  border-radius: 6px;
  background: #1c242f;
  color: #c9d1d9;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  transition: border-color 0.15s, color 0.15s;
}

.markdown-body .code-copy-button:hover,
.markdown-body .code-copy-button:focus {
  border-color: #56d4c8;
  color: #ffffff;
  outline: none;
}

.markdown-body .code-copy-button.copied {
  border-color: #2ea043;
  color: #7ee787;
}

.markdown-body pre {
  overflow-x: auto;
  background: var(--code-bg);
  color: var(--code-ink);
  padding: 18px 20px;
  tab-size: 2;
  margin: 0;
}

.markdown-body .codehilite pre,
.markdown-body .codehilite code {
  margin: 0;
}

.markdown-body pre code {
  background: transparent;
  color: var(--code-ink);
  padding: 0;
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace;
  font-size: 13px;
  line-height: 1.68;
  white-space: pre;
}

.markdown-body blockquote {
  margin: 1em 0;
  border-left: 4px solid var(--accent);
  border-radius: 0 8px 8px 0;
  background: var(--warm-soft);
  padding: 12px 16px;
  color: var(--muted);
  font-style: normal;
}

[data-theme="dark"] .markdown-body blockquote {
  background: rgba(14, 116, 108, 0.1);
}

.markdown-body img {
  max-width: 100%;
  border-radius: 8px;
}

.markdown-body hr {
  border: 0;
  border-top: 2px solid var(--line);
  margin: 2em 0;
}

/* ── TOC Panel ── */
.toc-panel {
  display: none;
}

@media (min-width: 1360px) {
  .toc-panel {
    display: block;
    position: fixed;
    top: 0;
    right: 0;
    width: var(--toc-w);
    height: 100vh;
    overflow-y: auto;
    padding: 24px 16px 40px;
    border-left: 1px solid var(--line);
    background: var(--paper-soft);
    transition: background var(--transition), border-color var(--transition);
  }

  .toc-panel[hidden] {
    display: none;
  }

  .content {
    margin-right: var(--toc-w);
  }
}

.toc-heading {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted);
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  background: var(--paper-soft);
  padding-top: 4px;
}

.toc-link {
  display: block;
  padding: 4px 8px;
  border-radius: 5px;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.45;
  transition: color var(--transition), background var(--transition);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toc-link:hover {
  color: var(--ink);
  background: var(--line);
  text-decoration: none;
}

.toc-link.active {
  color: var(--accent);
  background: var(--accent-soft);
  font-weight: 600;
}

.toc-h3 {
  padding-left: 18px;
  font-size: 12px;
}

/* ── Back to top ── */
.back-to-top {
  position: fixed;
  bottom: 28px;
  right: 28px;
  width: 40px;
  height: 40px;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--paper);
  color: var(--muted);
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: var(--shadow);
  transition: all var(--transition);
  font-size: 18px;
  z-index: 500;
}

.back-to-top:hover {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.back-to-top[hidden] {
  display: none;
}

/* ── Sidebar overlay (mobile) ── */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 90;
}

.sidebar-overlay.active {
  display: block;
}

/* ── Responsive ── */
@media (max-width: 860px) {
  .sidebar {
    transform: translateX(-100%);
    box-shadow: none;
  }

  .sidebar.open {
    transform: none;
    box-shadow: 10px 0 40px rgba(0, 0, 0, 0.16);
  }

  .menu-toggle {
    display: flex;
  }

  .content {
    margin-left: 0;
    padding: 20px 16px 64px;
  }

  .markdown-body {
    padding: 22px 18px;
  }

  .markdown-body h1 {
    font-size: 26px;
  }
}
"""
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    css_parts = [css.strip()]
    syntax_css = pygments_css().strip()
    if syntax_css:
        css_parts.append(syntax_css)
    (assets / "site.css").write_text("\n\n".join(css_parts) + "\n", encoding="utf-8")


def write_search_js(out_dir: Path) -> None:
    js = r"""
(function () {
  "use strict";

  /* ── Helpers ── */
  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  }

  function normalize(value) {
    return value.trim().toLowerCase();
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.cssText = "position:fixed;left:-9999px";
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand("copy") ? resolve() : reject(new Error("copy failed"));
      } catch (e) { reject(e); } finally { area.remove(); }
    });
  }

  /* ── Dark mode ── */
  function initTheme() {
    const toggle = document.getElementById("theme-toggle");
    const html = document.documentElement;
    const saved = localStorage.getItem("notebook-theme");
    if (saved) {
      html.dataset.theme = saved;
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      html.dataset.theme = "dark";
    }
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      const next = html.dataset.theme === "dark" ? "light" : "dark";
      html.dataset.theme = next;
      try { localStorage.setItem("notebook-theme", next); } catch (e) {}
    });
  }

  /* ── Progress bar ── */
  function initProgressBar() {
    const bar = document.getElementById("progress-bar");
    if (!bar) return;
    function update() {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const pct = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0;
      bar.style.width = pct + "%";
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* ── Back to top ── */
  function initBackToTop() {
    const btn = document.getElementById("back-to-top");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.hidden = (window.scrollY || document.documentElement.scrollTop) < 400;
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ── Mobile sidebar toggle ── */
  function initSidebarToggle() {
    const menuBtn = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (!menuBtn || !sidebar || !overlay) return;

    function openSidebar() {
      sidebar.classList.add("open");
      overlay.classList.add("active");
      document.body.style.overflow = "hidden";
    }
    function closeSidebar() {
      sidebar.classList.remove("open");
      overlay.classList.remove("active");
      document.body.style.overflow = "";
    }
    menuBtn.addEventListener("click", openSidebar);
    overlay.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("open")) closeSidebar();
    });
  }

  /* ── TOC (right panel) ── */
  function initToc() {
    const article = document.getElementById("markdown-body");
    const tocPanel = document.getElementById("toc-panel");
    const tocLinks = document.getElementById("toc-links");
    if (!article || !tocPanel || !tocLinks) return;

    const headings = Array.from(article.querySelectorAll("h2, h3"));
    if (headings.length < 2) return;

    tocPanel.hidden = false;

    const frag = document.createDocumentFragment();
    headings.forEach(function (h) {
      const a = document.createElement("a");
      a.href = h.id ? "#" + h.id : "#";
      a.className = "toc-link toc-" + h.tagName.toLowerCase();
      a.textContent = (h.textContent || "").replace(/\s*¶\s*$/, "").trim();
      frag.appendChild(a);
    });
    tocLinks.appendChild(frag);

    /* Scrollspy */
    if ("IntersectionObserver" in window) {
      const allLinks = Array.from(tocLinks.querySelectorAll(".toc-link"));
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            allLinks.forEach(function (link) {
              link.classList.toggle("active", id && link.getAttribute("href") === "#" + id);
            });
          }
        });
      }, { rootMargin: "0px 0px -55% 0px", threshold: 0 });
      headings.forEach(function (h) { if (h.id) observer.observe(h); });
    }
  }

  /* ── Code copy buttons ── */
  function addCodeTools() {
    const targets = Array.from(document.querySelectorAll(".markdown-body .codehilite, .markdown-body pre"));
    const handled = new Set();
    targets.forEach(function (target) {
      const pre = target.matches("pre") ? target : target.querySelector("pre");
      if (!pre || handled.has(pre)) return;
      handled.add(pre);

      let container = target;
      if (target.matches("pre") && !target.closest(".codehilite")) {
        container = document.createElement("div");
        container.className = "codehilite plain-code";
        container.dataset.lang = target.dataset.lang || "Code";
        target.parentNode.insertBefore(container, target);
        container.appendChild(target);
      } else if (target.matches("pre")) {
        container = target.closest(".codehilite") || target;
      }
      if (container.querySelector(".code-toolbar")) return;

      const toolbar = document.createElement("div");
      toolbar.className = "code-toolbar";
      const label = document.createElement("span");
      label.className = "code-lang";
      label.textContent = container.dataset.lang || pre.dataset.lang || "Code";
      const btn = document.createElement("button");
      btn.className = "code-copy-button";
      btn.type = "button";
      btn.textContent = "Copy";
      btn.addEventListener("click", function () {
        copyText(pre.textContent || "").then(function () {
          btn.textContent = "Copied";
          btn.classList.add("copied");
          window.setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 1400);
        }).catch(function () {
          btn.textContent = "Failed";
          window.setTimeout(function () { btn.textContent = "Copy"; }, 1400);
        });
      });
      toolbar.appendChild(label);
      toolbar.appendChild(btn);
      container.insertBefore(toolbar, pre);
    });
  }

  /* ── Search ── */
  function initSearch() {
    const input = document.getElementById("site-search");
    const results = document.getElementById("search-results");
    const navLinks = Array.from(document.querySelectorAll(".nav-link"));
    if (!input || !results) return;

    const searchIndex = window.NOTEBOOK_SEARCH_INDEX || [];

    /* "/" to focus search */
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const tag = (document.activeElement || {}).tagName;
        if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
          e.preventDefault();
          input.focus();
          input.select();
        }
      }
      if (e.key === "Escape" && document.activeElement === input) {
        input.blur();
        input.value = "";
        update();
      }
    });

    function update() {
      const query = normalize(input.value);
      navLinks.forEach(function (link) {
        const haystack = link.dataset.search || "";
        link.style.display = !query || haystack.includes(query) ? "" : "none";
      });

      if (query.length < 2 || searchIndex.length === 0) {
        results.hidden = true;
        results.innerHTML = "";
        return;
      }

      const words = query.split(/\s+/).filter(Boolean);
      const matches = searchIndex
        .map(function (item) {
          const haystack = (item.title + " " + item.path + " " + item.text).toLowerCase();
          const score = words.reduce(function (tot, w) { return tot + (haystack.includes(w) ? 1 : 0); }, 0);
          return { item, score };
        })
        .filter(function (m) { return m.score > 0; })
        .sort(function (a, b) { return b.score - a.score || a.item.path.localeCompare(b.item.path); })
        .slice(0, 8);

      if (matches.length === 0) {
        results.hidden = true;
        results.innerHTML = "";
        return;
      }

      const root = window.NOTEBOOK_ROOT || "";
      results.innerHTML = matches.map(function (m) {
        const url = root + m.item.path;
        return "<a href=\"" + escapeHtml(url) + "\"><strong>" + escapeHtml(m.item.title) + "</strong><small>" + escapeHtml(m.item.path) + "</small></a>";
      }).join("");
      results.hidden = false;
    }

    input.addEventListener("input", update);
  }

  /* ── Boot ── */
  initTheme();
  initProgressBar();
  initBackToTop();
  initSidebarToggle();
  addCodeTools();
  initToc();
  initSearch();

})();
"""
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "search.js").write_text(js.strip() + "\n", encoding="utf-8")


def write_search_index(out_dir: Path, pages: list[Page]) -> None:
    items = []
    for page in pages:
        text = strip_markdown_for_search(read_text(page.source))
        items.append(
            {
                "title": page.title,
                "path": posix(page.output_rel),
                "source": posix(page.source_rel),
                "text": text[:20000],
            }
        )
    json_text = json.dumps(items, ensure_ascii=False, indent=2)
    (out_dir / "search-index.json").write_text(json_text, encoding="utf-8")

    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "search-data.js").write_text(
        "window.NOTEBOOK_SEARCH_INDEX = " + json_text + ";\n",
        encoding="utf-8",
    )


def copy_assets(out_dir: Path) -> None:
    for source in ROOT.rglob("*"):
        if not source.is_file() or should_skip(source):
            continue
        if source.suffix.lower() not in ASSET_SUFFIXES:
            continue
        target = out_dir / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def build(out_dir: Path) -> None:
    markdown_files = iter_markdown_files()
    pages = build_pages(markdown_files)
    md_to_html = {page.source_rel: page.output_rel for page in pages}

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    write_site_css(out_dir)
    write_search_js(out_dir)
    write_search_index(out_dir, pages)
    copy_assets(out_dir)

    for page in pages:
        source_text = read_text(page.source)
        body = render_markdown(source_text)
        body = rewrite_links(body, page.source_rel, page.output_rel, md_to_html)
        body = annotate_code_blocks(body, fenced_code_languages(source_text))
        html_text = page_template(page, pages, body)
        target = out_dir / page.output_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html_text, encoding="utf-8")

    print(f"Built {len(pages)} pages in {out_dir}")
    print(f"Open {out_dir / 'index.html'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the ASIC/DV Markdown notebook as static HTML.")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory. Defaults to ./site.",
    )
    args = parser.parse_args()
    build(args.out.resolve())


if __name__ == "__main__":
    main()
