
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
RETRYABLE_SERVER_CODES = {500, 502, 503, 504}

LAST_USED_MODEL = None

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=20_000)
)


def classify_429(error):
    """Classify 429 errors using the available API error message."""

    message = str(error).lower()

    daily_indicators = [
        "per day",
        "daily quota",
        "requests_per_day",
        "per_day",
        "daily limit",
        "daily requests"
    ]

    minute_indicators = [
        "per minute",
        "requests_per_minute",
        "per_minute",
        "rpm",
        "retrydelay",
        "retry delay",
        "retry in"
    ]

    if any(term in message for term in daily_indicators):
        return "DAILY_QUOTA"

    if any(term in message for term in minute_indicators):
        return "TEMPORARY_RATE_LIMIT"

    # Unknown 429: don't waste retries guessing.
    return "UNKNOWN_QUOTA"


def call_fallback(prompt):
    """Call fallback model once."""

    global LAST_USED_MODEL

    print(f"Switching to fallback model: {FALLBACK_MODEL}")

    response = client.models.generate_content(
        model=FALLBACK_MODEL,
        contents=prompt
    )

    LAST_USED_MODEL = FALLBACK_MODEL

    return response.text


def call_llm(prompt):
    """Retry temporary failures and switch to fallback when appropriate."""

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

            # Handle quota and rate-limit errors separately.
            if status_code == 429:

                error_type = classify_429(e)

                if error_type == "DAILY_QUOTA":
                    print(
                        "Primary model daily quota exhausted. "
                        "Skipping retries."
                    )
                    break

                if error_type == "UNKNOWN_QUOTA":
                    print(
                        "Primary model returned an unclassified 429. "
                        "Skipping retries to avoid wasting quota."
                    )
                    break

                # Temporary rate limit: retry with backoff.
                if attempt == MAX_ATTEMPTS:
                    print(
                        "Primary model rate limit persisted after "
                        f"{MAX_ATTEMPTS} attempts."
                    )
                    break

                max_delay = min(8, 2 ** (attempt - 1))
                delay = random.uniform(0, max_delay)

                print(
                    f"Temporary rate limit. "
                    f"Retrying attempt {attempt + 1}/"
                    f"{MAX_ATTEMPTS} after {delay:.2f} seconds."
                )

                time.sleep(delay)
                continue

            # Retry temporary server errors.
            if status_code in RETRYABLE_SERVER_CODES:

                if attempt == MAX_ATTEMPTS:
                    print(
                        f"Primary model failed after "
                        f"{MAX_ATTEMPTS} attempts."
                    )
                    break

                max_delay = min(8, 2 ** (attempt - 1))
                delay = random.uniform(0, max_delay)

                print(
                    f"Primary server error {status_code}. "
                    f"Retrying attempt {attempt + 1}/"
                    f"{MAX_ATTEMPTS} after {delay:.2f} seconds."
                )

                time.sleep(delay)
                continue

            # Authentication, invalid requests and other errors.
            print(
                f"Non-retryable primary API error: {status_code}"
            )
            raise

    # Primary quota exhausted or temporary failures persisted.
    # Try fallback once.
    return call_fallback(prompt)
