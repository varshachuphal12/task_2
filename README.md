# Reliable Structured LLM Output

## Task

Make a model return JSON that code can rely on.

This project demonstrates a small, defensive pipeline for extracting a customer-support ticket from natural-language text.

## What it demonstrates

- **Schema:** `SupportTicket` is a Pydantic model with typed fields and allowed values.
- **Validation:** the model response is parsed as JSON and validated with Pydantic.
- **Retry/repair:** if JSON parsing or schema validation fails, the validation error is fed back into the next prompt and the model gets another attempt.
- **Typed result:** successful output is returned as a `SupportTicket` object, not an unvalidated dictionary.

## Project structure

```text
structured-llm-output/
├── main.py
├── requirements.txt
└── README.md
```

## Schema

The model must return:

```json
{
  "category": "billing",
  "priority": "high",
  "summary": "Customer was charged twice",
  "needs_human": true
}
```

Allowed values:

- `category`: `billing`, `technical`, `account`, `shipping`, `other`
- `priority`: `low`, `medium`, `high`
- `summary`: string
- `needs_human`: boolean

## How the validation works

1. Send the customer message to the LLM with an explicit JSON schema description.
2. Read the model response.
3. Parse it using Python's `json.loads`.
4. Validate it using `SupportTicket.model_validate`.
5. If parsing or validation fails, capture the error.
6. Include that error in a repair prompt.
7. Retry up to three times.
8. Return the validated `SupportTicket` object.

This means invalid output is rejected instead of silently being passed to application code.

## Setup

Python 3.10+ is recommended.

Install dependencies:

```bash
pip install -r requirements.txt
```

Set a Gemini API key:

### Linux/macOS

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

Then run:

```bash
python main.py
```

## Example output

A successful run will look similar to:

```text
Valid output received on attempt 1.

Validated typed result:
category='billing' priority='high' summary='Customer was charged twice for a monthly subscription' needs_human=True

As JSON:
{
  "category": "billing",
  "priority": "high",
  "summary": "Customer was charged twice for a monthly subscription",
  "needs_human": true
}
```

If the model produces invalid JSON or a value outside the schema, the script rejects it and retries with the validation error.

## Design decision

The smallest useful implementation was chosen: one Pydantic schema, one LLM call function, explicit JSON parsing, validation, and a bounded repair loop. The retry limit prevents the program from retrying forever.

## Security note

The API key is read from an environment variable and is **not stored in the repository**. Do not commit API keys or other secrets to GitHub.
