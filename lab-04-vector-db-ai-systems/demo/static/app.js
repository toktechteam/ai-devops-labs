const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab04_vector_demo";

const state = {
  config: {
    ingestUrl: defaults.ingestUrl || "",
    searchUrl: defaults.searchUrl || "",
    authToken: defaults.authToken || "",
  },
};

const elements = {
  ingestUrl: document.getElementById("ingestUrl"),
  searchUrl: document.getElementById("searchUrl"),
  authToken: document.getElementById("authToken"),
  saveConfig: document.getElementById("saveConfig"),
  docId: document.getElementById("docId"),
  textInput: document.getElementById("textInput"),
  fileInput: document.getElementById("fileInput"),
  ingestBtn: document.getElementById("ingestBtn"),
  ingestStatus: document.getElementById("ingestStatus"),
  queryInput: document.getElementById("queryInput"),
  topK: document.getElementById("topK"),
  searchBtn: document.getElementById("searchBtn"),
  searchStatus: document.getElementById("searchStatus"),
  searchResults: document.getElementById("searchResults"),
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
  elements.searchUrl.value = state.config.searchUrl;
  elements.authToken.value = state.config.authToken;
}

function saveConfig() {
  state.config.ingestUrl = elements.ingestUrl.value.trim();
  state.config.searchUrl = elements.searchUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  setStatus(elements.ingestStatus, "Settings saved", "ok");
  setStatus(elements.searchStatus, "Settings saved", "ok");
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

async function search() {
  const query = elements.queryInput.value.trim();
  if (!state.config.searchUrl) {
    setStatus(elements.searchStatus, "Set search URL", "error");
    return;
  }
  if (!query) {
    setStatus(elements.searchStatus, "Add a query", "error");
    return;
  }
  setStatus(elements.searchStatus, "Searching...", "busy");

  const payload = {
    search_url: state.config.searchUrl,
    auth_token: state.config.authToken,
    query,
    top_k: Number(elements.topK.value || 5),
  };

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(elements.searchStatus, data.error || "Error", "error");
      return;
    }
    const results = data.payload?.results || [];
    renderResults(results);
    setStatus(elements.searchStatus, `Results: ${results.length}`, "ok");
  } catch (err) {
    setStatus(elements.searchStatus, "Network error", "error");
  }
}

function renderResults(results) {
  elements.searchResults.innerHTML = "";
  if (!results.length) {
    elements.searchResults.textContent = "No matches yet.";
    return;
  }
  results.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-meta">Doc: ${item.doc_id} - Chunk: ${item.chunk_id} - Score: ${Number(item.score).toFixed(3)}</div>
      <div class="result-text">${item.text}</div>
    `;
    elements.searchResults.appendChild(card);
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
  elements.searchBtn.addEventListener("click", search);
  elements.fileInput.addEventListener("change", handleFileUpload);
}

init();
