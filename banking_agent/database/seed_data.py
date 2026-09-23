import logging

from banking_agent.config import DATABASE_PATH, configure_logging
from banking_agent.database.db import get_connection, initialize_database

configure_logging()

LOGGER = logging.getLogger(__name__)


CUSTOMERS = [
    ("C001", "Rahul Sharma", "9000000001"),
    ("C002", "Amit Kumar", "9000000002"),
    ("C003", "Priya Singh", "9000000003"),
    ("C004", "Neha Verma", "9000000004"),
    ("C005", "Arjun Kumar", "9000000005"),
]

ACCOUNTS = [
    ("1000000001", "C001", "SAVINGS", 85450.00, "INR", "ACTIVE", "2024-01-15"),
    ("1000000002", "C001", "SALARY", 125000.00, "INR", "ACTIVE", "2024-02-10"),
    ("1000000003", "C001", "FIXED_DEPOSIT", 200000.00, "INR", "ACTIVE", "2024-03-01"),
    ("1000000004", "C002", "SAVINGS", 42000.00, "INR", "ACTIVE", "2024-01-20"),
    ("1000000005", "C003", "CURRENT", 73500.00, "INR", "ACTIVE", "2024-02-12"),
    ("1000000006", "C004", "RECURRING_DEPOSIT", 18000.00, "INR", "ACTIVE", "2024-03-15"),
    ("1000000007", "C005", "SAVINGS", 9900.00, "INR", "INACTIVE", "2024-04-01"),
]

TRANSACTIONS = [
    ("TX001", "1000000001", "2025-09-01", "Salary Credit", 60000.0, "CREDIT", 85450.0),
    ("TX002", "1000000001", "2025-08-28", "UPI Payment", -850.0, "DEBIT", 25450.0),
    ("TX003", "1000000001", "2025-08-20", "Interest Credit", 450.0, "CREDIT", 26300.0),
    ("TX004", "1000000001", "2025-08-15", "ATM Withdrawal", -2000.0, "DEBIT", 25850.0),
    ("TX005", "1000000001", "2025-08-10", "NEFT Credit", 10000.0, "CREDIT", 27850.0),
    ("TX006", "1000000001", "2025-08-05", "Bill Payment", -1200.0, "DEBIT", 17850.0),
    ("TX007", "1000000001", "2025-07-30", "Cash Deposit", 5000.0, "CREDIT", 19050.0),
    ("TX008", "1000000001", "2025-07-20", "UPI Payment", -750.0, "DEBIT", 14050.0),
    ("TX009", "1000000001", "2025-07-15", "Interest Credit", 300.0, "CREDIT", 14800.0),
    ("TX010", "1000000001", "2025-07-01", "Salary Credit", 60000.0, "CREDIT", 14500.0),
    ("TX011", "1000000002", "2025-09-01", "Salary Credit", 125000.0, "CREDIT", 125000.0),
    ("TX012", "1000000004", "2025-08-29", "Cash Deposit", 10000.0, "CREDIT", 42000.0),
]


def seed_database() -> None:
    initialize_database()
    with get_connection() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO customers VALUES (?, ?, ?)", CUSTOMERS
        )
        connection.executemany(
            "INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)", ACCOUNTS
        )
        connection.executemany(
            "INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)",
            TRANSACTIONS,
        )


if __name__ == "__main__":
    seed_database()
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Demo database initialized | path=%s", DATABASE_PATH)
