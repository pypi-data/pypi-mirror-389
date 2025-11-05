from abc import abstractmethod, ABC


class BaseLLM(ABC):
    """
    Abstract base class for any LLM (Large Language Model) integration.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate text from a prompt using the underlying LLM.

        Args:
            prompt: Input prompt string.

        Returns:
            Generated text as a string.
        """
        ...
