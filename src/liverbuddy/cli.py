"""`liverbuddy` command line: download data, build indexes, train, evaluate, serve."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

import httpx

from liverbuddy.config import ROOT, get_settings
from liverbuddy.ml.cohort import NHANES_BASE, NHANES_FILES

SOURCES = {
    "livertox/livertox.tar.gz": "https://ftp.ncbi.nlm.nih.gov/pub/litarch/29/31/livertox_NBK547852.tar.gz",
    "fdc/sr_legacy.zip": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip",
    "nutrition5k/dish_metadata_cafe1.csv": "https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/"
                                           "metadata/dish_metadata_cafe1.csv",
    "guidelines/PMC11519095.xml": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11519095/fullTextXML",
    "guidelines/PMC10735173.xml": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=10735173"
                                  "&rettype=xml",
    **{f"nhanes/{f}.xpt": f"{NHANES_BASE}/{f}.xpt" for f in NHANES_FILES},
}


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=600,
                      headers={"User-Agent": "liverbuddy/2.0 (research)"}) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    tmp.replace(dest)


def cmd_download(args) -> None:
    raw = get_settings().raw_dir
    for rel, url in SOURCES.items():
        dest = raw / rel
        if dest.exists() and not args.force:
            print(f"  ok      {rel}")
            continue
        print(f"  fetch   {rel}")
        _fetch(url, dest)
    lt = raw / "livertox"
    if not (lt / "livertox_NBK547852").exists():
        print("  extract LiverTox")
        with tarfile.open(lt / "livertox.tar.gz") as tar:
            tar.extractall(lt, filter="data")
    fdc = raw / "fdc"
    if not any(fdc.glob("FoodData_Central_*")):
        print("  extract USDA FDC")
        with zipfile.ZipFile(fdc / "sr_legacy.zip") as z:
            z.extractall(fdc)


def cmd_pull_models(args) -> None:
    s = get_settings()
    for model in dict.fromkeys([s.ollama_chat_model, s.ollama_embed_model] + ([s.ollama_vision_model]
                                                                               if args.vision else [])):
        print(f"pulling {model} from {s.ollama_url} ...")
        r = httpx.post(f"{s.ollama_url}/api/pull", json={"name": model, "stream": False}, timeout=3600)
        r.raise_for_status()


def cmd_build_index(args) -> None:
    from liverbuddy.drugs.livertox import build_drug_table
    from liverbuddy.llm import get_llm
    from liverbuddy.nutrition.fdc import FoodMatcher, build_food_table
    from liverbuddy.rag.corpus import guideline_chunks, livertox_chunks
    from liverbuddy.rag.index import HybridIndex

    s = get_settings()
    llm = get_llm()
    embed_model = s.gemini_embed_model if s.llm_provider == "gemini" else s.ollama_embed_model
    lt_dir = s.raw_dir / "livertox" / "livertox_NBK547852"
    fdc_dir = next((s.raw_dir / "fdc").glob("FoodData_Central_*"))
    t = time.time()
    print(f"drug table: {build_drug_table(lt_dir, s.index_dir / 'livertox_drugs.json')} drugs")
    print(f"food table: {build_food_table(fdc_dir, s.index_dir / 'foods.json')} foods")
    for name, chunks in (("guidelines", guideline_chunks(s.raw_dir / "guidelines")),
                         ("livertox", livertox_chunks(lt_dir))):
        HybridIndex.build(chunks, llm, embed_model).save(s.index_dir, name)
        print(f"index {name}: {len(chunks)} chunks")
    FoodMatcher.load(s.index_dir / "foods.json").embed_all(llm, s.index_dir / "foods.npy")
    print(f"food embeddings done; total {time.time() - t:.0f}s")


def cmd_train(args) -> None:
    from liverbuddy.ml.train import train_all

    s = get_settings()
    train_all(s.raw_dir / "nhanes", s.model_dir, ROOT / "docs")


def cmd_eval(args) -> None:
    from liverbuddy.evals.run import main as run_evals

    run_evals(args.suites, limit=args.limit)


def cmd_serve(args) -> None:
    import uvicorn

    uvicorn.run("liverbuddy.api.server:root", host=args.host, port=args.port, reload=args.reload)


def cmd_ui(args) -> None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "streamlit_app.py")], check=False)


def cmd_traces(args) -> None:
    from liverbuddy.observability import summarize

    print(json.dumps(summarize(get_settings().artifacts_dir / "traces.jsonl"), indent=2))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="liverbuddy", description=__doc__)
    sub = p.add_subparsers(required=True)
    d = sub.add_parser("download", help="download public datasets (~250 MB)")
    d.add_argument("--force", action="store_true")
    d.set_defaults(fn=cmd_download)
    pm = sub.add_parser("pull-models", help="pull the configured Ollama models")
    pm.add_argument("--vision", action="store_true", help="also pull the vision model (~3 GB)")
    pm.set_defaults(fn=cmd_pull_models)
    sub.add_parser("build-index", help="build drug/food tables and RAG indexes").set_defaults(fn=cmd_build_index)
    sub.add_parser("train", help="train NHANES risk models and write the model card").set_defaults(fn=cmd_train)
    e = sub.add_parser("eval", help="run evaluation suites")
    e.add_argument("suites", nargs="*", default=[])
    e.add_argument("--limit", type=int, default=None)
    e.set_defaults(fn=cmd_eval)
    sv = sub.add_parser("serve", help="run the API")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--reload", action="store_true")
    sv.set_defaults(fn=cmd_serve)
    sub.add_parser("ui", help="run the Streamlit app").set_defaults(fn=cmd_ui)
    sub.add_parser("traces", help="summarise LLM/tool latency and tokens").set_defaults(fn=cmd_traces)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
