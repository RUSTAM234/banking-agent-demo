const chat = document.querySelector("#chat");
const form = document.querySelector("#chat-form");
const messageInput = document.querySelector("#message");
const customer = document.querySelector("#customer");
const account = document.querySelector("#account");
let threadId = crypto.randomUUID();

function addMessage(text, type) {
  const item = document.createElement("div");
  item.className = `message ${type}`;
  if (typeof text === "string") {
    item.textContent = text;
  } else if (Array.isArray(text)) {
    item.textContent = text
      .map((part) => typeof part === "string" ? part : part?.text || part?.content || "")
      .filter(Boolean)
      .join("\n");
  } else {
    item.textContent = text?.content || text?.text || JSON.stringify(text);
  }
  chat.appendChild(item);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(text) {
  text = text.trim();
  if (!text) return;
  if (/^\d{10}$/.test(text)) {
    account.value = text;
  }
  await reflectCustomerFromAccount();
  addMessage(text, "user");
  messageInput.value = "";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message: text, customer_id: customer.value,
        account_number: account.value, thread_id: threadId
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed");
    if (data.account_number) account.value = data.account_number;
    if (data.customer_id) customer.value = data.customer_id;
    threadId = data.thread_id || threadId;
    addMessage(data.response, "agent");
  } catch (error) {
    addMessage(error.message, "agent");
  }
}

async function reflectCustomerFromAccount() {
  const accountNumber = account.value.trim();
  if (!/^\d{10}$/.test(accountNumber)) return;
  try {
    const response = await fetch(`/api/account-owner/${accountNumber}`);
    const data = await response.json();
    if (!response.ok) return;
    customer.value = data.customer_id;
  } catch (error) {
    console.error("Could not find account owner", error);
  }
}

form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(messageInput.value); });
document.querySelectorAll("[data-message]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

account.addEventListener("blur", reflectCustomerFromAccount);
account.addEventListener("change", reflectCustomerFromAccount);
account.addEventListener("input", () => {
  if (/^\d{10}$/.test(account.value.trim())) {
    reflectCustomerFromAccount();
  }
});

account.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    const value = account.value.trim();
    if (value) {
      sendMessage(value);
    }
  }
});
