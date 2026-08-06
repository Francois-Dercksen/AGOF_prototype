const API_BASE = "https://YOUR-RENDER-SERVICE.onrender.com"; // <-- update after Render deploy

const chatWindow = document.getElementById("chat-window");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const modelLabel = document.getElementById("model-label");

let history = [];

function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = content;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    modelLabel.textContent = data.model || "unknown model";
  } catch (e) {
    modelLabel.textContent = "backend offline";
  }
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  history.push({ role: "user", content: text });
  input.value = "";
  sendBtn.disabled = true;

  const typingEl = addMessage("ai", "Qwen is thinking…");
  typingEl.classList.add("typing");

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    });
    const data = await res.json();

    if (!res.ok) {
      typingEl.textContent = "Error: " + (data.error || "unknown error");
      typingEl.classList.remove("typing");
      return;
    }

    typingEl.textContent = data.reply;
    typingEl.classList.remove("typing");
    history.push({ role: "assistant", content: data.reply });
  } catch (err) {
    typingEl.textContent = "Network error: could not reach backend.";
    typingEl.classList.remove("typing");
  } finally {
    sendBtn.disabled = false;
  }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

checkHealth();
