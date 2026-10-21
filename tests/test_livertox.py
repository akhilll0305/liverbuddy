import json

import pytest

from liverbuddy.drugs.livertox import LiverTox, parse_monograph

MONOGRAPH = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book-part-wrapper PUBLIC "-//NLM//DTD BITS Book Interchange DTD v2.0 20151225//EN" "x.dtd">
<book-part-wrapper id="Atorvastatin"><book-part><book-part-meta><title-group><title>Atorvastatin</title>
</title-group></book-part-meta><body>
<sec><title>OVERVIEW</title>
  <sec><title>Introduction</title><p>Atorvastatin is a commonly used statin.</p></sec>
  <sec><title>Hepatotoxicity</title><p>Mild ALT elevations occur.</p>
  <p>Likelihood score: A (well known cause of clinically apparent liver injury).</p></sec>
</sec>
<sec><title>PRODUCT INFORMATION</title>
  <p><bold>REPRESENTATIVE TRADE NAMES</bold></p><p>Atorvastatin &#x02013; Generic, Lipitor&#x000ae;</p>
  <p><bold>DRUG CLASS</bold></p><p>Antilipemic Agents</p>
</sec></body></book-part></book-part-wrapper>"""


def test_parse_monograph_extracts_score_brand_and_class():
    rec = parse_monograph(MONOGRAPH, "Atorvastatin")
    assert rec.name == "Atorvastatin"
    assert rec.likelihood == "A"
    assert rec.trade_names == ["Lipitor"]
    assert rec.drug_class == "Antilipemic Agents"
    assert "statin" in rec.summary


def test_parse_monograph_without_score_is_skipped():
    assert parse_monograph(MONOGRAPH.replace("Likelihood score: A", "No score"), "X") is None


@pytest.fixture
def lt(tmp_path):
    def rec(name, score, trade=()):
        return {"id": name, "name": name, "trade_names": list(trade), "drug_class": "", "likelihood": score,
                "likelihood_all": [score], "summary": "", "url": "u"}
    table = [rec("Atorvastatin", "A", ["Lipitor"]), rec("Acetaminophen", "A"), rec("Metformin", "B"),
             rec("Vitamin E", "E")]
    p = tmp_path / "drugs.json"
    p.write_text(json.dumps(table))
    return LiverTox(p)


@pytest.mark.parametrize("query,expected", [
    ("Lipitor", "Atorvastatin"),
    ("atorvastatin 20 mg", "Atorvastatin"),
    ("atrovastatin", "Atorvastatin"),       # misspelling
    ("Crocin", "Acetaminophen"),            # Indian brand alias
    ("paracetamol 500mg", "Acetaminophen"),  # INN alias
])
def test_lookup_matches(lt, query, expected):
    r = lt.lookup(query)
    assert r.matched and r.record.name == expected


def test_lookup_rejects_unknown_drug(lt):
    r = lt.lookup("xyzzy")
    assert not r.matched and r.record is None


def test_high_risk_drug_note_discourages_self_discontinuation(lt):
    assert "Do not stop" in lt.lookup("Lipitor").note
