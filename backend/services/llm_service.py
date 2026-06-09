import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

# Client is initialised once at import time; the API key is read from .env
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_narrative_feedback(exercise: str, checks: list[dict]) -> str | None:
    """
    Ask Gemini to turn the structured form-check results into a short coaching paragraph.

    Args:
        exercise: e.g. "pull_up" or "push_up"
        checks:   the list of check dicts from the analysis service, each with
                  keys "name", "passed", and "message"

    Returns:
        A 2–3 sentence coaching string, or None if the API call fails (so the
        rest of the response is never blocked by an LLM error).
    """
    # Format each check as a bullet so Gemini can read them clearly
    check_lines = "\n".join(
        f"- {'PASS' if c['passed'] else 'FAIL'}: {c['message']}"
        for c in checks
    )
    overall = "PASS" if all(c["passed"] for c in checks) else "FAIL"
    exercise_label = exercise.replace("_", " ")

    prompt = (
        f"A user attempted a {exercise_label}. "
        f"Here are the automated form check results:\n{check_lines}\n"
        f"Overall result: {overall}\n\n"
        "Write 2-3 sentences of specific, encouraging coaching feedback. "
        "If they passed, acknowledge what they did well. "
        "If they failed, focus on the most important thing to fix and give actionable advice. "
        "Do not use bullet points or headers — write in plain prose."
    )

    try:
        # gemini-1.5-flash is free-tier eligible (15 RPM, 1 500 req/day)
        response = _client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as exc:
        # Narrative is a nice-to-have. A failed API call should never break the
        # upload response — the structured check cards are still returned.
        print(f"Gemini API call failed: {exc}")
        return None
