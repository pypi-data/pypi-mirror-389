from abc import ABC, abstractmethod
from typing import TypedDict, List, Dict


# --- TypedDict definitions for strict typing ---

class FileMetadata(TypedDict):
    """
    Structure of metadata stored for each file.
    """
    size: int
    modified: float


class ChunkMapping(TypedDict):
    """
    Structure of a single chunk mapping.
    """
    chunk_id: str
    file_path: str
    start: int
    end: int


# --- Base class ---

class BaseMetadataStore(ABC):
    """
    Abstract base class for metadata storage backends.

    Defines strict output formats for metadata and chunk mapping.
    """

    @abstractmethod
    def load_metadata(self) -> Dict[str, FileMetadata]:
        """
        Load all metadata from persistent storage.

        Returns:
            Dictionary mapping file paths to FileMetadata dictionaries.
        """
        ...

    @abstractmethod
    def save_metadata(self, metadata: Dict[str, FileMetadata]) -> None:
        """
        Save metadata to persistent storage.

        Args:
            metadata: Dictionary mapping file paths to FileMetadata dictionaries.
        """
        ...

    @abstractmethod
    def get_file_info(self, file_path: str) -> FileMetadata:
        """
        Get information about a specific file.

        Args:
            file_path: Path to the file.

        Returns:
            A FileMetadata dictionary.
        """
        ...

    @abstractmethod
    def is_modified(self, file_path: str, current_info: FileMetadata) -> bool:
        """
        Determine if a file has changed compared to stored metadata.

        Args:
            file_path: Path to the file.
            current_info: Current FileMetadata dictionary.

        Returns:
            True if the file is modified, False otherwise.
        """
        ...

    @abstractmethod
    def update(self, file_path: str, file_info: FileMetadata) -> None:
        """
        Update metadata for a specific file.

        Args:
            file_path: Path to the file.
            file_info: FileMetadata dictionary.
        """
        ...

    @abstractmethod
    def load_chunk_mapping(self) -> List[ChunkMapping]:
        """
        Load the chunk mapping list from persistent storage.

        Returns:
            List of ChunkMapping dictionaries.
        """
        ...

    @abstractmethod
    def save_chunk_mapping(self, chunk_mapping: List[ChunkMapping]) -> None:
        """
        Save the chunk mapping list to persistent storage.

        Args:
            chunk_mapping: List of ChunkMapping dictionaries.
        """
        ...