"""Deterministic drug-induced liver injury (DILI) lookup over NIH LiverTox (public domain).

The hepatotoxicity category shown to users is LiverTox's own expert likelihood score (A-E), read
from the monograph text. The LLM never assigns it.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from rapidfuzz import fuzz, process

from liverbuddy.drugs.synonyms import ALIASES
from liverbuddy.rag.jats import clean, element_text

LIVERTOX_URL = "https://www.ncbi.nlm.nih.gov/books/NBK547852/"
CATEGORY_MEANING = {
    "A": "Well established cause of clinically apparent liver injury (over 50 published cases).",
    "B": "Highly likely cause of clinically apparent liver injury (12-50 cases).",
    "C": "Probable cause of clinically apparent liver injury (fewer than 12 cases).",
    "D": "Possible rare cause of clinically apparent liver injury.",
    "E": "Unlikely cause of clinically apparent liver injury.",
    "E*": "Unproven but suspected rare cause of clinically apparent liver injury.",
    "D*": "Possible rare cause of clinically apparent liver injury (limited evidence).",
    "X": "Unknown: too new or too rarely used to judge.",
}
_SCORE = re.compile(r"Likelihood scores?:?\s*([A-EX])(\*)?(\s*\[[^\]]*\])?", re.I)


class DrugRecord(BaseModel):
    id: str
    name: str
    trade_names: list[str]
    drug_class: str
    likelihood: str  # A, B, C, D, E, E*, X
    likelihood_all: list[str]
    summary: str
    url: str


class DrugLookup(BaseModel):
    query: str
    matched: bool
    match_score: float
    record: DrugRecord | None
    category_meaning: str | None
    alternatives: list[str] = []
    note: str


def parse_monograph(xml_text: str, chapter_id: str) -> DrugRecord | None:
    import xml.etree.ElementTree as ET

    xml_text = re.sub(r"<!DOCTYPE[^>]*>", "", xml_text)
    root = ET.fromstring(xml_text)
    body = root.find(".//body")
    if body is None:
        return None
    full = element_text(body)
    scores = [(m.group(1).upper() + (m.group(2) or "")) for m in _SCORE.finditer(full)]
    if not scores:
        return None
    title_el = root.find(".//book-part-meta//title")
    name = element_text(title_el) if title_el is not None else chapter_id
    intro = ""
    for sec in body.iter("sec"):
        t = sec.find("title")
        if t is not None and element_text(t).lower() == "introduction":
            intro = " ".join(element_text(p) for p in sec.findall("p"))
            break
    trade, klass = [], ""
    paras = [element_text(p) for p in body.iter("p")]
    for i, p in enumerate(paras):
        if p.upper() == "REPRESENTATIVE TRADE NAMES" and i + 1 < len(paras):
            # "Atorvastatin – Generic, Lipitor®" (one paragraph per ingredient)
            for line in paras[i + 1:i + 4]:
                if line.upper() == "DRUG CLASS":
                    break
                rhs = re.split(r"\s[–-]\s", line, maxsplit=1)[-1]
                trade += [clean(t).strip("®™ ") for t in rhs.split(",")
                          if t.strip().lower() not in ("generic", "various trade names", "various")]
        if p.upper() == "DRUG CLASS" and i + 1 < len(paras):
            klass = paras[i + 1]
    # most monographs give one score; combination/class chapters give several - keep the most severe
    worst = min(scores, key=lambda s: "ABCDE*X".index(s[0]) if s[0] in "ABCDEX" else 9)
    return DrugRecord(id=chapter_id, name=name, trade_names=sorted({t for t in trade if 1 < len(t) < 40}),
                      drug_class=klass, likelihood=worst, likelihood_all=scores, summary=intro[:1200],
                      url=f"https://www.ncbi.nlm.nih.gov/books/n/livertox/{chapter_id}/")


def build_drug_table(livertox_dir: Path, out_path: Path) -> int:
    records = []
    for f in sorted(livertox_dir.glob("*.nxml")):
        try:
            rec = parse_monograph(f.read_text(encoding="utf-8"), f.stem)
        except Exception:  # a few chapters are malformed; skip rather than fail the build
            continue
        if rec:
            records.append(rec.model_dump())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(records, indent=1), encoding="utf-8")
    return len(records)


class LiverTox:
    def __init__(self, table_path: Path):
        self.records = [DrugRecord(**r) for r in json.loads(table_path.read_text(encoding="utf-8"))]
        self._names: list[str] = []
        self._owner: list[int] = []
        by_name = {r.name: i for i, r in enumerate(self.records)}
        for i, r in enumerate(self.records):
            for n in [r.name, *r.trade_names]:
                self._names.append(n.lower())
                self._owner.append(i)
        for alias, target in ALIASES.items():
            if target in by_name:
                self._names.append(alias)
                self._owner.append(by_name[target])

    def lookup(self, query: str, min_score: float = 85.0) -> DrugLookup:
        q = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|iu|ml|%)\b", "", query.lower()).strip(" ,.")
        hits = process.extract(q, self._names, scorer=fuzz.WRatio, limit=5)
        if not hits:
            return DrugLookup(query=query, matched=False, match_score=0, record=None, category_meaning=None,
                              note="No LiverTox entry found.")
        # very short names ("BAL", "INH") only count on an exact match, or "football" -> "BAL"
        hits = [h for h in hits if len(h[0]) >= 5 or h[0] == q] or hits[:0]
        if not hits:
            return DrugLookup(query=query, matched=False, match_score=0, record=None, category_meaning=None,
                              note="No LiverTox entry found.")
        best_name, score, idx = hits[0]
        rec = self.records[self._owner[idx]]
        alts = list(dict.fromkeys(self.records[self._owner[i]].name for _, _, i in hits[1:]
                                  if self._owner[i] != self._owner[idx]))[:3]
        if score < min_score:
            return DrugLookup(query=query, matched=False, match_score=score, record=None, category_meaning=None,
                              alternatives=[rec.name, *alts],
                              note="No confident match. Check the spelling or use the generic name.")
        note = f"LiverTox likelihood score {rec.likelihood}. Source: NIH LiverTox ({rec.url})."
        if rec.likelihood in ("A", "B"):
            note += " Do not stop a prescribed medicine on your own. Discuss liver monitoring with your prescriber."
        return DrugLookup(query=query, matched=True, match_score=score, record=rec,
                          category_meaning=CATEGORY_MEANING.get(rec.likelihood), alternatives=alts, note=note)


@lru_cache
def get_livertox(table_path: str) -> LiverTox:
    return LiverTox(Path(table_path))
