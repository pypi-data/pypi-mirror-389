from abc import ABC, abstractmethod


class BaseTextExtractor(ABC):
    """
    Abstract base class for extracting text from documents.

    Subclasses must implement methods to determine if a file type is supported
    and to extract text from files.
    """

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """
        Determine if this extractor can handle the given file type.

        Args:
            file_path: Path to the file.

        Returns:
            True if this extractor can process the file type, False otherwise.
        """
        ...

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extract and return text from a file.

        Args:
            file_path: Path to the file.

        Returns:
            Extracted text as a string.
        """
        ...

    @abstractmethod
    def split_text(self, text: str) -> list[str]:
        """
        Split the input text into smaller chunks suitable for embedding.

        The exact chunking strategy (size, overlap, etc.) is implementation-dependent.

        Args:
            text (str): The full text to split.

        Returns:
            List[str]: A list of text chunks.
        """