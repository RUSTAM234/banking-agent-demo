from langchain_core.tools import tool
import logging

from banking_agent.database.db import get_connection
from banking_agent.tools.account_tools import _account

LOGGER = logging.getLogger(__name__)


@tool
def check_balance(account_number: str) -> str:
    """Read the current available balance for an active demo account."""
    LOGGER.info("TOOL check_balance | account=******%s", account_number[-4:])
    row = _account(account_number)
    if row is None:
        return "Account could not be found."
    if row["status"] != "ACTIVE":
        return "This account is currently inactive."
    return f"Your current available balance is {row['currency']} {row['balance']:,.2f}."


@tool
def get_transaction_history(account_number: str, limit: int = 5) -> str:
    """Return recent transactions from SQLite for a demo account."""
    LOGGER.info(
        "TOOL get_transaction_history | account=******%s | limit=%s",
        account_number[-4:],
        limit,
    )
    row = _account(account_number)
    if row is None:
        return "Account could not be found."
    if row["status"] != "ACTIVE":
        return "This account is currently inactive."
    safe_limit = max(1, min(int(limit), 20))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT date, description, amount, transaction_type, "
            "balance_after_transaction FROM transactions "
            "WHERE account_number = ? ORDER BY date DESC, transaction_id DESC LIMIT ?",
            (account_number.strip(), safe_limit),
        ).fetchall()
    if not rows:
        return "No transactions were found for this account."
    return "\n".join(
        f"{item['date']} | {item['description']} | "
        f"{item['transaction_type']} {item['amount']:,.2f} | "
        f"Balance after: {item['balance_after_transaction']:,.2f}"
        for item in rows
    )
