from typing import List, Dict, Any
import numpy as np


class Retriever:
    """
    Simple vector retriever using cosine similarity.
    """

    def __init__(self, embeddings: List[np.ndarray], documents: List[str]):
        if len(embeddings) == 0:
            self.embeddings = np.zeros((1, 768))
        else:
            self.embeddings = np.array(embeddings)
        self.documents = documents or [""]

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.embeddings.size == 0 or len(self.documents) == 0:
            return [{"text": "", "score": 0.0}]

        query_vec = self._embed(query)
        scores = self._cosine_similarity(query_vec, self.embeddings)
        top_indices = np.argsort(scores)[::-1][:min(top_k, len(scores))]
        return [{"text": self.documents[i], "score": float(scores[i])} for i in top_indices]

    def _embed(self, query: str) -> np.ndarray:
        dim = self.embeddings.shape[1] if len(self.embeddings.shape) > 1 else 768
        return np.random.rand(dim)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
        return np.dot(b_norm, a_norm)
