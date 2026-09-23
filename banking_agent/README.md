# Banking Customer Service AI Agent

This is a local, fictional banking assistant for learning GenAI agents. It uses dummy customers, read-only SQLite tools, LangChain's current `create_agent` API, Google Gemini, and a small Flask chat UI. It never connects to a bank and never asks for OTPs, PINs, CVVs, passwords, card numbers, or other credentials.

## Architecture

`Flask UI -> /api/chat -> LangChain agent -> selected tool -> parameterized SQLite query -> tool result -> Gemini response -> UI`

The agent receives the selected demo customer and remembers the known account number in the conversation. Tools are deliberately read-only. If no Gemini key is configured, a deterministic local router calls the same tools so database practice still works.

## Structure

- `app.py`: Flask routes and safe request validation.
- `agent.py`: Gemini model, system prompt, tools, memory, and local fallback.
- `config.py`: environment variables and database paths.
- `database/`: schema, connection helper, and fake seed data.
- `tools/`: account, transaction, and customer-care functions exposed to the agent.
- `models/`: Pydantic data models.
- `templates/` and `static/`: frontend.

## Windows PowerShell setup

From the repository root:

```powershell
py -3.11 -m venv .\banking_agent\.venv
.\banking_agent\.venv\Scripts\Activate.ps1
python -m pip install -r .\banking_agent\requirements.txt
Copy-Item .\banking_agent\.env.example .\banking_agent\.env
notepad .\banking_agent\.env
python -m banking_agent.database.seed_data
python -m banking_agent.app
```

Put your Gemini key in `.env` as `GOOGLE_API_KEY=...`. Do not commit `.env`. With no key, the local fallback mode still supports the requested demo flows.

Open http://127.0.0.1:5000. Choose a demo customer, enter `1000000001`, and try:

- `What is my balance?`
- `Show my last 5 transactions.`
- `Show my account details.`
- `List my accounts.`
- `I want customer care.`
- `9999999999` (not found)

## Teaching flow

For “Show my balance”, the user message reaches Flask, then the LangChain agent identifies the intent and calls `check_balance(account_number)`. The tool performs a parameterized `SELECT` against SQLite, returns the real dummy balance, and the agent turns that result into a concise response. The model is instructed never to invent financial data or reveal credentials.

## Adding a feature

Add a read-only function in `tools/`, decorate it with `@tool`, add it to `TOOLS` in `agent.py`, and update the system prompt and UI quick actions. If it needs data, add a table/seed rows and use `?` placeholders in SQLite queries.

## Test cases

1. `validate_account("1000000001")` verifies an active account.
2. `validate_account("9999999999")` returns not found.
3. “What is my balance?” calls `check_balance`.
4. “Show my last 5 transactions” calls `get_transaction_history`.
5. “Account details” calls `get_account_details`.
6. “List my accounts” shows Rahul's three accounts.
7. “Customer care” calls `customer_service`.
8. An empty API message returns HTTP 400.
9. An unknown request receives a safe capability message.
10. A database failure is logged server-side and does not expose a traceback in the UI.
