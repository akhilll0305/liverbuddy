"""Hybrid retrieval: dense embeddings + BM25, fused with reciprocal rank fusion (RRF)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer

from liverbuddy.llm import LLM
from liverbuddy.rag.corpus import Chunk

RRF_K = 60


@dataclass
class Hit:
    chunk: Chunk
    score: float  # fused RRF score
    dense: float  # cosine similarity, used for abstention
    bm25: float


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.vec = CountVectorizer(token_pattern=r"(?u)\b[\w-]+\b", lowercase=True, stop_words="english")
        tf = self.vec.fit_transform(texts).tocsc().astype(np.float32)
        n = tf.shape[0]
        df = np.diff(tf.indptr)
        self.idf = np.log(1 + (n - df + 0.5) / (df + 0.5)).astype(np.float32)
        lengths = np.asarray(tf.sum(axis=1)).ravel()
        norm = k1 * (1 - b + b * lengths / lengths.mean())
        tf = tf.tocoo()
        weights = tf.data * (k1 + 1) / (tf.data + norm[tf.row])
        self.matrix = sparse.csr_matrix((weights, (tf.row, tf.col)), shape=tf.shape)

    def scores(self, query: str) -> np.ndarray:
        q = self.vec.transform([query])
        q.data[:] = 1.0
        q = q.multiply(self.idf).tocsr()
        return np.asarray(self.matrix @ q.T.toarray()).ravel()


class HybridIndex:
    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray, embed_model: str):
        self.chunks = chunks
        self.embeddings = embeddings
        self.embed_model = embed_model
        self.bm25 = BM25([c.embed_text for c in chunks])
        self.sources = np.array([c.source for c in chunks])

    @classmethod
    def build(cls, chunks: list[Chunk], llm: LLM, embed_model: str) -> HybridIndex:
        emb = llm.embed([c.embed_text for c in chunks], kind="document")
        return cls(chunks, emb, embed_model)

    def save(self, directory: Path, name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / f"{name}.npy", self.embeddings.astype(np.float16))
        with (directory / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        (directory / f"{name}.meta.json").write_text(json.dumps({"embed_model": self.embed_model,
                                                                  "n_chunks": len(self.chunks)}))

    @classmethod
    def load(cls, directory: Path, name: str) -> HybridIndex:
        chunks = [Chunk(**json.loads(line)) for line in
                  (directory / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
        emb = np.load(directory / f"{name}.npy").astype(np.float32)
        meta = json.loads((directory / f"{name}.meta.json").read_text())
        return cls(chunks, emb, meta["embed_model"])

    def search(self, query: str, llm: LLM, k: int = 6, sources: list[str] | None = None,
               candidates: int = 50) -> list[Hit]:
        q = llm.embed([query], kind="query")[0]
        if q.shape[0] != self.embeddings.shape[1]:
            raise ValueError(f"Query embedding dim {q.shape[0]} != index dim {self.embeddings.shape[1]}. "
                             f"Index was built with {self.embed_model}; rebuild it for this provider.")
        dense = self.embeddings @ q
        lexical = self.bm25.scores(query)
        mask = np.isin(self.sources, sources) if sources else np.ones(len(self.chunks), bool)
        dense_m = np.where(mask, dense, -np.inf)
        lex_m = np.where(mask, lexical, -np.inf)
        fused: dict[int, float] = {}
        for ranking in (np.argsort(-dense_m)[:candidates], np.argsort(-lex_m)[:candidates]):
            for rank, idx in enumerate(ranking):
                if np.isfinite(dense_m[idx]):
                    fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (RRF_K + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [Hit(self.chunks[i], fused[i], float(dense[i]), float(lexical[i])) for i in top]

