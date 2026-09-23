from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str
    name: str
    phone: str


class Account(BaseModel):
    customer_id: str
    account_number: str
    account_type: str
    balance: float
    currency: str = "INR"
    status: str
    created_date: str


class Transaction(BaseModel):
    transaction_id: str
    account_number: str
    date: str
    description: str
    amount: float
    transaction_type: str
    balance_after_transaction: float


class AgentResponse(BaseModel):
    response: str = Field(description="Safe, concise response shown to the demo customer.")
    tool_used: str | None = Field(default=None, description="Tool used, if any.")
