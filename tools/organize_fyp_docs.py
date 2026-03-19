#!/opt/homebrew/bin/python3

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path("/Users/frankieliu/Desktop/FYP")
ORIGINALS_DIR = ROOT / "01_originals"
MARKDOWN_DIR = ROOT / "02_markdown"
LEGACY_PREVIEW_DIR = MARKDOWN_DIR / "_legacy_preview"
DOC_SUFFIXES = {".pdf", ".pptx", ".ppt"}


def run_command(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u2212", "-")
    text = text.replace("\t", " ")
    return text


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def escape_table_text(text: str) -> str:
    return text.replace("|", r"\|")


def normalize_label(label: str) -> str:
    key = collapse_spaces(label).strip(":")
    known = {
        "Project code": "Project code",
        "Project title": "Project title",
        "No. of students": "No. of students",
        "Description of project": "Description of project",
        "Industrial collaboration": "Industrial collaboration",
        "Email": "Email",
        "Office": "Office",
    }
    return known.get(key, key)


KNOWN_FIELD_LABELS = {
    "Project code",
    "Project title",
    "No. of students",
    "Description of project",
    "Industrial collaboration",
    "Email",
    "Office",
}


def split_paragraphs(lines: list[str]) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = collapse_spaces(line)
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def render_header(lines: list[str]) -> list[str]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = collapse_spaces(line)
        if not stripped:
            if current:
                groups.append(current)
                current = []
            continue
        current.append(stripped)
    if current:
        groups.append(current)

    rendered: list[str] = []
    if not groups:
        return rendered

    rendered.append(f"# {groups[0][0]}")
    rendered.append("")

    if len(groups[0]) > 1:
        rendered.append("  \n".join(groups[0][1:]))
        rendered.append("")

    for idx, group in enumerate(groups[1:], start=1):
        if idx == len(groups) - 1:
            rendered.append("  ".join(group))
        else:
            rendered.append("  \n".join(group))
        rendered.append("")
    return rendered


def parse_project_text(text: str) -> str:
    lines = normalize_whitespace(text).splitlines()
    field_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 .()/&,'-]+?)\s*:\s*(.*)$")

    header_lines: list[str] = []
    tail_lines: list[str] = []
    projects: list[list[tuple[str, list[str]]]] = []
    current_project: list[tuple[str, list[str]]] = []
    current_label: str | None = None
    current_value_lines: list[str] = []
    started = False

    def commit_field() -> None:
        nonlocal current_label, current_value_lines, current_project
        if current_label is None:
            return
        current_project.append((current_label, current_value_lines[:]))
        current_label = None
        current_value_lines = []

    def commit_project() -> None:
        nonlocal current_project
        if current_label is not None:
            commit_field()
        if current_project:
            projects.append(current_project[:])
            current_project = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            if started and current_label is not None and current_value_lines and current_value_lines[-1] != "":
                current_value_lines.append("")
            elif not started:
                header_lines.append("")
            continue

        match = field_pattern.match(line)
        if match:
            label = normalize_label(match.group(1))
            value = match.group(2).strip()
            if label not in KNOWN_FIELD_LABELS:
                match = None
        if match:
            if label == "Project code":
                if started:
                    commit_project()
                started = True
                current_label = label
                current_value_lines = [value]
            elif started:
                commit_field()
                current_label = label
                current_value_lines = [value]
            else:
                header_lines.append(stripped)
            continue

        if started and is_date_like(stripped):
            if current_label is not None:
                commit_field()
            tail_lines.append(stripped)
            continue

        if started and current_label is not None:
            current_value_lines.append(stripped)
        elif started:
            tail_lines.append(stripped)
        else:
            header_lines.append(stripped)

    if started:
        commit_project()

    output: list[str] = render_header(header_lines)

    field_order = [
        "Project code",
        "Project title",
        "No. of students",
        "Description of project",
        "Industrial collaboration",
    ]

    for project in projects:
        field_map = {label: split_paragraphs(value_lines) for label, value_lines in project}
        project_code = field_map.get("Project code", ["Project"])[0]
        output.append(f"## Project {escape_table_text(project_code)}")
        output.append("")
        output.append("| Field | Content |")
        output.append("| --- | --- |")

        used_labels: set[str] = set()
        for label in field_order:
            if label not in field_map:
                continue
            content = "<br><br>".join(escape_table_text(p) for p in field_map[label])
            output.append(f"| {escape_table_text(label)} | {content} |")
            used_labels.add(label)

        for label, paragraphs in field_map.items():
            if label in used_labels:
                continue
            content = "<br><br>".join(escape_table_text(p) for p in paragraphs)
            output.append(f"| {escape_table_text(label)} | {content} |")

        output.append("")

    if tail_lines:
        output.extend(split_paragraphs(tail_lines))
        output.append("")

    return "\n".join(output).strip() + "\n"


def remove_repeated_slide_footers(pages: list[list[str]]) -> list[list[str]]:
    normalized_counter: Counter[str] = Counter()
    footer_prefix_counter: Counter[str] = Counter()
    for page in pages:
        seen: set[str] = set()
        seen_prefixes: set[str] = set()
        for line in page:
            normalized = collapse_spaces(line)
            if not normalized:
                continue
            seen.add(normalized)
            footer_match = re.match(r"^(.*)\s+\d+\s*/\s*\d+$", normalized)
            if footer_match:
                seen_prefixes.add(footer_match.group(1).strip())
        normalized_counter.update(seen)
        footer_prefix_counter.update(seen_prefixes)

    repeated = {
        line
        for line, count in normalized_counter.items()
        if count >= 3 and count >= max(3, len(pages) // 2)
    }
    repeated_footer_prefixes = {
        line
        for line, count in footer_prefix_counter.items()
        if count >= 3 and count >= max(3, len(pages) // 2)
    }

    cleaned_pages: list[list[str]] = []
    for page in pages:
        filtered: list[str] = []
        for line in page:
            normalized = collapse_spaces(line)
            if not normalized:
                continue
            if normalized in repeated:
                continue
            if re.fullmatch(r"\d+\s*/\s*\d+", normalized):
                continue
            footer_match = re.match(r"^(.*)\s+\d+\s*/\s*\d+$", normalized)
            if footer_match and footer_match.group(1).strip() in repeated_footer_prefixes:
                continue
            filtered.append(line.rstrip())
        cleaned_pages.append(filtered)
    return cleaned_pages


def is_bullet_line(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith(("•", "-", "*", "", "■", "▪"))


def strip_bullet(text: str) -> str:
    stripped = text.lstrip()
    while stripped and stripped[0] in {"•", "-", "*", "", "■", "▪"}:
        stripped = stripped[1:].lstrip()
    return collapse_spaces(stripped)


def render_slide_page(lines: list[str], index: int, first_page: bool) -> list[str]:
    if not lines:
        return []

    output: list[str] = []
    stripped_lines = [line.rstrip() for line in lines if collapse_spaces(line)]
    if not stripped_lines:
        return []

    title_lines: list[str] = []
    body_start = 0
    for idx, line in enumerate(stripped_lines):
        if is_bullet_line(line):
            body_start = idx
            break
        clean = collapse_spaces(line)
        indent = len(line) - len(line.lstrip())
        if not first_page and title_lines:
            first_title = title_lines[0]
            if len(title_lines) >= 2:
                body_start = idx
                break
            if indent >= 8 and not re.match(r"^(Topic|#)", first_title, re.IGNORECASE):
                body_start = idx
                break
        title_lines.append(clean)
        body_start = idx + 1

    if first_page:
        output.append(f"# {title_lines[0] if title_lines else f'Document {index}'}")
        output.append("")
        for line in title_lines[1:]:
            output.append(line)
            output.append("")
    else:
        title = " - ".join(title_lines[:2]) if len(title_lines[:2]) == 2 else (title_lines[0] if title_lines else f"Slide {index}")
        output.append(f"## {title}")
        output.append("")
        if len(title_lines) > 2:
            for line in title_lines[2:]:
                output.append(line)
                output.append("")

    body_lines = stripped_lines[body_start:]
    force_bullets = (
        len(body_lines) >= 2
        and not any(is_bullet_line(line) for line in body_lines)
        and all(len(collapse_spaces(line)) <= 140 for line in body_lines)
    )

    current_bullet: str | None = None
    current_paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal current_paragraph
        if current_paragraph:
            output.append(" ".join(current_paragraph))
            output.append("")
            current_paragraph = []

    def flush_bullet() -> None:
        nonlocal current_bullet
        if current_bullet:
            output.append(f"- {current_bullet}")
            current_bullet = None

    for raw_line in body_lines:
        line = raw_line.rstrip()
        clean = collapse_spaces(line)
        if not clean:
            flush_paragraph()
            flush_bullet()
            continue

        if force_bullets:
            flush_paragraph()
            flush_bullet()
            output.append(f"- {clean}")
            continue

        if is_bullet_line(line):
            flush_paragraph()
            flush_bullet()
            current_bullet = strip_bullet(line)
            continue

        if current_bullet is not None:
            current_bullet = f"{current_bullet} {clean}"
            continue

        current_paragraph.append(clean)

    flush_paragraph()
    flush_bullet()
    return output


def parse_slide_text(text: str) -> str:
    pages = [page.splitlines() for page in normalize_whitespace(text).split("\f")]
    pages = remove_repeated_slide_footers(pages)
    output: list[str] = []

    first_content_page = True
    for idx, page in enumerate(pages, start=1):
        rendered = render_slide_page(page, idx, first_page=first_content_page)
        if not rendered:
            continue
        output.extend(rendered)
        if output and output[-1] != "":
            output.append("")
        first_content_page = False

    return "\n".join(output).strip() + "\n"


def convert_to_text(source_path: Path) -> str:
    if source_path.suffix.lower() == ".pdf":
        return run_command(["pdftotext", "-layout", str(source_path), "-"])

    with tempfile.TemporaryDirectory(prefix="fyp-docs-") as temp_dir:
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_dir,
                str(source_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pdf_path = Path(temp_dir) / f"{source_path.stem}.pdf"
        return run_command(["pdftotext", "-layout", str(pdf_path), "-"])


def is_project_document(text: str) -> bool:
    lowered = text.lower()
    return "project code" in lowered and "description of project" in lowered


def infer_advisor_slug(filename: str) -> str:
    stem = Path(filename).stem
    match = re.match(
        r"^(.+?)(?:[_ ](?:suggested|fyp|ppt|Suggested|FYP|PPT)|$)",
        stem,
        re.IGNORECASE,
    )
    advisor = match.group(1) if match else stem
    advisor = advisor.replace("(1)", "").strip(" _-")
    advisor = re.sub(r"[^A-Za-z0-9]+", "_", advisor)
    advisor = advisor.strip("_")
    return advisor.upper() if advisor else "MISC"


def infer_doc_kind(filename: str, suffix: str) -> str:
    lowered = filename.lower()
    if suffix in {".pptx", ".ppt"}:
        return "slides_source"
    if any(token in lowered for token in ["ppt", "slides", "presentation", "briefing"]):
        return "slides"
    return "topics"


def unique_target_path(base_dir: Path, stem: str, suffix: str) -> Path:
    candidate = base_dir / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = base_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def organize_preview_files() -> None:
    preview_dir = ROOT / "markdown_preview"
    if not preview_dir.exists():
        return
    LEGACY_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for preview_file in preview_dir.glob("*.md"):
        target = unique_target_path(LEGACY_PREVIEW_DIR, preview_file.stem, preview_file.suffix)
        shutil.move(str(preview_file), str(target))
    shutil.rmtree(preview_dir)


def build_markdown(text: str) -> str:
    if is_project_document(text):
        return parse_project_text(text)
    return parse_slide_text(text)


def is_date_like(text: str) -> bool:
    clean = collapse_spaces(text)
    return bool(
        re.fullmatch(r"\d{4}\s+[A-Za-z]+(?:\s+\d{1,2})?", clean)
        or re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", clean)
    )


def rebuild_markdown_from_originals() -> list[tuple[Path, Path]]:
    processed: list[tuple[Path, Path]] = []
    for original in sorted(path for path in ORIGINALS_DIR.rglob("*") if path.is_file() and path.suffix.lower() in DOC_SUFFIXES):
        advisor = original.parent.name
        markdown_subdir = MARKDOWN_DIR / advisor
        markdown_subdir.mkdir(parents=True, exist_ok=True)
        raw_text = convert_to_text(original)
        markdown = build_markdown(raw_text)
        markdown_target = markdown_subdir / f"{original.stem}.md"
        markdown_target.write_text(markdown, encoding="utf-8")
        processed.append((original, markdown_target))
    return processed


def organize_documents() -> list[tuple[Path, Path]]:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    organize_preview_files()

    source_files = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in DOC_SUFFIXES
    )

    for source in source_files:
        advisor = infer_advisor_slug(source.name)
        kind = infer_doc_kind(source.name, source.suffix.lower())

        originals_subdir = ORIGINALS_DIR / advisor
        markdown_subdir = MARKDOWN_DIR / advisor
        originals_subdir.mkdir(parents=True, exist_ok=True)
        markdown_subdir.mkdir(parents=True, exist_ok=True)

        normalized_stem = f"{advisor}_{kind}"
        moved_source = unique_target_path(originals_subdir, normalized_stem, source.suffix.lower())
        shutil.move(str(source), str(moved_source))

    return rebuild_markdown_from_originals()


def print_summary(processed: list[tuple[Path, Path]]) -> None:
    print(f"Processed {len(processed)} documents.")
    print(f"Originals: {ORIGINALS_DIR}")
    print(f"Markdown: {MARKDOWN_DIR}")
    for original, markdown in processed[:10]:
        print(f"- {original.name} -> {markdown.name}")
    if len(processed) > 10:
        print(f"... and {len(processed) - 10} more")


if __name__ == "__main__":
    processed_pairs = organize_documents()
    print_summary(processed_pairs)
