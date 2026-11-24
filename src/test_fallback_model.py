
from llm import client

FALLBACK_MODEL = "gemini-3.5-flash-lite"

try:
    response = client.models.generate_content(
        model=FALLBACK_MODEL,
        contents="Reply with exactly: FALLBACK MODEL WORKS"
    )

    print("Fallback model:", FALLBACK_MODEL)
    print("Response:", response.text)
    print("FALLBACK TEST PASSED")

except Exception as e:
    print("FALLBACK TEST FAILED")
    print(type(e).__name__, str(e))
