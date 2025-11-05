from abc import ABC, abstractmethod
import numpy as np


class BaseEmbedder(ABC):
    """
    Abstract base class for any text embedding model.

    Subclasses must implement methods to encode text into vectors and
    report embedding dimensionality.
    """

    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        Convert a single text string into a vector embedding.

        Args:
            text: Input text to embed.

        Returns:
            np.ndarray: The resulting embedding vector (dtype=float32).
        """
        ...

    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality of the embedding vectors produced by this model.

        Returns:
            int: Embedding dimension.
        """
        ...

