"""
Task 2: Reliable Structured LLM Output

A small example that:
1. Requests JSON from an LLM.
2. Validates the response against a Pydantic schema.
3. Retries with validation feedback when the output is invalid.
4. Returns a typed SupportTicket object.

This example uses Google's Gemini API. Set GEMINI_API_KEY before running.
"""

import json
import os
from typing import Literal

from google import genai
from pydantic import BaseModel, ValidationError


class SupportTicket(BaseModel):
    category: Literal["billing", "technical", "account", "shipping", "other"]
    priority: Literal["low", "medium", "high"]
    summary: str
    needs_human: bool


SCHEMA_DESCRIPTION = {
    "category": "one of: billing, technical, account, shipping, other",
    "priority": "one of: low, medium, high",
    "summary": "short description of the customer's issue",
    "needs_human": "true if a human support agent should review the issue, otherwise false",
}


def build_prompt(user_text: str, repair_error: str | None = None) -> str:
    repair = ""
    if repair_error:
        repair = f"""
The previous response failed validation.

Validation error:
{repair_error}

Repair the response. Return ONLY valid JSON matching the required schema.
"""

    return f"""
Extract a support ticket from the customer message below.

Required JSON object:
{json.dumps(SCHEMA_DESCRIPTION, indent=2)}

Rules:
- Return ONLY a JSON object.
- Do not use Markdown or code fences.
- Do not add fields that are not in the schema.
- category must be exactly one of: billing, technical, account, shipping, other.
- priority must be exactly one of: low, medium, high.
- summary must be a concise string.
- needs_human must be a JSON boolean (true or false).

Customer message:
{user_text}
{repair}
"""


def get_ticket(user_text: str, max_attempts: int = 3) -> SupportTicket:
    """Ask the model for JSON and retry/repair until validation succeeds."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add your Gemini API key as an environment variable."
        )

    client = genai.Client(api_key=api_key)
    last_error = None

    for attempt in range(1, max_attempts + 1):
        prompt = build_prompt(user_text, last_error)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw = response.text.strip()

        # Remove accidental Markdown fences before parsing.
        if raw.startswith("```"):
            raw = raw.removeprefix("```json").removeprefix("```").strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()

        try:
            data = json.loads(raw)
            ticket = SupportTicket.model_validate(data)

            print(f"Valid output received on attempt {attempt}.")
            return ticket

        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            print(f"Attempt {attempt} failed validation.")

    raise RuntimeError(
        f"Could not obtain valid structured output after {max_attempts} attempts.\n"
        f"Last validation error: {last_error}"
    )


if __name__ == "__main__":
    message = (
        "I was charged twice for my monthly subscription. "
        "I only want one charge and need someone to fix the duplicate billing."
    )

    ticket = get_ticket(message)

    print("\nValidated typed result:")
    print(ticket)
    print("\nAs JSON:")
    print(ticket.model_dump_json(indent=2))
