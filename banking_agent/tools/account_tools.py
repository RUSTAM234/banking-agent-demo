import logging

from langchain_core.tools import tool

from banking_agent.database.db import get_connection

LOGGER = logging.getLogger(__name__)


def _mask(account_number: str) -> str:
    return f"******{account_number[-4:]}"


def _account(account_number: str, customer_id: str | None = None):
    query = "SELECT * FROM accounts WHERE account_number = ?"
    params: list[str] = [account_number.strip()]
    if customer_id:
        query += " AND customer_id = ?"
        params.append(customer_id)
    LOGGER.info(
        "Database query | accounts | account=******%s%s",
        account_number[-4:],
        f" | customer={customer_id}" if customer_id else "",
    )
    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()
    LOGGER.info("Database query result | accounts | found=%s", row is not None)
    return row


def get_account_owner(account_number: str):
    """Return the demo customer who owns an account, or None if it does not exist."""
    LOGGER.info(
        "Database query | account owner | account=******%s",
        account_number[-4:],
    )
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT a.account_number, a.account_type, a.status, c.customer_id, c.name
            FROM accounts AS a
            JOIN customers AS c ON c.customer_id = a.customer_id
            WHERE a.account_number = ?
            """,
            (account_number.strip(),),
        ).fetchone()


@tool
def validate_account(account_number: str) -> str:
    """Check a demo account exists and is active. Never returns credentials."""
    LOGGER.info("Tool started | validate_account | account=******%s", account_number[-4:])
    row = get_account_owner(account_number)
    if row is None:
        LOGGER.info("Account verification result | not found")
        return "Account could not be found."
    if row["status"] != "ACTIVE":
        LOGGER.info("Account verification result | inactive")
        return "This account is currently inactive."
    LOGGER.info(
        "Account verification result | verified | type=%s",
        row["account_type"],
    )
    return (
        f"Hello! I have accessed your {row['account_type'].title()} account "
        f"ending in **{row['account_number'][-4:]}**.\n\n"
        f"Account Number: {row['account_number']}\n"
        f"Account Name: {row['name']} ({row['customer_id']})"
    )


@tool
def get_account_details(account_number: str) -> str:
    """Return safe details for one demo account with its number masked."""
    LOGGER.info("TOOL get_account_details | account=******%s", account_number[-4:])
    row = _account(account_number)
    if row is None:
        return "Account could not be found."
    with get_connection() as connection:
        owner = connection.execute(
            """
            SELECT c.name, c.customer_id
            FROM accounts AS a
            JOIN customers AS c ON c.customer_id = a.customer_id
            WHERE a.account_number = ?
            """,
            (account_number.strip(),),
        ).fetchone()
    return (
        f"Account Number: {row['account_number']}\n"
        f"Account Name: {owner['name']} ({owner['customer_id']})\n"
        f"Account Type: {row['account_type'].title()} Account"
    )


@tool
def list_customer_accounts(customer_id: str) -> str:
    """List all demo accounts belonging to a selected demo customer."""
    LOGGER.info("TOOL list_customer_accounts | customer=%s", customer_id)
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT account_number, account_type, status "
            "FROM accounts WHERE customer_id = ? ORDER BY account_number",
            (customer_id.strip(),),
        ).fetchall()
    if not rows:
        return "Customer could not be found or has no accounts."
    return "\n".join(
        f"- {row['account_number']} | {row['account_type'].title()} Account | "
        f"{row['status'].title()}"
        for row in rows
    )
