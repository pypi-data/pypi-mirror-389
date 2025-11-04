import os
import json
from ragmint.tuner import RAGMint


def setup_validation_file(tmp_path):
    data = [
        {"question": "What is AI?", "answer": "Artificial Intelligence"},
        {"question": "Define ML", "answer": "Machine Learning"}
    ]
    file = tmp_path / "validation_qa.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return str(file)


def setup_docs(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "doc1.txt").write_text("This is about Artificial Intelligence.")
    (corpus / "doc2.txt").write_text("This text explains Machine Learning.")
    return str(corpus)


def test_optimize_random(tmp_path):
    docs_path = setup_docs(tmp_path)
    val_file = setup_validation_file(tmp_path)

    rag = RAGMint(
        docs_path=docs_path,
        retrievers=["faiss"],
        embeddings=["openai/text-embedding-3-small"],
        rerankers=["mmr"]
    )

    best, results = rag.optimize(validation_set=val_file, metric="faithfulness", trials=2)
    assert isinstance(best, dict)
    assert isinstance(results, list)
