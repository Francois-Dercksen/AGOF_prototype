const API_BASE = "https://agof-prototype.onrender.com";

const chatWindow = document.getElementById("chat-window");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

let history = [];

function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  if (content) div.textContent = content;
  chatWindow.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function renderMarkdown(el, text) {
  if (window.marked) {
    el.innerHTML = marked.parse(text);
  } else {
    el.textContent = text;
  }
}

function showTypingIndicator() {
  const div = document.createElement("div");
  div.className = "msg ai typing-indicator";
  div.innerHTML = "<span></span><span></span><span></span>";
  chatWindow.appendChild(div);
  scrollToBottom();
  return div;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  history.push({ role: "user", content: text });
  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;

  const typingEl = showTypingIndicator();
  let aiEl = null;
  let fullText = "";

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    });

    if (!res.ok || !res.body) {
      typingEl.remove();
      addMessage("ai", "Something went wrong. Please try again.");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunkText = decoder.decode(value, { stream: true });

      if (chunkText.startsWith("[ERROR]")) {
        typingEl.remove();
        addMessage("ai", "Something went wrong. Please try again.");
        return;
      }

      if (!aiEl) {
        typingEl.remove();
        aiEl = addMessage("ai", "");
      }

      fullText += chunkText;
      aiEl.textContent = fullText;
      scrollToBottom();
    }

    if (aiEl) {
      renderMarkdown(aiEl, fullText);
      scrollToBottom();
      history.push({ role: "assistant", content: fullText });
    } else {
      typingEl.remove();
      addMessage("ai", "No response received.");
    }
  } catch (err) {
    typingEl.remove();
    addMessage("ai", "Network error: could not reach the server.");
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
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
});
