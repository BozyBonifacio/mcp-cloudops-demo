const messages = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const trace = document.getElementById("trace");
const traceCount = document.getElementById("traceCount");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "Y" : "M";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const label = document.createElement("strong");
  label.textContent = role === "user" ? "You" : "CloudOps MCP";
  const body = document.createElement("p");
  body.textContent = text;
  bubble.append(label, body);
  row.append(avatar, bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function renderTrace(items) {
  trace.innerHTML = "";
  traceCount.textContent = `${items.length} ${items.length === 1 ? "call" : "calls"}`;
  if (!items.length) {
    trace.innerHTML = '<div class="empty">No MCP calls reported.</div>';
    return;
  }
  for (const item of items) {
    const el = document.createElement("div");
    el.className = "trace-item";
    const title = document.createElement("strong");
    title.textContent = `${item.kind.toUpperCase()} · ${item.name}`;
    const args = document.createElement("code");
    args.textContent = Object.keys(item.arguments || {}).length ? JSON.stringify(item.arguments) : "discovery";
    el.append(title, args);
    trace.appendChild(el);
  }
}

function renderChips(id, values) {
  const el = document.getElementById(id);
  el.innerHTML = "";
  values.forEach(value => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    el.appendChild(chip);
  });
}

async function loadCapabilities() {
  const dot = document.querySelector(".dot");
  try {
    const response = await fetch("/api/capabilities");
    if (!response.ok) throw new Error("Capability discovery failed");
    const data = await response.json();
    document.getElementById("toolCount").textContent = data.tools.length;
    document.getElementById("resourceCount").textContent = data.resources.length;
    document.getElementById("promptCount").textContent = data.prompts.length;
    renderChips("tools", data.tools);
    renderChips("resources", data.resources);
    renderChips("prompts", data.prompts);
    document.getElementById("statusText").textContent = "MCP server online";
    dot.classList.add("online");
  } catch (error) {
    document.getElementById("statusText").textContent = "MCP server unavailable";
    dot.classList.add("offline");
  }
}

async function submitMessage(message) {
  const text = message.trim();
  if (!text) return;
  addMessage("user", text);
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.textContent = "Calling MCP…";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    addMessage("assistant", data.answer);
    renderTrace(data.trace || []);
  } catch (error) {
    addMessage("assistant", `Request failed: ${error.message}. Check the terminal running mcp-cloudops-web.`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Run through MCP";
    input.focus();
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  submitMessage(input.value);
});
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
document.querySelectorAll("[data-prompt]").forEach(button => {
  button.addEventListener("click", () => submitMessage(button.dataset.prompt));
});
document.getElementById("clearBtn").addEventListener("click", () => {
  messages.innerHTML = "";
  addMessage("assistant", "Chat cleared. Pick a suggested CloudOps scenario or type a question.");
  renderTrace([]);
});

loadCapabilities();
