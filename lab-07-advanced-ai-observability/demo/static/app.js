const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab07_observability_demo";

const state = {
  config: {
    invokeUrl: defaults.invokeUrl || "",
    authToken: defaults.authToken || "",
    traceparent: defaults.traceparent || "",
  },
};

const elements = {
  invokeUrl: document.getElementById("invokeUrl"),
  authToken: document.getElementById("authToken"),
  traceparent: document.getElementById("traceparent"),
  saveConfig: document.getElementById("saveConfig"),
  promptInput: document.getElementById("promptInput"),
  modelId: document.getElementById("modelId"),
  temperature: document.getElementById("temperature"),
  generateTraceparent: document.getElementById("generateTraceparent"),
  sendTrace: document.getElementById("sendTrace"),
  invokeBtn: document.getElementById("invokeBtn"),
  invokeStatus: document.getElementById("invokeStatus"),
  traceStatus: document.getElementById("traceStatus"),
  traceSummary: document.getElementById("traceSummary"),
  stageList: document.getElementById("stageList"),
  modelLatency: document.getElementById("modelLatency"),
  answerText: document.getElementById("answerText"),
};

function randomHex(bytes) {
  const array = new Uint8Array(bytes);
  crypto.getRandomValues(array);
  return Array.from(array)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function buildTraceparent() {
  const traceId = randomHex(16);
  const spanId = randomHex(8);
  return `00-${traceId}-${spanId}-01`;
}

function loadConfig() {
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    try {
      state.config = { ...state.config, ...JSON.parse(saved) };
    } catch (err) {
      console.warn("Failed to parse saved config", err);
    }
  }
  elements.invokeUrl.value = state.config.invokeUrl;
  elements.authToken.value = state.config.authToken;
  elements.traceparent.value = state.config.traceparent;
}

function saveConfig() {
  state.config.invokeUrl = elements.invokeUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  state.config.traceparent = elements.traceparent.value.trim();
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  setStatus(elements.invokeStatus, "Settings saved", "ok");
  setStatus(elements.traceStatus, "Settings saved", "ok");
}

function setStatus(el, text, mode) {
  el.textContent = text;
  el.classList.remove("ok", "error", "busy");
  if (mode) {
    el.classList.add(mode);
  }
}

async function invoke() {
  const prompt = elements.promptInput.value.trim();
  if (!state.config.invokeUrl) {
    setStatus(elements.invokeStatus, "Set invoke URL", "error");
    return;
  }
  if (!prompt) {
    setStatus(elements.invokeStatus, "Add a prompt", "error");
    return;
  }

  setStatus(elements.invokeStatus, "Invoking...", "busy");
  setStatus(elements.traceStatus, "Tracing...", "busy");

  const traceparentValue = elements.traceparent.value.trim();
  const payload = {
    invoke_url: state.config.invokeUrl,
    auth_token: state.config.authToken,
    prompt,
    model_id: elements.modelId.value.trim(),
    temperature: Number(elements.temperature.value || 0.2),
    traceparent: elements.sendTrace.checked ? traceparentValue : "",
  };

  try {
    const res = await fetch("/api/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    const payloadResp = data.payload || {};
    const hasError = !res.ok || (data.status && data.status >= 400) || payloadResp.error;
    if (hasError) {
      setStatus(elements.invokeStatus, payloadResp.error || data.error || "Error", "error");
      setStatus(elements.traceStatus, "Failed", "error");
      return;
    }
    renderTrace(payloadResp.trace || {});
    renderStages(payloadResp.lifecycle || []);
    renderLatency(payloadResp);
    renderAnswer(payloadResp.answer || "No answer returned.");
    setStatus(elements.invokeStatus, "Response ready", "ok");
    setStatus(elements.traceStatus, "Trace captured", "ok");
  } catch (err) {
    setStatus(elements.invokeStatus, "Network error", "error");
    setStatus(elements.traceStatus, "Network error", "error");
  }
}

function renderTrace(trace) {
  if (!trace || !trace.trace_id) {
    elements.traceSummary.textContent = "No trace data returned.";
    return;
  }
  const exporter = trace.otel_exporter || "none";
  elements.traceSummary.textContent = `Trace ID: ${trace.trace_id} | Span ID: ${trace.span_id || "n/a"} | Exporter: ${exporter}`;
  if (trace.traceparent) {
    elements.traceparent.value = trace.traceparent;
  }
}

function renderStages(stages) {
  elements.stageList.innerHTML = "";
  if (!stages.length) {
    elements.stageList.textContent = "No lifecycle stages returned.";
    return;
  }
  stages.forEach((stage) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-meta">${stage.name} • start ${Number(stage.start_ms).toFixed(2)} ms</div>
      <div class="result-text">Duration: ${Number(stage.duration_ms).toFixed(2)} ms</div>
    `;
    elements.stageList.appendChild(card);
  });
}

function renderLatency(payload) {
  const total = Number(payload.latency_ms || 0).toFixed(2);
  const model = Number(payload.model_latency_ms || 0).toFixed(2);
  const nonModel = Number(payload.non_model_latency_ms || 0).toFixed(2);
  elements.modelLatency.textContent = `Total: ${total} ms | Model: ${model} ms | Non-model: ${nonModel} ms`;
}

function renderAnswer(answer) {
  elements.answerText.textContent = answer;
}

function init() {
  loadConfig();
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.invokeBtn.addEventListener("click", invoke);
  elements.generateTraceparent.addEventListener("click", () => {
    elements.traceparent.value = buildTraceparent();
  });
}

init();
