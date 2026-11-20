
import os
from dotenv import load_dotenv
from google import genai

# Load variables from the project's .env file
load_dotenv()

# Keep the model name in one place
MODEL_NAME = "gemini-3.8-flash"

# Read the API key without exposing it in the code
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

# Create the Gemini client
client = genai.Client(api_key=api_key)


def call_llm(prompt):
    """Send a prompt to Gemini and return its text response."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text
