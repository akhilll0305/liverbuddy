"""Turn guideline and LiverTox XML into retrievable chunks with citation metadata."""

from __future__ import annotations

import re

from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from liverbuddy.rag.jats import Block, parse_article, parse_book_part

GUIDELINES = {
    "PMC10735173": {
        "source": "aasld2023",
        "short": "AASLD 2023 Practice Guidance",
        "citation": "Rinella ME et al. AASLD Practice Guidance on the clinical assessment and management of "
                    "nonalcoholic fatty liver disease. Hepatology 2023;77:1797-1835.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10735173/",
    },
    "PMC11519095": {
        "source": "easl2024",
        "short": "EASL-EASD-EASO 2024 MASLD Guideline",
        "citation": "EASL-EASD-EASO Clinical Practice Guidelines on the management of MASLD: executive "
                    "summary. Diabetologia 2024;67:2375-2392.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11519095/",
    },
}
LIVERTOX_SECTIONS = {"Introduction", "Background", "Hepatotoxicity", "Mechanism of Injury",
                     "Outcome and Management"}

TARGET_CHARS = 1100
MAX_CHARS = 1800


@dataclass
class Chunk:
    id: str
    source: str  # aasld2023 | easl2024 | livertox
    doc_title: str
    section: str
    text: str
    url: str
    kind: str

    @property
    def embed_text(self) -> str:
        # contextual header: retrieval sees where a passage lives, not just its words
        return f"{self.doc_title} | {self.section}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


def _split_long(text: str, limit: int = MAX_CHARS) -> Iterator[str]:
    if len(text) <= limit:
        yield text
        return
    # rows/lines first, then bullets, then sentences; recurse until every piece fits
    for pattern, sep in ((r"\n", "\n"), (r"\s*•\s*", "\n• "), (r"(?<=[.!?\]])\s+", " ")):
        pieces = [p for p in re.split(pattern, text) if p.strip()]
        if len(pieces) > 1:
            break
    else:
        yield from (text[i:i + limit] for i in range(0, len(text), limit))
        return
    pieces = [q for p in pieces for q in (_split_long(p, limit) if len(p) > limit else [p])]
    buf: list[str] = []
    size = 0
    for piece in pieces:
        if buf and size + len(piece) + len(sep) > limit:
            yield sep.join(buf)
            buf, size = [], 0
        buf.append(piece)
        size += len(piece) + len(sep)
    if buf:
        yield sep.join(buf)


def chunk_blocks(blocks: Iterable[Block], *, source: str, doc_title: str, url: str, prefix: str) -> list[Chunk]:
    """Greedy merge of consecutive paragraphs within a section; tables and boxes stand alone."""
    chunks: list[Chunk] = []
    buf: list[str] = []
    cur_path: tuple[str, ...] | None = None
    cur_id = ""

    def flush() -> None:
        if buf:
            text = " ".join(buf)
            for part in _split_long(text):
                chunks.append(Chunk(f"{prefix}-{len(chunks):04d}", source, doc_title,
                                    " > ".join(cur_path or ()), part, f"{url}#{cur_id}" if cur_id else url,
                                    "text"))
            buf.clear()

    for b in blocks:
        path = tuple(b.section_path)
        if b.kind in ("table", "box"):
            flush()
            for part in _split_long(b.text):
                chunks.append(Chunk(f"{prefix}-{len(chunks):04d}", source, doc_title, " > ".join(path), part,
                                    f"{url}#{b.section_id}" if b.section_id else url, b.kind))
            continue
        if path != cur_path or sum(len(x) for x in buf) + len(b.text) > TARGET_CHARS:
            flush()
            cur_path, cur_id = path, b.section_id
        buf.append(b.text)
    flush()
    return chunks


def guideline_chunks(guideline_dir: Path) -> list[Chunk]:
    out: list[Chunk] = []
    for pmcid, meta in GUIDELINES.items():
        path = guideline_dir / f"{pmcid}.xml"
        if not path.exists():
            continue
        _, blocks = parse_article(path.read_text(encoding="utf-8"))
        out += chunk_blocks(blocks, source=meta["source"], doc_title=meta["short"], url=meta["url"],
                            prefix=meta["source"])
    return out


def livertox_chunks(livertox_dir: Path) -> list[Chunk]:
    out: list[Chunk] = []
    for f in sorted(livertox_dir.glob("*.nxml")):
        try:
            title, blocks = parse_book_part(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        keep = [b for b in blocks if b.section_path and b.section_path[-1] in LIVERTOX_SECTIONS]
        if not keep:
            continue
        url = f"https://www.ncbi.nlm.nih.gov/books/n/livertox/{f.stem}/"
        for c in chunk_blocks(keep, source="livertox", doc_title=f"LiverTox: {title}", url=url,
                              prefix=f"livertox-{f.stem}"):
            c.section = c.section.removeprefix("OVERVIEW > ")
            out.append(c)
    return out
