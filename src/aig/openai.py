import os
import sys
from openai import OpenAI
from openai.types.chat import ChatCompletion


client: OpenAI | None = None


def is_available() -> bool:
    """Check if the OpenAI API key is available in environment."""
    return os.getenv("OPENAI_API_KEY") is not None


def init() -> None:
    """Initialize the OpenAI client with the API key."""
    api_key: str | None = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "OpenAI API key not found. Please set the relevant environment variable."
        )
    global client
    client = OpenAI(api_key=api_key)


def ask_openai(prompt: str, max_tokens: int = 400) -> str:
    """Single‑shot prompt to OpenAI, returns trimmed text."""
    if not client:
        raise Exception("OpenAI client not initialized.")
    try:
        model_name: str = os.getenv("MODEL_NAME") or "gpt-4-turbo-2024-04-09"
        response: ChatCompletion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        if response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return ""
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")
