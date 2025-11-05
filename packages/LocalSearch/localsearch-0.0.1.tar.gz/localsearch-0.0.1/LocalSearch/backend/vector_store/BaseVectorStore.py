from abc import ABC, abstractmethod
from typing import List, Dict, Set, TypedDict
import numpy as np

class SearchResult(TypedDict):
    """TypedDict for a single search result returned by the vector store."""
    id: int
    score: float
    metadata: dict

class IndexPreparation(TypedDict):
    """
    TypedDict for the dictionary returned by prepare_index().
    Ensures a strict format for generic utilities.
    """
    index: object  # Internal index object; type depends on implementation
    current_files: Set[str]
    used_ids: Set[int]

class BaseVectorStore(ABC):
    """
    Abstract base class for any vector store.

    Any implementation must provide all of the following methods to be compatible
    with _process_files and other utilities.
    """

    @abstractmethod
    def add(self, vectors: np.ndarray, ids: np.ndarray, metadata: List[dict]):
        """
        Add vectors with corresponding IDs and associated metadata.

        Args:
            vectors (np.ndarray): 2D array of vectors to add.
            ids (np.ndarray): 1D array of unique IDs for each vector.
            metadata (List[dict]): List of metadata dicts, one per vector.
        """
        ...

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int) -> List[SearchResult]:
        """
        Return the top_k nearest neighbors for a query vector.

        Args:
            query_vector (np.ndarray): Single query vector.
            top_k (int): Number of nearest neighbors to return.

        Returns:
            List[SearchResult]: List of search results with keys 'id', 'score', 'metadata'.
        """
        ...

    @abstractmethod
    def remove_by_id(self, vector_id: int) -> None:
        """
        Remove a vector from the store by its ID.

        Args:
            vector_id (int): ID of the vector to remove.
        """
        ...

    @abstractmethod
    def save(self, path: str):
        """
        Persist the store to disk.

        Args:
            path (str): File path or directory to save the store.
        """
        ...

    @abstractmethod
    def load(self, path: str):
        """
        Load the store from disk.

        Args:
            path (str): File path or directory to load the store from.
        """
        ...

    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality of vectors supported by this store.

        Returns:
            int: Embedding vector dimensionality.
        """
        ...

    @abstractmethod
    def get_all_ids(self) -> Set[int]:
        """
        Return a set of all vector IDs currently stored.

        Returns:
            Set[int]: All IDs in the store.
        """
        ...

    @abstractmethod
    def prepare_index(self, directory_path: str, recursive: bool = True) -> IndexPreparation:
        """
        Prepare or load the index from a directory.

        Args:
            directory_path (str): Directory containing files to index.
            recursive (bool): Whether to scan subdirectories.

        Returns:
            IndexPreparation: Dict with keys:
                - 'index': internal index object
                - 'current_files': set of files present in the directory
                - 'used_ids': set of vector IDs already in the index
        """
        ...
