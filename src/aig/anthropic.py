import os
import sys
from anthropic import Anthropic
from anthropic.types import Message, TextBlock


client: Anthropic | None = None


def is_available() -> bool:
    """Checks if the Anthropic API key is available in the environment variables."""
    return os.getenv("ANTHROPIC_API_KEY") is not None


def init() -> None:
    """Initializes the Anthropic client."""
    api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit(
            "Anthropic API key not found. Please set the relevant environment variable."
        )
    global client
    client = Anthropic(api_key=api_key)


def ask_anthropic(prompt: str, max_tokens: int = 400) -> str:
    """Sends a single-shot prompt to the Anthropic API and returns the response."""
    if not client:
        raise Exception("Anthropic client not initialized.")
    try:
        model_name: str = os.getenv("MODEL_NAME") or "claude-3-opus-20240229"
        response: Message = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text.strip()
        raise Exception("No text block found in response")
    except Exception as e:
        if "API key not valid" in str(e):
            raise Exception(
                "Anthropic API key is not valid. Please check your .env file."
            )
        raise Exception(f"Anthropic API error: {e}")
