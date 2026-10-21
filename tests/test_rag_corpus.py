from liverbuddy.rag.corpus import MAX_CHARS, _split_long, chunk_blocks
from liverbuddy.rag.jats import Block, parse_article

ARTICLE = """<article><front><article-meta><title-group><article-title>Test Guideline</article-title>
</title-group></article-meta></front><body>
<sec id="S1"><title>Screening</title>
  <p>General population screening for steatotic liver disease is not advised in this guideline.</p>
  <p>High-risk individuals such as those with type 2 diabetes should be screened for advanced fibrosis.</p>
</sec>
<sec id="S2"><title>Treatment</title>
  <sec id="S3"><title>Lifestyle</title><p>Weight loss of 7-10 percent improves steatohepatitis and fibrosis.</p></sec>
</sec>
<sec><title>References</title><p>Should never be indexed because it is back matter of the article.</p></sec>
</body><floats-group>
<boxed-text id="BX1"><sec><title>Guidance statements:</title><list>
  <list-item><p>Weight loss of 7-10 percent is recommended for people with overweight and MASLD.</p></list-item>
  <list-item><p>A Mediterranean diet pattern is recommended to reduce liver fat content.</p></list-item>
</list></sec></boxed-text>
</floats-group></article>"""


def test_parse_article_sections_skips_back_matter_and_attaches_floats():
    title, blocks = parse_article(ARTICLE)
    assert title == "Test Guideline"
    assert not any("back matter" in b.text for b in blocks)
    box = next(b for b in blocks if b.kind == "box")
    # uncited box lands in the most similar body section (lifestyle/weight loss)
    assert box.section_path[:2] == ["Treatment", "Lifestyle"]
    assert box.text.count("\n") >= 1  # one recommendation per line


def test_chunk_blocks_merges_within_section_and_keeps_boxes_separate():
    _, blocks = parse_article(ARTICLE)
    chunks = chunk_blocks(blocks, source="t", doc_title="T", url="https://x/", prefix="t")
    sections = [c.section for c in chunks]
    assert sections.count("Screening") == 1  # two short paragraphs merged
    assert any(c.kind == "box" for c in chunks)
    assert chunks[0].url == "https://x/#S1"
    assert chunks[0].embed_text.startswith("T | Screening")


def test_split_long_respects_limit_for_bullets_and_sentences():
    bullets = "Header" + "".join(f"• item number {i} with some words " * 3 for i in range(200))
    sentences = " ".join(f"Sentence {i} has several words in it." for i in range(400))
    for text in (bullets, sentences):
        parts = list(_split_long(text))
        assert len(parts) > 1
        assert max(len(p) for p in parts) <= MAX_CHARS


def test_blocks_dataclass_roundtrip():
    b = Block(["A"], "S1", "text " * 20, "paragraph")
    assert chunk_blocks([b], source="s", doc_title="D", url="u", prefix="p")[0].section == "A"
