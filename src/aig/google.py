import os
import sys
import google.generativeai as genai
from google.generativeai.types import (
    GenerateContentResponse,
    HarmBlockThreshold,
    HarmCategory,
)


def is_available() -> bool:
    """Check if a Gemini/Google API key is available."""
    return (
        os.getenv("GEMINI_API_KEY") is not None
        or os.getenv("GOOGLE_API_KEY") is not None
    )


def init() -> None:
    """Initialize the Google Gemini API client."""
    api_key: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        sys.exit(
            "Google API key not found. Please set the relevant environment variable."
        )
    genai.configure(api_key=api_key)  # type: ignore


def ask_gemini(prompt: str, max_tokens: int = 400) -> str:
    """Single‑shot prompt to Gemini, returns trimmed text."""
    try:
        model_name: str = os.getenv("MODEL_NAME") or "gemini-1.5-pro-latest"
        model: genai.GenerativeModel = genai.GenerativeModel(model_name)  # type: ignore
        response: GenerateContentResponse = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": max_tokens,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )
        if hasattr(response, "text") and response.text is not None:
            if response.text.strip().startswith(
                "```"
            ) and response.text.strip().endswith("```"):
                return response.text.strip()[3:-3].strip()
            return response.text.strip()
        return ""
    except Exception as e:
        if "API key not valid" in str(e):
            raise Exception("Gemini API key is not valid. Please check your .env file.")
        raise Exception(f"Gemini API error: {e}")
