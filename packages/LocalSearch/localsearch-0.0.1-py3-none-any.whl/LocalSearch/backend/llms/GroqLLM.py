from groq import Groq

from LocalSearch.backend.llms.BaseLLM import BaseLLM


class GroqLLM(BaseLLM):
    """
    Groq LLM client wrapper.

    Uses the Groq SDK to call a specified model and stream output.
    """

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        """
        Initialize the Groq LLM client.

        Args:
            api_key: API key for authenticating with Groq.
            model: Model name to use (default: "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        """
        Generate text for the given prompt.

        Args:
            prompt: Input string to generate a response for.

        Returns:
            Generated text as a string.
        """
        messages = [{"role": "user", "content": prompt}]

        completion = self.client.chat.completions.create(
            model=self.model,  # Use instance model instead of hardcoded
            messages=messages,
            temperature=0.7,
            max_tokens=10000,
            top_p=1,
            stream=True,
            stop=None,
        )

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content or ""

        return response_text