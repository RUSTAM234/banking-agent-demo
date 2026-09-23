import logging
import re
import uuid

from flask import Flask, jsonify, render_template, request

from banking_agent.config import LOG_PATH, configure_logging

configure_logging()

from banking_agent.agent import ask_agent
from banking_agent.database.db import initialize_database
from banking_agent.database.seed_data import seed_database
from banking_agent.tools.account_tools import (
    get_account_details,
    get_account_owner,
    list_customer_accounts,
    validate_account,
)
from banking_agent.tools.transaction_tools import check_balance

LOGGER = logging.getLogger(__name__)
logging.getLogger("werkzeug").setLevel(logging.INFO)
app = Flask(__name__)
initialize_database()
seed_database()
LOGGER.info("APPLICATION ready | open http://127.0.0.1:5000")
LOGGER.info("APPLICATION log file | %s", LOG_PATH)


@app.before_request
def log_http_request():
    LOGGER.info(
        "HTTP request started | method=%s | path=%s",
        request.method,
        request.path,
    )


@app.after_request
def log_http_response(response):
    LOGGER.info(
        "HTTP request completed | method=%s | path=%s | status=%s",
        request.method,
        request.path,
        response.status_code,
    )
    return response


@app.get("/")
def index():
    LOGGER.info("HTTP request | GET / | serving banking UI")
    return render_template("index.html")


@app.get("/api/customers")
def customers():
    return jsonify(
        [
            {"customer_id": "C001", "name": "Rahul Sharma"},
            {"customer_id": "C002", "name": "Amit Kumar"},
            {"customer_id": "C003", "name": "Priya Singh"},
            {"customer_id": "C004", "name": "Neha Verma"},
            {"customer_id": "C005", "name": "Arjun Kumar"},
        ]
    )


@app.get("/api/account-owner/<account_number>")
def account_owner(account_number):
    if not re.fullmatch(r"\d{10}", account_number):
        return jsonify({"error": "Please enter a valid 10-digit account number."}), 400
    owner = get_account_owner(account_number)
    if owner is None:
        return jsonify({"error": "Account could not be found."}), 404
    return jsonify(
        {
            "account_number": owner["account_number"],
            "customer_id": owner["customer_id"],
            "customer_name": owner["name"],
            "status": owner["status"],
        }
    )


@app.post("/api/chat")
def chat():
    LOGGER.info("HTTP request | POST /api/chat | request received from UI")
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    customer_id = str(data.get("customer_id", "C001")).strip()
    account_number = str(data.get("account_number", "")).strip() or None
    thread_id = str(data.get("thread_id", "")).strip() or str(uuid.uuid4())
    if not message:
        LOGGER.warning("Rejected empty chat message")
        return jsonify({"error": "Please enter a message."}), 400
    if customer_id not in {"C001", "C002", "C003", "C004", "C005"}:
        LOGGER.warning("Rejected invalid demo customer: %s", customer_id)
        return jsonify({"error": "Please select a valid demo customer."}), 400
    found = re.search(r"\b\d{10}\b", message)
    if found:
        account_number = found.group(0)
    if account_number and re.fullmatch(r"\d{10}", account_number):
        owner = get_account_owner(account_number)
        if owner is not None:
            customer_id = owner["customer_id"]
    masked_account = f"******{account_number[-4:]}" if account_number else "none"
    LOGGER.info(
        "Account input received | account=%s | source=%s",
        account_number or "none",
        "message" if found else "account field",
    )
    LOGGER.info(
        "UI request received | customer=%s | account=%s | message=%r",
        customer_id,
        masked_account,
        message,
    )
    if found or (account_number and message == account_number):
        LOGGER.info(
            "Account verification started | account=%s",
            masked_account,
        )
    LOGGER.info(
        "CHAT request | customer=%s | account=%s | message=%r | thread=%s",
        customer_id,
        masked_account,
        message,
        thread_id,
    )
    if re.fullmatch(r"\d{10}", message):
        LOGGER.info(
            "Intent detected | intent=validate_account | account=%s",
            account_number,
        )
        LOGGER.info("Calling tool | validate_account")
        response = validate_account.invoke({"account_number": message})
    else:
        text = message.lower()
        intent = "agent_request"
        if "detail" in text or "account type" in text:
            intent = "account_details"
        elif "balance" in text or "available" in text:
            intent = "check_balance"
        elif "my accounts" in text or "list account" in text:
            intent = "list_customer_accounts"
        LOGGER.info(
            "Intent detected | intent=%s | account=%s | message=%r",
            intent,
            account_number or "none",
            message,
        )
        if intent == "account_details":
            response = get_account_details.invoke(
                {"account_number": account_number or ""}
            )
        elif intent == "check_balance":
            response = check_balance.invoke({"account_number": account_number or ""})
        elif intent == "list_customer_accounts":
            response = list_customer_accounts.invoke({"customer_id": customer_id})
        else:
            response = ask_agent(message, customer_id, account_number, thread_id)
    LOGGER.info("UI response sent | customer=%s | response=%r", customer_id, response)
    LOGGER.info("HTTP response | POST /api/chat | status=200")
    return jsonify(
        {
            "response": response,
            "account_number": account_number,
            "customer_id": customer_id,
            "thread_id": thread_id,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
