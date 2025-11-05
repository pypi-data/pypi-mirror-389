import numpy as np
from ragmint.core.retriever import Retriever


def test_retrieve_basic():
    embeddings = [np.random.rand(5) for _ in range(3)]
    docs = ["doc A", "doc B", "doc C"]
    retriever = Retriever(embeddings, docs)

    results = retriever.retrieve("sample query", top_k=2)
    assert isinstance(results, list)
    assert len(results) == 2
    assert "text" in results[0]
    assert "score" in results[0]
