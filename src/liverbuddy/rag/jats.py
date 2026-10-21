"""Parse JATS/BITS XML (PubMed Central, NCBI Bookshelf) into section-aware text blocks."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

_WS = re.compile(r"\s+")
BLOCK_TAGS = {"p", "list", "boxed-text", "table-wrap", "disp-quote", "def-list"}
SKIP_SECTIONS = re.compile(
    r"^(references?|acknowledge?ments?|contributor information|footnotes|supplementary|abbreviations|"
    r"author.*(relationships|contributions?)|contribution statement|conflicts? of interest|funding|"
    r"associated data|cited references|annotated bibliography|other reference links|chemical formula)",
    re.I)


@dataclass
class Block:
    section_path: list[str]
    section_id: str
    text: str
    kind: str  # paragraph | table | list | box


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean(text: str) -> str:
    return _WS.sub(" ", html.unescape(text)).strip()


def element_text(el: ET.Element) -> str:
    return clean("".join(el.itertext()))


def _table_text(el: ET.Element) -> str:
    parts = []
    for child in el.iter():
        t = _local(child.tag)
        if t in ("label", "caption"):
            parts.append(element_text(child))
        elif t == "tr":
            cells = [element_text(c) for c in child if _local(c.tag) in ("td", "th")]
            parts.append(" | ".join(c for c in cells if c))
        elif t == "table-wrap-foot":
            parts.append(element_text(child))
    return "\n".join(p for p in parts if p)


def _blocks(sec: ET.Element, path: list[str], sec_id: str) -> Iterator[Block]:
    for child in sec:
        tag = _local(child.tag)
        if tag == "sec":
            title_el = next((c for c in child if _local(c.tag) == "title"), None)
            title = element_text(title_el) if title_el is not None else ""
            if title and SKIP_SECTIONS.match(title):
                continue
            yield from _blocks(child, path + [title] if title else path, child.get("id") or sec_id)
        elif tag in BLOCK_TAGS:
            kind = {"table-wrap": "table", "list": "list", "boxed-text": "box"}.get(tag, "paragraph")
            text = _table_text(child) if kind == "table" else element_text(child)
            if len(text) > 40:
                yield Block(path, sec_id, text, kind)


def parse_article(xml_text: str) -> tuple[str, list[Block]]:
    """PMC article XML -> (title, blocks from <body>)."""
    root = ET.fromstring(xml_text)
    title_el = root.find(".//{*}article-title") if "}" in root.tag else root.find(".//article-title")
    title = element_text(title_el) if title_el is not None else "Untitled"
    body = root.find(".//body")
    if body is None:
        return title, []
    blocks = list(_blocks(body, [], ""))
    body_blocks = list(blocks)
    # Author manuscripts keep boxes/tables (e.g. AASLD "Guidance statements") in <floats-group>;
    # file each float under the section that first cites it.
    cited_in = _first_citing_section(body)
    floats = root.find(".//floats-group")
    for el in (floats if floats is not None else []):
        tag = _local(el.tag)
        if tag not in ("boxed-text", "table-wrap"):
            continue
        path, sec_id = cited_in.get(el.get("id", "")) or _most_similar_section(element_text(el), body_blocks)
        if tag == "table-wrap":
            text = _table_text(el)
            label = element_text(el.find("label")) if el.find("label") is not None else "Table"
            kind = "table"
        else:
            text = element_text(el)
            label = element_text(el.find(".//title")) if el.find(".//title") is not None else "Box"
            kind = "box"
        if len(text) > 40:
            blocks.append(Block(path + [label.rstrip(":")], sec_id, text, kind))
    return title, blocks


def _most_similar_section(text: str, blocks: list[Block]) -> tuple[list[str], str]:
    """Uncited floats (e.g. 'Key points' boxes) go to the body section with the closest TF-IDF match."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    sections: dict[str, tuple[list[str], str, list[str]]] = {}
    for b in blocks:
        key = " > ".join(b.section_path)
        sections.setdefault(key, (b.section_path, b.section_id, []))[2].append(b.text)
    if not sections:
        return ["Tables and boxes"], ""
    keys = list(sections)
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    mat = vec.fit_transform([" ".join(sections[k][2]) for k in keys] + [text])
    best = keys[int(linear_kernel(mat[-1], mat[:-1]).argmax())]
    return sections[best][0], sections[best][1]


def _first_citing_section(body: ET.Element) -> dict[str, tuple[list[str], str]]:
    out: dict[str, tuple[list[str], str]] = {}

    def walk(sec: ET.Element, path: list[str], sec_id: str) -> None:
        for child in sec:
            if _local(child.tag) == "sec":
                t = child.find("title")
                title = element_text(t) if t is not None else ""
                walk(child, path + [title] if title else path, child.get("id") or sec_id)
            else:
                for x in child.iter("xref"):
                    for rid in (x.get("rid") or "").split():
                        out.setdefault(rid, (path, sec_id))

    walk(body, [], "")
    return out


def parse_book_part(xml_text: str) -> tuple[str, list[Block]]:
    """NCBI Bookshelf (BITS) chapter -> (chapter title, blocks)."""
    xml_text = re.sub(r"<!DOCTYPE[^>]*>", "", xml_text)
    root = ET.fromstring(xml_text)
    title_el = root.find(".//book-part-meta//title")
    title = element_text(title_el) if title_el is not None else root.get("id", "Untitled")
    body = root.find(".//body")
    return title, list(_blocks(body, [], "")) if body is not None else []
