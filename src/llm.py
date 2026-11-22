import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables from the project's .env file
load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

# Set a 20-second request timeout
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=20_000)
)


def call_llm(prompt):
    """Send a prompt to Gemini and return its text response."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text