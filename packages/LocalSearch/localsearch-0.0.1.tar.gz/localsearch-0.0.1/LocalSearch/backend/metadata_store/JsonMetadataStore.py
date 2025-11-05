import json
import os

from LocalSearch.backend.metadata_store.BaseMetaDataStore import BaseMetadataStore


class JsonMetadataStore(BaseMetadataStore):
    """JSON-based metadata and chunk mapping persistence."""

    def __init__(self, directory_path: str):
        self.metadata_path = os.path.join(directory_path, "metadata.json")
        self.chunk_map_path = os.path.join(directory_path, "chunk_mapping.json")

    # --- Metadata Handling ---

    def load_metadata(self):
        if not os.path.exists(self.metadata_path):
            return {}
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_metadata(self, metadata: dict):
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def get_file_info(self, file_path: str) -> dict:
        stat = os.stat(file_path)
        return {"size": stat.st_size, "modified": stat.st_mtime}

    def is_modified(self, file_path: str, current_info: dict) -> bool:
        metadata = self.load_metadata()
        stored_info = metadata.get(file_path)
        return stored_info != current_info

    def update(self, file_path: str, file_info: dict):
        metadata = self.load_metadata()
        metadata[file_path] = file_info
        self.save_metadata(metadata)

    # --- Chunk Mapping Handling ---

    def load_chunk_mapping(self):
        if not os.path.exists(self.chunk_map_path):
            return []
        with open(self.chunk_map_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_chunk_mapping(self, chunk_mapping: list[dict]):
        with open(self.chunk_map_path, "w", encoding="utf-8") as f:
            json.dump(chunk_mapping, f, indent=2)
