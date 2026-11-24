
import os
import time
import random

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

MAX_ATTEMPTS = 3
RETRYABLE_CODES = {429, 500, 502, 503, 504}

LAST_USED_MODEL = None

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=20_000)
)


def call_llm(prompt):
    """Try the primary model with retries, then use fallback."""

    global LAST_USED_MODEL

    LAST_USED_MODEL = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            LAST_USED_MODEL = MODEL_NAME
            return response.text

        except APIError as e:

            status_code = getattr(e, "code", None)

            if status_code not in RETRYABLE_CODES:
                raise

            if attempt == MAX_ATTEMPTS:
                print(
                    f"Primary model failed after {MAX_ATTEMPTS} attempts."
                )
                break

            max_delay = min(8, 2 ** (attempt - 1))
            delay = random.uniform(0, max_delay)

            print(
                f"Primary model error {status_code}. "
                f"Retrying attempt {attempt + 1}/{MAX_ATTEMPTS} "
                f"after {delay:.2f} seconds."
            )

            time.sleep(delay)

    # Primary model exhausted: try fallback once
    print(f"Switching to fallback model: {FALLBACK_MODEL}")

    response = client.models.generate_content(
        model=FALLBACK_MODEL,
        contents=prompt
    )

    LAST_USED_MODEL = FALLBACK_MODEL
    return response.text
