import numpy as np
from sentence_transformers import SentenceTransformer

from LocalSearch.backend.embeddings.BaseEmbeddings import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Embedder using a Sentence-Transformers model.

    Default model: "all-MiniLM-L6-v2"
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SentenceTransformer embedder.

        Args:
            model_name: Name of the sentence-transformers model to use.
        """
        self.model = SentenceTransformer(model_name)
        self._dim: int = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str) -> np.ndarray:
        """
        Encode a text string into a vector embedding.

        Args:
            text: Input string to encode.

        Returns:
            np.ndarray: Embedding vector as float32 array.
        """
        vector = self.model.encode(text)
        return np.array(vector, dtype=np.float32)

    def dimension(self) -> int:
        """
        Return the dimensionality of the embedding vectors.

        Returns:
            int: Embedding dimension.
        """
        return self._dim