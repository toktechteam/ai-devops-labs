const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab08_security_demo";

const state = {
  config: {
    invokeUrl: defaults.invokeUrl || "",
    authToken: defaults.authToken || "",
    policyMode: "strict",
  },
};

const elements = {
  invokeUrl: document.getElementById("invokeUrl"),
  authToken: document.getElementById("authToken"),
  policyMode: document.getElementById("policyMode"),
  saveConfig: document.getElementById("saveConfig"),
  promptInput: document.getElementById("promptInput"),
  modelId: document.getElementById("modelId"),
  temperature: document.getElementById("temperature"),
  allowOverride: document.getElementById("allowOverride"),
  outputFilter: document.getElementById("outputFilter"),
  invokeBtn: document.getElementById("invokeBtn"),
  invokeStatus: document.getElementById("invokeStatus"),
  decisionStatus: document.getElementById("decisionStatus"),
  policySummary: document.getElementById("policySummary"),
  policyViolations: document.getElementById("policyViolations"),
  stageList: document.getElementById("stageList"),
  answerText: document.getElementById("answerText"),
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
  elements.invokeUrl.value = state.config.invokeUrl;
  elements.authToken.value = state.config.authToken;
  elements.policyMode.value = state.config.policyMode || "strict";
}

function saveConfig() {
  state.config.invokeUrl = elements.invokeUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  state.config.policyMode = elements.policyMode.value;
  localStorage.setItem(storageKey, JSON.stringify(state.config));
  setStatus(elements.invokeStatus, "Settings saved", "ok");
  setStatus(elements.decisionStatus, "Settings saved", "ok");
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

  setStatus(elements.invokeStatus, "Securing...", "busy");
  setStatus(elements.decisionStatus, "Evaluating...", "busy");

  const payload = {
    invoke_url: state.config.invokeUrl,
    auth_token: state.config.authToken,
    prompt,
    model_id: elements.modelId.value.trim(),
    temperature: Number(elements.temperature.value || 0.2),
    policy_mode: state.config.policyMode,
    allow_override: elements.allowOverride.checked,
    enable_output_filter: elements.outputFilter.checked,
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
      setStatus(elements.decisionStatus, "Blocked", "error");
      renderPolicy(payloadResp.policy || {}, false);
      renderViolations(payloadResp.policy?.violations || []);
      renderStages(payloadResp.lifecycle || []);
      renderAnswer(payloadResp.answer || "No answer returned.");
      return;
    }

    renderPolicy(payloadResp.policy || {}, payloadResp.allowed !== false);
    renderViolations(payloadResp.policy?.violations || []);
    renderStages(payloadResp.lifecycle || []);
    renderAnswer(payloadResp.answer || "No answer returned.");

    setStatus(elements.invokeStatus, "Response ready", "ok");
    setStatus(elements.decisionStatus, "Decision ready", "ok");
  } catch (err) {
    setStatus(elements.invokeStatus, "Network error", "error");
    setStatus(elements.decisionStatus, "Network error", "error");
  }
}

function renderPolicy(policy, allowed) {
  if (!policy || typeof policy !== "object") {
    elements.policySummary.textContent = "No policy data.";
    return;
  }
  const mode = policy.mode || "strict";
  const risk = policy.risk_score ?? "n/a";
  const injection = policy.injection_detected ? "yes" : "no";
  const sensitive = policy.sensitive_detected ? "yes" : "no";
  const override = policy.allow_override ? "yes" : "no";
  const status = allowed ? "allowed" : "blocked";
  elements.policySummary.textContent = `Status: ${status} | Mode: ${mode} | Risk: ${risk} | Injection: ${injection} | Sensitive: ${sensitive} | Override: ${override}`;
}

function renderViolations(violations) {
  elements.policyViolations.innerHTML = "";
  if (!violations.length) {
    elements.policyViolations.textContent = "No violations.";
    return;
  }
  violations.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<div class="result-text">${item}</div>`;
    elements.policyViolations.appendChild(card);
  });
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
      <div class="result-meta">${stage.name} - start ${Number(stage.start_ms).toFixed(2)} ms</div>
      <div class="result-text">Duration: ${Number(stage.duration_ms).toFixed(2)} ms</div>
    `;
    elements.stageList.appendChild(card);
  });
}

function renderAnswer(answer) {
  elements.answerText.textContent = answer;
}

function init() {
  loadConfig();
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.invokeBtn.addEventListener("click", invoke);
}

init();
