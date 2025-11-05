import numpy as np
from ragmint.core.pipeline import RAGPipeline
from ragmint.core.retriever import Retriever
from ragmint.core.reranker import Reranker
from ragmint.core.evaluation import Evaluator


def test_pipeline_run():
    docs = ["doc1 text", "doc2 text"]
    embeddings = [np.random.rand(4) for _ in range(2)]
    retriever = Retriever(embeddings, docs)
    reranker = Reranker("mmr")
    evaluator = Evaluator()
    pipeline = RAGPipeline(retriever, reranker, evaluator)

    result = pipeline.run("what is doc1?")
    assert "query" in result
    assert "answer" in result
    assert "metrics" in result
