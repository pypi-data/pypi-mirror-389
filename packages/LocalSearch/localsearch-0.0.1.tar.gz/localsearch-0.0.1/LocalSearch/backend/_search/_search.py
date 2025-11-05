
import numpy as np


from LocalSearch.backend.embeddings.BaseEmbeddings import BaseEmbedder
from LocalSearch.backend.vector_store.BaseVectorStore import BaseVectorStore


# Search function
def _search_query(
    query: str,
    embedder: BaseEmbedder,
    vector_store: BaseVectorStore,
    top_k: int = 5,
) -> list[dict]:
    """
    Perform a semantic search for a query using delegated classes.

    Args:
        query (str): The search query string.
        embedder (BaseEmbedder): Initialized embedding delegate.
        vector_store (BaseVectorStore): Vector store delegate.
        top_k (int): Number of nearest neighbors to return.

    Returns:
        list[dict]: Top-k results containing file, chunk_index, text, and score.
    """

    # 1. Embed the query
    query_vector = embedder.encode(query).astype(np.float32).reshape(1, -1)

    # 2. Search top-k in the vector store
    search_results = vector_store.search(query_vector, top_k)

    # 3. Extract relevant info from search results
    results = []
    for item in search_results:
        metadata = item.get("metadata", {})
        results.append({
            "file": metadata.get("file"),
            "chunk_index": metadata.get("chunk_index"),
            "text": metadata.get("text"),
            "score": item.get("score")
        })

    return results


