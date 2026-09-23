# Banking AI Assistant - Learning Guide

This file explains the project architecture and the path a request takes through
the application. Read it together with the Python files in this folder.

## 1. Complete architecture

```text
Browser
  |
  | User asks: "What is my balance?"
  v
templates/index.html + static/script.js
  |
  | POST /api/chat
  v
app.py - Flask web server
  |
  | validates customer, message, and account number
  v
agent.py - AI decision maker
  |
  | Gemini chooses a tool
  | or local fallback works without an API key
  v
tools/
  |-- account_tools.py
  |-- transaction_tools.py
  |-- customer_service_tools.py
  |
  | parameterized SQL queries
  v
database/db.py
  |
  v
SQLite database: data/banking.db
  |
  | result
  v
Tool result -> AI response -> Flask JSON -> Browser
```

The important idea is:

```text
User question
    -> Flask receives it
    -> AI or the local router identifies the intention
    -> A Python tool performs a safe database operation
    -> The result is returned to the browser
    -> The user sees the answer
```

## 2. Example: checking a balance

```text
"What is my balance?"
    -> Browser sends POST /api/chat
    -> app.py validates the request
    -> agent.py identifies a balance request
    -> check_balance(account_number) is called
    -> SQLite returns the balance
    -> Flask returns JSON
    -> script.js displays the answer
```

The AI does not directly change the database. It can only use the tools listed
in `agent.py`. The tools are the controlled connection between the AI and the
database.

## 3. File and folder guide

| File or folder | Purpose |
|---|---|
| `app.py` | Starts Flask and defines web routes |
| `agent.py` | Connects Gemini AI with Python tools |
| `config.py` | Stores paths and environment settings |
| `database/db.py` | Opens and manages SQLite connections |
| `database/schema.sql` | Defines the database tables |
| `database/seed_data.py` | Inserts fictional sample customers and accounts |
| `tools/account_tools.py` | Validates accounts and returns account information |
| `tools/transaction_tools.py` | Reads balances and transaction history |
| `tools/customer_service_tools.py` | Returns customer-care information |
| `models/schemas.py` | Defines validated Pydantic data models |
| `templates/index.html` | Defines the web page structure |
| `static/script.js` | Sends requests and displays chat messages |
| `static/style.css` | Controls the web page appearance |
| `.env` | Local secrets; never upload this file |

## 4. Browser to server flow

### `templates/index.html`

The HTML file creates:

- The customer dropdown.
- The account-number input.
- The chat area.
- Quick-action buttons.
- The message input and Send button.

The important lines are:

```html
<form id="chat-form">
```

This creates the form used to send a message.

```html
<script src="{{ url_for('static', filename='script.js') }}"></script>
```

This loads the JavaScript file. Flask's `url_for` generates the correct static
file URL.

### `static/script.js`

```javascript
const chat = document.querySelector("#chat");
const account = document.querySelector("#account");
```

These lines find HTML elements so JavaScript can read and update them.

```javascript
fetch("/api/chat", {
  method: "POST",
  ...
});
```

`fetch` sends the user's message to Flask. `POST` means data is being sent to
the server.

```javascript
body: JSON.stringify({
  message: text,
  customer_id: customer.value,
  account_number: account.value,
  thread_id: threadId
})
```

This converts JavaScript data into JSON.

```javascript
const data = await response.json();
```

This converts Flask's JSON response back into a JavaScript object.

```javascript
addMessage(data.response, "agent");
```

This places the assistant response into the chat window.

## 5. Flask server flow

### `banking_agent/app.py`

```python
app = Flask(__name__)
```

Creates the Flask application object.

```python
@app.get("/")
def index():
    return render_template("index.html")
```

When the browser opens `/`, Flask sends the HTML page.

```python
@app.post("/api/chat")
def chat():
```

When JavaScript sends a `POST` request to `/api/chat`, Flask runs `chat()`.

```python
data = request.get_json(silent=True) or {}
```

Reads the JSON sent by the browser. If no JSON is provided, it uses an empty
dictionary.

```python
message = str(data.get("message", "")).strip()
```

Gets the message, converts it to text, and removes extra spaces.

```python
found = re.search(r"\b\d{10}\b", message)
```

Searches the message for a ten-digit account number.

```python
owner = get_account_owner(account_number)
```

Looks up the account owner in the database.

```python
customer_id = owner["customer_id"]
```

Updates the selected customer to match the account owner.

The route then selects the correct operation:

```text
Account number      -> validate_account
Balance request     -> check_balance
Account details     -> get_account_details
My accounts         -> list_customer_accounts
Other requests      -> ask_agent
```

Finally, Flask returns JSON:

```python
return jsonify({
    "response": response,
    "account_number": account_number,
    "customer_id": customer_id,
    "thread_id": thread_id,
})
```

## 6. The AI agent

### `banking_agent/agent.py`

```python
TOOLS = [
    validate_account,
    get_account_details,
    check_balance,
    get_transaction_history,
    list_customer_accounts,
    customer_service,
]
```

This is the allow-list of functions Gemini may call.

```python
SYSTEM_PROMPT = """..."""
```

This tells Gemini how to behave. It says not to invent financial data and not
to request sensitive credentials.

```python
if not GOOGLE_API_KEY:
    return None
```

Without a Gemini key, the project uses `_fallback`, a local keyword-based
router. This makes the demo usable without an internet AI request.

```python
result = AGENT.invoke(...)
```

This sends the conversation to Gemini and lets Gemini choose one of the tools.

## 7. Tools and safe database access

### `tools/account_tools.py`

Account tools look up owners, validate accounts, and list accounts.

### `tools/transaction_tools.py`

Transaction tools read balances and transaction history.

### Parameterized SQL

The tools use queries like this:

```python
connection.execute(
    "SELECT * FROM accounts WHERE account_number = ?",
    (account_number,),
)
```

The `?` placeholder keeps user input separate from SQL code. This is safer than
building a query by joining strings together.

## 8. Database files

### `database/schema.sql`

Defines the tables:

```text
customers
  -> customer_id, name, phone

accounts
  -> account_number, customer_id, account_type, balance, status

transactions
  -> transaction_id, account_number, date, amount, transaction_type
```

The `customer_id` and `account_number` values connect related records.

### `database/db.py`

```python
with get_connection() as connection:
```

Opens a database connection and guarantees that it is closed afterwards.

```python
connection.commit()
```

Saves successful changes.

```python
connection.rollback()
```

Cancels incomplete changes after a database error.

### `database/seed_data.py`

Contains fictional demo data and inserts it into SQLite when the application
starts. It is safe sample data, not real banking data.

## 9. Python classes

### `models/schemas.py`

```python
class Customer(BaseModel):
    customer_id: str
    name: str
    phone: str
```

`Customer` is a class, which is a blueprint for customer data. Pydantic checks
that the values have the expected types.

```python
class Account(BaseModel):
    customer_id: str
    account_number: str
    balance: float
```

This describes account data. `str` means text and `float` means a decimal
number.

```python
currency: str = "INR"
```

Uses `"INR"` as the default currency when no currency is supplied.

## 10. How to run and study the project

From the project root:

```powershell
python -m banking_agent.app
```

Open:

```text
http://127.0.0.1:5000
```

Recommended learning order:

1. Read `templates/index.html`.
2. Read `static/script.js`.
3. Read the `/api/chat` route in `banking_agent/app.py`.
4. Read one tool in `tools/`.
5. Read `database/db.py`.
6. Read `database/schema.sql`.
7. Read `agent.py`.
8. Read `models/schemas.py`.

Try these requests one at a time:

```text
1000000002
Check my balance
Show my account details
List my accounts
Show my last 5 transactions
I want customer care
```

After each request, trace the same path through the diagram and identify which
route, function, tool, SQL query, and response was used.
