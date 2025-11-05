import os
import json
from typing import List, Optional, Set
import numpy as np
import faiss

from LocalSearch.backend.vector_store.BaseVectorStore import BaseVectorStore, SearchResult, IndexPreparation


class FaissVectorStore(BaseVectorStore):
    """
    FAISS-based vector store with optional metadata persistence.
    """

    def __init__(self, dim: int):
        """
        Initialize FAISS vector store.

        Args:
            dim: Dimensionality of the vectors.
        """
        self.embed_dim = dim
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        self.id_to_metadata: dict[str, dict] = {}
        self.index_path: Optional[str] = None
        self.metadata_path: Optional[str] = None

    # -----------------------------
    # Index preparation
    # -----------------------------
    def prepare_index(self, directory_path: str, recursive: bool = True) -> IndexPreparation:
        """
        Load existing index if available, else create a new one.

        Args:
            directory_path: Directory to store/load index.
            recursive: Whether to scan subdirectories.

        Returns:
            IndexPreparation: Dict with keys:
                - index: FAISS index object
                - current_files: set of valid files
                - used_ids: set of IDs already in index
        """
        self.index_path = os.path.join(directory_path, "vector.index")
        self.metadata_path = self.index_path + ".meta.json"

        # Load or create index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            if not isinstance(self.index, faiss.IndexIDMap):
                self.index = faiss.IndexIDMap(self.index)
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.id_to_metadata = json.load(f)
        else:
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.embed_dim))
            self.id_to_metadata = {}

        # Collect valid files
        used_ids = set(map(int, self.id_to_metadata.keys()))
        current_files = set()
        for root, _, files in os.walk(directory_path):
            if not recursive and root != directory_path:
                continue
            for f in files:
                if f in ["metadata.json", "chunk_mapping.json", "vector.index", "vector.index.meta.json"]:
                    continue
                current_files.add(os.path.join(root, f))

        return {"index": self.index, "current_files": current_files, "used_ids": used_ids}

    # -----------------------------
    # Add / Search / Remove
    # -----------------------------
    def add(self, vectors: np.ndarray, ids: np.ndarray, metadata: Optional[List[dict]] = None):
        """
        Add vectors with IDs and optional metadata.

        Args:
            vectors: Array of shape (n, dim)
            ids: Array of integer IDs
            metadata: Optional list of metadata dictionaries
        """
        self.index.add_with_ids(vectors.astype(np.float32), ids.astype(np.int64))
        if metadata:
            for i, id_val in enumerate(ids):
                self.id_to_metadata[str(int(id_val))] = metadata[i]

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[SearchResult]:
        """
        Search for nearest neighbors of a query vector.

        Args:
            query_vector: Array of shape (1, dim)
            top_k: Number of neighbors to return

        Returns:
            List[SearchResult]: List of dictionaries with keys 'id', 'score', 'metadata'
        """
        distances, indices = self.index.search(query_vector.astype(np.float32), top_k)
        results: List[SearchResult] = []

        for id_val, dist in zip(indices[0], distances[0]):
            if id_val == -1:
                continue
            md = self.id_to_metadata.get(str(int(id_val)), {})
            results.append({"id": int(id_val), "score": float(dist), "metadata": md})

        return results

    def remove_by_id(self, vector_id: int) -> None:
        """Remove a vector by its ID and delete associated metadata."""
        try:
            self.index.remove_ids(np.array([vector_id], dtype=np.int64))
            self.id_to_metadata.pop(str(vector_id), None)
        except Exception as e:
            print(f"[FAISS] Failed to remove vector {vector_id}: {e}")

    # -----------------------------
    # Persistence
    # -----------------------------
    def save(self, path: Optional[str] = None):
        """
        Save FAISS index and metadata mapping.

        Args:
            path: Optional path to save index (overrides self.index_path)
        """
        if path:
            self.index_path = path
            self.metadata_path = path + ".meta.json"
        elif not self.index_path:
            raise ValueError("No index_path provided to save FAISS index.")

        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.id_to_metadata, f, indent=2)

    def load(self, path: str):
        """Load FAISS index and associated metadata."""
        self.index_path = path
        self.metadata_path = path + ".meta.json"
        self.index = faiss.read_index(path)
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.id_to_metadata = json.load(f)

    # -----------------------------
    # Misc
    # -----------------------------
    def dimension(self) -> int:
        """Return dimensionality of vectors in this store."""
        return self.embed_dim

    def get_all_ids(self) -> Set[int]:
        """Return a set of all vector IDs currently stored."""
        return set(map(int, self.id_to_metadata.keys()))
