import numpy as np


class EmbeddingModel:
    """
    Wrapper for embedding backends (OpenAI, HuggingFace, etc.)
    """

    def __init__(self, backend: str = "dummy"):
        self.backend = backend

    def encode(self, texts):
        if self.backend == "openai":
            # Example placeholder — integrate with actual OpenAI API
            return [np.random.rand(768) for _ in texts]
        elif self.backend == "huggingface":
            return [np.random.rand(768) for _ in texts]
        else:
            return [np.random.rand(768) for _ in texts]
