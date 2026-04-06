const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab06_router_demo";

const state = {
  config: {
    ingestUrl: defaults.ingestUrl || "",
    routeUrl: defaults.routeUrl || "",
    authToken: defaults.authToken || "",
  },
};

const elements = {
  ingestUrl: document.getElementById("ingestUrl"),
  routeUrl: document.getElementById("routeUrl"),
  authToken: document.getElementById("authToken"),
  saveConfig: document.getElementById("saveConfig"),
  docId: document.getElementById("docId"),
  chunkSize: document.getElementById("chunkSize"),
  chunkOverlap: document.getElementById("chunkOverlap"),
  metadata: document.getElementById("metadata"),
  textInput: document.getElementById("textInput"),
  fileInput: document.getElementById("fileInput"),
  ingestBtn: document.getElementById("ingestBtn"),
  ingestStatus: document.getElementById("ingestStatus"),
  promptInput: document.getElementById("promptInput"),
  taskType: document.getElementById("taskType"),
  routeTopK: document.getElementById("routeTopK"),
  routeTemp: document.getElementById("routeTemp"),
  forceRag: document.getElementById("forceRag"),
  modelOverride: document.getElementById("modelOverride"),
  filters: document.getElementById("filters"),
  routeBtn: document.getElementById("routeBtn"),
  routeStatus: document.getElementById("routeStatus"),
  routeMeta: document.getElementById("routeMeta"),
  routeAnswer: document.getElementById("routeAnswer"),
  routeCitations: document.getElementById("routeCitations"),
};

function loadConfig() {
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      state.config = { ...state.config, ...JSON.parse(saved) };
    } catch (err) {
      console.warn("Failed to parse saved config", err);
    }
  }
  elements.ingestUrl.value = state.config.ingestUrl;
  elements.routeUrl.value = state.config.routeUrl;
  elements.authToken.value = state.config.authToken;
}

function saveConfig() {
  state.config.ingestUrl = elements.ingestUrl.value.trim();
  state.config.routeUrl = elements.routeUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  setStatus(elements.ingestStatus, "Settings saved", "ok");
  setStatus(elements.routeStatus, "Settings saved", "ok");
}

function setStatus(el, text, mode) {
  el.textContent = text;
  el.classList.remove("ok", "error", "busy");
  if (mode) {
    el.classList.add(mode);
  }
}

async function ingest() {
  const text = elements.textInput.value.trim();
  if (!state.config.ingestUrl) {
    setStatus(elements.ingestStatus, "Set ingest URL", "error");
    return;
  }
  if (!text) {
    setStatus(elements.ingestStatus, "Add text", "error");
    return;
  }
  setStatus(elements.ingestStatus, "Ingesting...", "busy");

  const payload = {
    ingest_url: state.config.ingestUrl,
    auth_token: state.config.authToken,
    doc_id: elements.docId.value.trim() || "routing-doc",
    text,
    chunk_size: Number(elements.chunkSize.value || 800),
    chunk_overlap: Number(elements.chunkOverlap.value || 120),
    metadata: elements.metadata.value.trim(),
  };

  try {
    const res = await fetch("/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(elements.ingestStatus, data.error || "Error", "error");
      return;
    }
    const payloadResp = data.payload || {};
    setStatus(
      elements.ingestStatus,
      `Indexed ${payloadResp.indexed || 0} chunks`,
      "ok"
    );
  } catch (err) {
    setStatus(elements.ingestStatus, "Network error", "error");
  }
}

async function routeRequest() {
  const prompt = elements.promptInput.value.trim();
  if (!state.config.routeUrl) {
    setStatus(elements.routeStatus, "Set route URL", "error");
    return;
  }
  if (!prompt) {
    setStatus(elements.routeStatus, "Add a prompt", "error");
    return;
  }
  setStatus(elements.routeStatus, "Routing...", "busy");

  const payload = {
    route_url: state.config.routeUrl,
    auth_token: state.config.authToken,
    prompt,
    task_type: elements.taskType.value,
    top_k: Number(elements.routeTopK.value || 5),
    temperature: Number(elements.routeTemp.value || 0.2),
    force_rag: elements.forceRag.checked,
    model_override: elements.modelOverride.value.trim(),
    filters: elements.filters.value.trim(),
  };

  try {
    const res = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(elements.routeStatus, data.error || "Error", "error");
      return;
    }
    const payloadResp = data.payload || {};
    renderRouteMeta(payloadResp);
    renderAnswer(payloadResp.answer || "No answer returned.");
    renderCitations(payloadResp.citations || []);
    setStatus(elements.routeStatus, "Answer ready", "ok");
  } catch (err) {
    setStatus(elements.routeStatus, "Network error", "error");
  }
}

function renderRouteMeta(payload) {
  const route = payload.route || "unknown";
  const model = payload.model_id || "unknown";
  const fallback = payload.fallback_used ? "yes" : "no";
  const retrieved = typeof payload.retrieved === "number" ? payload.retrieved : 0;
  elements.routeMeta.textContent = `Route: ${route} | Model: ${model} | Fallback: ${fallback} | Retrieved: ${retrieved}`;
}

function renderAnswer(answer) {
  elements.routeAnswer.textContent = answer;
}

function renderCitations(citations) {
  elements.routeCitations.innerHTML = "";
  if (!citations.length) {
    elements.routeCitations.textContent = "No citations returned.";
    return;
  }
  citations.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-meta">Doc: ${item.doc_id} - Chunk: ${item.chunk_id} - Score: ${Number(item.score || 0).toFixed(3)}</div>
    `;
    elements.routeCitations.appendChild(card);
  });
}

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    elements.textInput.value = reader.result || "";
  };
  reader.readAsText(file);
}

function init() {
  loadConfig();
  if (!elements.docId.value.trim()) {
    elements.docId.value = "routing-doc";
  }
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.ingestBtn.addEventListener("click", ingest);
  elements.routeBtn.addEventListener("click", routeRequest);
  elements.fileInput.addEventListener("change", handleFileUpload);
}

init();
