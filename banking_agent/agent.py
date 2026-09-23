import logging
import re

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from banking_agent.config import GEMINI_MODEL, GOOGLE_API_KEY
from banking_agent.tools.account_tools import (
    get_account_details,
    list_customer_accounts,
    validate_account,
)
from banking_agent.tools.customer_service_tools import customer_service
from banking_agent.tools.transaction_tools import check_balance, get_transaction_history

LOGGER = logging.getLogger(__name__)
TOOLS = [
    validate_account,
    get_account_details,
    check_balance,
    get_transaction_history,
    list_customer_accounts,
    customer_service,
]
SYSTEM_PROMPT = """You are a banking customer service assistant for a fictional demo bank.
Use tools for account information, balances, transactions, account lists, and customer care.
Never invent balances or transactions. Never request or expose OTP, PIN, CVV, passwords,
real card numbers, or banking credentials. Account numbers must be masked in responses.
The selected demo customer is provided in the conversation context. If multiple accounts
exist and the customer has not specified one, ask which account they want to use.
Keep responses concise and conversational. This is not a real bank."""


def _build_agent():
    if not GOOGLE_API_KEY:
        LOGGER.warning("AGENT mode=local fallback | GOOGLE_API_KEY is not configured")
        return None
    LOGGER.info("AGENT mode=Gemini | model=%s", GEMINI_MODEL)
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


AGENT = _build_agent()


def _fallback(message: str, customer_id: str, account_number: str | None) -> str:
    """A deterministic local mode keeps the UI usable without a Gemini key."""
    text = message.lower()
    number = account_number or (re.search(r"\b\d{10}\b", message) or [None])[0]
    if re.search(r"\b\d{10}\b", message):
        LOGGER.info("AGENT fallback selected tool=validate_account")
        return validate_account.invoke({"account_number": number})
    if any(word in text for word in ("customer care", "customer service", "contact")):
        LOGGER.info("AGENT fallback selected tool=customer_service")
        return customer_service.invoke({})
    if "my accounts" in text or "list account" in text:
        LOGGER.info("AGENT fallback selected tool=list_customer_accounts")
        return list_customer_accounts.invoke({"customer_id": customer_id})
    if any(word in text for word in ("transaction", "recent", "history")):
        limit_match = re.search(r"\b(?:last|top)\s+(\d+)", text)
        limit = int(limit_match.group(1)) if limit_match else 5
        LOGGER.info("AGENT fallback selected tool=get_transaction_history | limit=%s", limit)
        return get_transaction_history.invoke({"account_number": number or "", "limit": limit})
    if "detail" in text or "account type" in text:
        LOGGER.info("AGENT fallback selected tool=get_account_details")
        return get_account_details.invoke({"account_number": number or ""})
    if any(word in text for word in ("balance", "money", "available")):
        LOGGER.info("AGENT fallback selected tool=check_balance")
        return check_balance.invoke({"account_number": number or ""})
    LOGGER.info("AGENT fallback selected tool=none")
    return "I can help with balance, transactions, account details, account lists, or customer care. Please provide a demo account number."


def ask_agent(message: str, customer_id: str, account_number: str | None, thread_id: str) -> str:
    if not message.strip():
        return "Please enter a message."
    if AGENT is None:
        return _fallback(message, customer_id, account_number)
    LOGGER.info("AGENT invoke | customer=%s | thread=%s", customer_id, thread_id)
    context = (
        f"Selected demo customer ID: {customer_id}. "
        f"Known account number for this conversation: {account_number or 'none'}.\n"
        f"Customer message: {message}"
    )
    try:
        result = AGENT.invoke(
            {"messages": [{"role": "user", "content": context}]},
            {"configurable": {"thread_id": thread_id}},
        )
        LOGGER.info("AGENT completed | thread=%s", thread_id)
        return result["messages"][-1].content
    except Exception:
        LOGGER.exception("Gemini agent request failed")
        LOGGER.warning("Using local tool router after Gemini failure")
        return _fallback(message, customer_id, account_number)
