import os
from typing import List, Tuple, Set, Dict, Optional

import numpy as np

from LocalSearch.backend.embeddings.BaseEmbeddings import BaseEmbedder
from LocalSearch.backend.metadata_store.BaseMetaDataStore import BaseMetadataStore
from LocalSearch.backend.vector_store.BaseVectorStore import BaseVectorStore


def _get_file_info(file_path: str) -> dict:
    """
    Retrieve basic file information.

    Args:
        file_path: Path to the file.

    Returns:
        Dictionary with file size and modification time.
    """
    stat = os.stat(file_path)
    return {"size": stat.st_size, "modified": stat.st_mtime}


def _cleanup_deleted_files(
    chunk_mapping: List[dict],
    current_files: Set[str],
    used_ids: Set[int],
    vector_store: BaseVectorStore,
) -> Tuple[List[dict], int]:
    """
    Remove deleted files' vectors from the vector store and return updated mapping.

    Args:
        chunk_mapping: List of existing chunks with file references.
        current_files: Set of files currently present in the directory.
        used_ids: Set of used vector IDs.
        vector_store: Vector store instance.

    Returns:
        Tuple of updated chunk_mapping and next available ID.
    """
    new_chunk_mapping = []

    for chunk in chunk_mapping:
        if chunk["file"] in current_files:
            new_chunk_mapping.append(chunk)
            used_ids.add(chunk["index"])
        else:
            vector_store.remove_by_id(chunk["index"])

    next_id = max(used_ids) + 1 if used_ids else 0
    return new_chunk_mapping, next_id


def _filter_included_files(current_files: Set[str], include_file_types: List[str]) -> Set[str]:
    """
    Filter files by allowed extensions.

    Args:
        current_files: Set of files in the directory.
        include_file_types: List of allowed file extensions.

    Returns:
        Set of filtered file paths.
    """
    allowed = [f for f in current_files if os.path.splitext(f)[1].lower() in include_file_types]
    return set(allowed)


def _process_files(
    current_files: Set[str],
    metadata_store: BaseMetadataStore,
    vector_store: BaseVectorStore,
    extractor,
    embedder: BaseEmbedder,
    force: bool,
    verbose: bool = True,
) -> Tuple[dict, bool]:
    """
    Process files: extract text, split, embed, and store in vector & metadata stores.

    Args:
        current_files: Files to process.
        metadata_store: Metadata store instance.
        vector_store: Vector store instance.
        extractor: Text extractor instance.
        embedder: Embedding model instance.
        force: If True, process all files regardless of modification.
        verbose: If True, prints logs.

    Returns:
        summary: Dict with processed, skipped, and failed files.
        updated: Bool indicating if new/modified files were processed.
    """
    summary = {"processed_files": [], "skipped_files": [], "failed_chunks": []}
    updated = False

    used_ids = set(map(int, vector_store.id_to_metadata.keys())) if hasattr(vector_store, "id_to_metadata") else set()
    next_id = max(used_ids) + 1 if used_ids else 0

    for file_path in current_files:
        try:
            file_info = metadata_store.get_file_info(file_path)
        except Exception as e:
            summary["skipped_files"].append(file_path)
            if verbose:
                print(f"[SKIPPED] Cannot access file {file_path}: {e}")
            continue

        if force or metadata_store.is_modified(file_path, file_info):
            try:
                text = extractor.extract_text(file_path)
            except Exception as e:
                summary["skipped_files"].append(file_path)
                if verbose:
                    print(f"[ERROR] Extraction failed for {file_path}: {e}")
                continue

            if not text.strip():
                summary["skipped_files"].append(file_path)
                continue

            chunks = extractor.split_text(text)

            for idx, chunk in enumerate(chunks):
                try:
                    vector = embedder.encode(chunk)
                    chunk_metadata = {
                        "file": file_path,
                        "chunk_index": idx,
                        "text": chunk
                    }

                    vector_store.add(
                        vectors=np.array([vector]),
                        ids=np.array([next_id]),
                        metadata=[chunk_metadata],
                    )
                    next_id += 1

                except Exception as e:
                    summary["failed_chunks"].append((file_path, idx))
                    if verbose:
                        print(f"[ERROR] Embedding failed for chunk {idx} of {file_path}: {e}")
                    continue

            metadata_store.update(file_path, file_info)
            summary["processed_files"].append(file_path)
            updated = True

            if verbose:
                rel = os.path.relpath(file_path, getattr(extractor, "base_path", "."))
                print(f"[PROCESSED] {rel}")

    return summary, updated


def _save_all(vector_store: BaseVectorStore, metadata_store: BaseMetadataStore):
    """
    Persist vector store and metadata store to disk.

    Args:
        vector_store: Vector store instance.
        metadata_store: Metadata store instance.
    """
    try:
        vector_store.save()
    except Exception as e:
        print(f"[ERROR] Failed to save vector store: {e}")

    try:
        metadata_store.save_metadata(metadata_store.load_metadata())
        metadata_store.save_chunk_mapping(metadata_store.load_chunk_mapping())
    except Exception as e:
        print(f"[ERROR] Failed to save metadata or chunk mapping: {e}")


def _generate_embeddings(
    directory_path: str,
    embedding_model: BaseEmbedder,
    metadata_store: BaseMetadataStore,
    vector_store: BaseVectorStore,
    extractor,
    force: bool = False,
    include_file_types: List[str] = [".txt", ".pdf", ".html"],
    recursive: bool = True,
    verbose: bool = True,
) -> dict:
    """
    Generate or update embeddings for all files in a directory.

    Args:
        directory_path: Directory containing files to process.
        embedding_model: Embedding model instance.
        metadata_store: Metadata store instance.
        vector_store: Vector store instance.
        extractor: Text extractor instance.
        force: If True, regenerate all embeddings regardless of modification.
        include_file_types: List of file extensions to include.
        recursive: If True, process files in subdirectories.
        verbose: If True, prints logs.

    Returns:
        summary: Dictionary of processed, skipped, and failed files.
    """
    embedder = embedding_model
    metadata_store.load_metadata()
    metadata_store.load_chunk_mapping()

    index_info = vector_store.prepare_index(directory_path, recursive)
    index, current_files, used_ids = index_info["index"], index_info["current_files"], index_info["used_ids"]

    chunk_mapping, next_id = _cleanup_deleted_files(metadata_store.load_chunk_mapping(), current_files, used_ids, vector_store)
    current_files = _filter_included_files(current_files, include_file_types)

    summary, _ = _process_files(
        current_files=current_files,
        metadata_store=metadata_store,
        vector_store=vector_store,
        extractor=extractor,
        embedder=embedder,
        force=force,
        verbose=verbose,
    )

    _save_all(vector_store, metadata_store)

    if verbose:
        print("\n[SUMMARY]")
        print(summary)

    return summary
