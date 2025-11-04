from typing import Any, Dict, List
from .retriever import Retriever
from .reranker import Reranker
from .evaluation import Evaluator


class RAGPipeline:
    """
    Core Retrieval-Augmented Generation pipeline.
    Simplified (no generator). It retrieves, reranks, and evaluates.
    """

    def __init__(self, retriever: Retriever, reranker: Reranker, evaluator: Evaluator):
        self.retriever = retriever
        self.reranker = reranker
        self.evaluator = evaluator

    def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        # Retrieve documents
        retrieved_docs = self.retriever.retrieve(query, top_k=top_k)
        # Rerank
        reranked_docs = self.reranker.rerank(query, retrieved_docs)

        # Use top document as pseudo-answer
        if reranked_docs:
            answer = reranked_docs[0]["text"]
        else:
            answer = ""

        context = "\n".join([d["text"] for d in reranked_docs])
        metrics = self.evaluator.evaluate(query, answer, context)

        return {
            "query": query,
            "answer": answer,
            "docs": reranked_docs,
            "metrics": metrics,
        }
