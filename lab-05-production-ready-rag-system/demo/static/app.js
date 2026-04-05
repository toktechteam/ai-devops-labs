const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab05_rag_demo";

const state = {
  config: {
    ingestUrl: defaults.ingestUrl || "",
    retrieveUrl: defaults.retrieveUrl || "",
    askUrl: defaults.askUrl || "",
    authToken: defaults.authToken || "",
  },
};

const elements = {
  ingestUrl: document.getElementById("ingestUrl"),
  retrieveUrl: document.getElementById("retrieveUrl"),
  askUrl: document.getElementById("askUrl"),
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
  queryInput: document.getElementById("queryInput"),
  topK: document.getElementById("topK"),
  filters: document.getElementById("filters"),
  retrieveBtn: document.getElementById("retrieveBtn"),
  retrieveStatus: document.getElementById("retrieveStatus"),
  retrieveResults: document.getElementById("retrieveResults"),
  questionInput: document.getElementById("questionInput"),
  askTopK: document.getElementById("askTopK"),
  temperature: document.getElementById("temperature"),
  modelId: document.getElementById("modelId"),
  askBtn: document.getElementById("askBtn"),
  askStatus: document.getElementById("askStatus"),
  answerText: document.getElementById("answerText"),
  citationResults: document.getElementById("citationResults"),
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
  elements.retrieveUrl.value = state.config.retrieveUrl;
  elements.askUrl.value = state.config.askUrl;
  elements.authToken.value = state.config.authToken;
}

function saveConfig() {
  state.config.ingestUrl = elements.ingestUrl.value.trim();
  state.config.retrieveUrl = elements.retrieveUrl.value.trim();
  state.config.askUrl = elements.askUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  setStatus(elements.ingestStatus, "Settings saved", "ok");
  setStatus(elements.retrieveStatus, "Settings saved", "ok");
  setStatus(elements.askStatus, "Settings saved", "ok");
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
    doc_id: elements.docId.value.trim() || "sample-doc",
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

async function retrieve() {
  const query = elements.queryInput.value.trim();
  if (!state.config.retrieveUrl) {
    setStatus(elements.retrieveStatus, "Set retrieve URL", "error");
    return;
  }
  if (!query) {
    setStatus(elements.retrieveStatus, "Add a query", "error");
    return;
  }
  setStatus(elements.retrieveStatus, "Retrieving...", "busy");

  const payload = {
    retrieve_url: state.config.retrieveUrl,
    auth_token: state.config.authToken,
    query,
    top_k: Number(elements.topK.value || 5),
    filters: elements.filters.value.trim(),
  };

  try {
    const res = await fetch("/api/retrieve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(elements.retrieveStatus, data.error || "Error", "error");
      return;
    }
    const results = data.payload?.results || [];
    renderRetrieveResults(results);
    setStatus(elements.retrieveStatus, `Results: ${results.length}`, "ok");
  } catch (err) {
    setStatus(elements.retrieveStatus, "Network error", "error");
  }
}

async function ask() {
  const question = elements.questionInput.value.trim();
  if (!state.config.askUrl) {
    setStatus(elements.askStatus, "Set ask URL", "error");
    return;
  }
  if (!question) {
    setStatus(elements.askStatus, "Add a question", "error");
    return;
  }
  setStatus(elements.askStatus, "Generating...", "busy");

  const payload = {
    ask_url: state.config.askUrl,
    auth_token: state.config.authToken,
    question,
    top_k: Number(elements.askTopK.value || 5),
    temperature: Number(elements.temperature.value || 0.2),
    model_id: elements.modelId.value.trim(),
  };

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(elements.askStatus, data.error || "Error", "error");
      return;
    }
    const payloadResp = data.payload || {};
    renderAnswer(payloadResp.answer || "No answer returned.");
    renderCitations(payloadResp.citations || []);
    setStatus(elements.askStatus, "Answer ready", "ok");
  } catch (err) {
    setStatus(elements.askStatus, "Network error", "error");
  }
}

function renderRetrieveResults(results) {
  elements.retrieveResults.innerHTML = "";
  if (!results.length) {
    elements.retrieveResults.textContent = "No matches yet.";
    return;
  }
  results.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-meta">Doc: ${item.doc_id} - Chunk: ${item.chunk_id} - Score: ${Number(item.score).toFixed(3)}</div>
      <div class="result-text">${item.text || ""}</div>
    `;
    elements.retrieveResults.appendChild(card);
  });
}

function renderAnswer(answer) {
  elements.answerText.textContent = answer;
}

function renderCitations(citations) {
  elements.citationResults.innerHTML = "";
  if (!citations.length) {
    elements.citationResults.textContent = "No citations returned.";
    return;
  }
  citations.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-meta">Doc: ${item.doc_id} - Chunk: ${item.chunk_id} - Score: ${Number(item.score || 0).toFixed(3)}</div>
    `;
    elements.citationResults.appendChild(card);
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
    elements.docId.value = "sample-doc";
  }
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.ingestBtn.addEventListener("click", ingest);
  elements.retrieveBtn.addEventListener("click", retrieve);
  elements.askBtn.addEventListener("click", ask);
  elements.fileInput.addEventListener("change", handleFileUpload);
}

init();
