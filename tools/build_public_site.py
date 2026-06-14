from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / ".public-build"
PUBLIC_SOURCE = BUILD_ROOT / "source"
PUBLIC_SITE = BUILD_ROOT / "site"
DEFAULT_OUT_DIR = ROOT.parent / "notes-public-site"

INCLUDE_FILES = {
    Path("glossary.md"),
    Path("knowledge-base/README.md"),
    Path("knowledge-base/asic-frontend.md"),
    Path("knowledge-base/design-verification.md"),
    Path("knowledge-base/protocols.md"),
    Path("knowledge-base/systemverilog-uvm.md"),
    Path("question-bank/README.md"),
    Path("question-bank/question-bank.md"),
    Path("question-bank/dv-online-digest.md"),
}

EXCLUDED_TARGET_PREFIXES = (
    "actual-interviews/",
    "projects-hr/",
    "templates/",
)
EXCLUDED_TARGET_FILES = {
    "company-sites.md",
    "inbox.md",
}


def posix(path: Path) -> str:
    return path.as_posix()


def is_excluded_link(target: str) -> bool:
    clean = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not clean or re.match(r"^[a-z][a-z0-9+.-]*:", clean, flags=re.I):
        return False

    while clean.startswith("../"):
        clean = clean[3:]
    clean = clean.lstrip("./")
    clean = clean.replace("\\", "/")
    return clean in EXCLUDED_TARGET_FILES or clean.startswith(EXCLUDED_TARGET_PREFIXES)


def sanitize_markdown(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)
        return label if is_excluded_link(target) else match.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy_public_sources() -> list[str]:
    reset_dir(PUBLIC_SOURCE)
    (PUBLIC_SOURCE / "tools").mkdir(parents=True)
    shutil.copy2(ROOT / "tools" / "build_html.py", PUBLIC_SOURCE / "tools" / "build_html.py")

    included: list[str] = []
    for rel in sorted(INCLUDE_FILES, key=posix):
        source = ROOT / rel
        if not source.exists():
            continue
        target = PUBLIC_SOURCE / rel
        write_text(target, sanitize_markdown(source.read_text(encoding="utf-8")))
        included.append(posix(rel))

    write_text(
        PUBLIC_SOURCE / "index.md",
        """
# ASIC/DV Public Notes

这是筛选后的公开网页版本，只包含通用 ASIC、DV、SystemVerilog/UVM、协议和题库复习内容。

## 入口

| 模块 | 入口 |
| --- | --- |
| Knowledge Base | [知识库导航](knowledge-base/README.md) |
| Question Bank | [面试题库](question-bank/README.md) |
| Glossary | [术语速查](glossary.md) |

## 知识库

- [ASIC Frontend](knowledge-base/asic-frontend.md#asic-overview)
- [Design Verification](knowledge-base/design-verification.md#dv-overview)
- [SystemVerilog / UVM](knowledge-base/systemverilog-uvm.md#sv-overview)
- [Protocols](knowledge-base/protocols.md#protocol-overview)

## 题库

- [ASIC Frontend](question-bank/question-bank.md#qb-asic-frontend)
- [Design Verification](question-bank/question-bank.md#qb-design-verification)
- [SystemVerilog / UVM](question-bank/question-bank.md#qb-systemverilog-uvm)
- [Protocols](question-bank/question-bank.md#qb-protocols)
- [DV 网上面经知识点汇总](question-bank/dv-online-digest.md#common-directions)
""",
    )
    included.insert(0, "index.md")
    return included


def sync_site_to_output(out_dir: Path) -> None:
    out_dir = out_dir.resolve()
    root = ROOT.resolve()
    if out_dir == root or root in out_dir.parents:
        raise SystemExit(f"Refusing to publish inside the private notes tree: {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    for child in out_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for child in PUBLIC_SITE.iterdir():
        target = out_dir / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)

    write_text(out_dir / ".nojekyll", "")
    write_text(
        out_dir / "README.md",
        """
# ASIC/DV Public Notes Site

This repository contains a curated static HTML export of ASIC/DV study notes.

The private source notebook is not published here. Rebuild this repository from the private notebook with:

```powershell
python C:\\Users\\28724\\Desktop\\notes\\tools\\build_public_site.py
```
""",
    )


def build(out_dir: Path, profile: str) -> None:
    reset_dir(PUBLIC_SITE)

    if profile == "curated":
        copy_public_sources()
        build_script = PUBLIC_SOURCE / "tools" / "build_html.py"
        build_cwd = PUBLIC_SOURCE
    else:
        build_script = ROOT / "tools" / "build_html.py"
        build_cwd = ROOT

    subprocess.run([sys.executable, str(build_script), "--out", str(PUBLIC_SITE)], cwd=build_cwd, check=True)
    sync_site_to_output(out_dir)

    print(f"Public site is ready: {out_dir}")
    print(f"Open {out_dir / 'index.html'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a curated public static site from the private notes.")
    parser.add_argument(
        "--profile",
        choices=("full", "curated"),
        default="full",
        help="Use full to publish every generated page, or curated for the conservative subset.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output public repository directory. Defaults to {DEFAULT_OUT_DIR}.",
    )
    args = parser.parse_args()
    build(args.out.resolve(), args.profile)


if __name__ == "__main__":
    main()
