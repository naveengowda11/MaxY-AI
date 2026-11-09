const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const connectionLabel = document.querySelector("#connection-label");
const newChatButton = document.querySelector("#new-chat");

let conversationId = localStorage.getItem("maxy_conversation_id");

function addMessage(role, content) {
  const welcome = document.querySelector("#welcome");
  if (welcome) welcome.remove();

  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "message-role";
  label.textContent = role === "user" ? "YOU" : "MAXY";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;

  wrapper.append(label, bubble);
  messagesEl.append(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setBusy(busy) {
  sendButton.disabled = busy;
  input.disabled = busy;
  sendButton.innerHTML = busy ? "<span>…</span>" : "<span>↑</span>";
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("API unavailable");
    const health = await response.json();
    connectionLabel.textContent = `API connected · ${health.model}`;
    connectionLabel.previousElementSibling.classList.add("online");
  } catch {
    connectionLabel.textContent = "Local API unavailable";
    connectionLabel.previousElementSibling.classList.remove("online");
  }
}

async function loadConversation() {
  if (!conversationId) return;
  try {
    const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/messages`);
    if (!response.ok) {
      conversationId = null;
      localStorage.removeItem("maxy_conversation_id");
      return;
    }
    const history = await response.json();
    if (history.length) {
      const welcome = document.querySelector("#welcome");
      if (welcome) welcome.remove();
      history.forEach((item) => addMessage(item.role, item.content));
    }
  } catch {
    // A failed history fetch should not prevent starting a fresh conversation.
  }
}

async function sendMessage(message) {
  const clean = message.trim();
  if (!clean || sendButton.disabled) return;

  addMessage("user", clean);
  input.value = "";
  input.style.height = "auto";
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: clean, conversation_id: conversationId }),
    });
    const data = await response.json();
    const returnedConversationId = response.headers.get("X-Conversation-ID");
    if (returnedConversationId) {
      conversationId = returnedConversationId;
      localStorage.setItem("maxy_conversation_id", conversationId);
    }
    if (!response.ok) {
      throw new Error(data.detail || "MAXY could not complete the request.");
    }
    conversationId = data.conversation_id;
    localStorage.setItem("maxy_conversation_id", conversationId);
    addMessage("assistant", data.reply);
  } catch (error) {
    addMessage("assistant", `I couldn't complete that request. ${error.message}`);
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
});

newChatButton.addEventListener("click", () => {
  conversationId = null;
  localStorage.removeItem("maxy_conversation_id");
  messagesEl.innerHTML = `
    <div id="welcome" class="welcome">
      <div class="welcome-orb"><span>M</span></div>
      <p class="eyebrow">HELLO, I'M MAXY</p>
      <h2>What can I help you think through?</h2>
      <p class="welcome-copy">Ask a question, plan your day, or work through an idea. I'm running through your local AI setup.</p>
      <div class="suggestions">
        <button type="button" data-prompt="Help me plan my day.">Plan my day</button>
        <button type="button" data-prompt="Explain a difficult topic in simple terms.">Explain something</button>
        <button type="button" data-prompt="Help me break a project into steps.">Organize a project</button>
      </div>
    </div>`;
});

messagesEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-prompt]");
  if (button) sendMessage(button.dataset.prompt);
});

checkHealth();
loadConversation();
