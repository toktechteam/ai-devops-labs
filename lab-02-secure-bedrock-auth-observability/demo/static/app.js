const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "bedrock_demo_config";

const state = {
  config: {
    apiUrl: defaults.apiUrl || "",
    authToken: defaults.authToken || "",
    namespace: defaults.namespace || "Lab02/BedrockGateway",
    region: defaults.region || "us-east-1",
    modelId: defaults.modelId || "anthropic.claude-3-haiku-20240307-v1:0",
  },
  metrics: {},
};

const elements = {
  apiUrl: document.getElementById("apiUrl"),
  authToken: document.getElementById("authToken"),
  namespace: document.getElementById("namespace"),
  regionLabel: document.getElementById("regionLabel"),
  modelId: document.getElementById("modelId"),
  saveConfig: document.getElementById("saveConfig"),
  sendPrompt: document.getElementById("sendPrompt"),
  prompt: document.getElementById("prompt"),
  chatLog: document.getElementById("chatLog"),
  chatStatus: document.getElementById("chatStatus"),
  metricsStatus: document.getElementById("metricsStatus"),
  metricGrid: document.getElementById("metricGrid"),
};

function loadConfig() {
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      state.config = { ...state.config, ...parsed };
    } catch (err) {
      console.warn("Failed to parse saved config", err);
    }
  }
  elements.apiUrl.value = state.config.apiUrl;
  elements.authToken.value = state.config.authToken;
  elements.namespace.value = state.config.namespace;
  elements.modelId.value = state.config.modelId;
  elements.regionLabel.textContent = state.config.region;
}

function saveConfig() {
  state.config.apiUrl = elements.apiUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  state.config.namespace = elements.namespace.value.trim() || "Lab02/BedrockGateway";
  state.config.modelId = elements.modelId.value.trim() || state.config.modelId;
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  elements.regionLabel.textContent = state.config.region;
  flashStatus(elements.metricsStatus, "Settings saved", "ok");
}

function appendMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  elements.chatLog.appendChild(bubble);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
}

function flashStatus(el, text, mode) {
  el.textContent = text;
  el.classList.remove("ok", "error", "busy");
  if (mode) {
    el.classList.add(mode);
  }
}

async function sendPrompt() {
  const prompt = elements.prompt.value.trim();
  if (!prompt) {
    flashStatus(elements.chatStatus, "Enter a prompt", "error");
    return;
  }
  if (!state.config.apiUrl) {
    flashStatus(elements.chatStatus, "Set API URL", "error");
    return;
  }
  appendMessage("user", prompt);
  elements.prompt.value = "";
  flashStatus(elements.chatStatus, "Thinking...", "busy");

  try {
    const res = await fetch("/api/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_url: state.config.apiUrl,
        auth_token: state.config.authToken,
        prompt,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      appendMessage("assistant", data.error || "Request failed");
      flashStatus(elements.chatStatus, "Error", "error");
      return;
    }

    const payload = data.payload || {};
    const responseText = payload.response || payload.error || "No response";
    appendMessage("assistant", responseText);
    flashStatus(elements.chatStatus, "Done", "ok");
  } catch (err) {
    appendMessage("assistant", "Network error");
    flashStatus(elements.chatStatus, "Network error", "error");
  }
}

function sparkline(points, width = 140, height = 40) {
  if (!points.length) {
    return `<svg width="${width}" height="${height}"></svg>`;
  }
  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / Math.max(points.length - 1, 1);

  const path = points
    .map((p, idx) => {
      const x = idx * step;
      const y = height - ((p.value - min) / range) * height;
      return `${idx === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      <path d="${path}" fill="none" stroke="#ff8a3d" stroke-width="2" />
    </svg>
  `;
}

function renderMetrics(metrics) {
  elements.metricGrid.innerHTML = "";
  const order = [
    "LatencyMs",
    "ModelLatencyMs",
    "NonModelLatencyMs",
    "ApiGatewayToLambdaMs",
    "EstimatedTokens",
  ];

  order.forEach((name) => {
    const series = metrics[name] || [];
    const latest = series.length ? series[series.length - 1].value : "-";
    const unit = name === "EstimatedTokens" ? "count" : "ms";

    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `
      <div class="metric-name">${name}</div>
      <div class="metric-value">${latest} <span>${unit}</span></div>
      <div class="metric-spark">${sparkline(series)}</div>
    `;
    elements.metricGrid.appendChild(card);
  });
}

async function loadMetrics() {
  flashStatus(elements.metricsStatus, "Refreshing...", "busy");
  try {
    const params = new URLSearchParams({
      namespace: state.config.namespace,
      region: state.config.region,
      model_id: state.config.modelId,
      minutes: "30",
      period: "60",
    });
    const res = await fetch(`/api/metrics?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) {
      flashStatus(elements.metricsStatus, "Failed", "error");
      return;
    }
    state.metrics = data.metrics || {};
    renderMetrics(state.metrics);
    flashStatus(elements.metricsStatus, "Live", "ok");
  } catch (err) {
    flashStatus(elements.metricsStatus, "Error", "error");
  }
}

function init() {
  loadConfig();
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.sendPrompt.addEventListener("click", sendPrompt);
  elements.prompt.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      sendPrompt();
    }
  });
  loadMetrics();
  setInterval(loadMetrics, 15000);
}

init();
