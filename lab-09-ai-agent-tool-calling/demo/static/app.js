const defaults = window.DEMO_DEFAULTS || {};
const storageKey = "lab09_agent_demo";

const state = {
  config: {
    invokeUrl: defaults.invokeUrl || "",
    authToken: defaults.authToken || "",
    toolStrategy: defaults.toolStrategy || "auto",
  },
};

const elements = {
  invokeUrl: document.getElementById("invokeUrl"),
  authToken: document.getElementById("authToken"),
  toolStrategy: document.getElementById("toolStrategy"),
  saveConfig: document.getElementById("saveConfig"),
  promptInput: document.getElementById("promptInput"),
  modelId: document.getElementById("modelId"),
  temperature: document.getElementById("temperature"),
  maxTools: document.getElementById("maxTools"),
  useModel: document.getElementById("useModel"),
  invokeBtn: document.getElementById("invokeBtn"),
  invokeStatus: document.getElementById("invokeStatus"),
  decisionStatus: document.getElementById("decisionStatus"),
  planSummary: document.getElementById("planSummary"),
  toolList: document.getElementById("toolList"),
  structuredOutput: document.getElementById("structuredOutput"),
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
  elements.toolStrategy.value = state.config.toolStrategy || "auto";
}

function saveConfig() {
  state.config.invokeUrl = elements.invokeUrl.value.trim();
  state.config.authToken = elements.authToken.value.trim();
  state.config.toolStrategy = elements.toolStrategy.value;
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

function formatJson(value) {
  if (!value || typeof value !== "object") {
    return "{}";
  }
  return JSON.stringify(value, null, 2);
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

  setStatus(elements.invokeStatus, "Running...", "busy");
  setStatus(elements.decisionStatus, "Working...", "busy");

  const payload = {
    invoke_url: state.config.invokeUrl,
    auth_token: state.config.authToken,
    prompt,
    model_id: elements.modelId.value.trim(),
    temperature: Number(elements.temperature.value || 0.2),
    tool_strategy: state.config.toolStrategy,
    max_tool_calls: Number(elements.maxTools.value || 3),
    use_model: elements.useModel.checked,
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
      setStatus(elements.decisionStatus, "Failed", "error");
      return;
    }

    const agent = payloadResp.agent || {};
    renderPlan(agent);
    renderTools(agent.tool_calls || []);
    renderStructured(agent.structured_output || {});
    renderStages(payloadResp.lifecycle || []);
    renderAnswer(agent.final_answer || "No answer returned.");

    setStatus(elements.invokeStatus, "Response ready", "ok");
    setStatus(elements.decisionStatus, "Decision ready", "ok");
  } catch (err) {
    setStatus(elements.invokeStatus, "Network error", "error");
    setStatus(elements.decisionStatus, "Network error", "error");
  }
}

function renderPlan(agent) {
  const plan = agent.plan || [];
  const planText = plan.length ? plan.join(" → ") : "No tools invoked.";
  const intent = agent.intent || "n/a";
  const reason = agent.plan_reason || "";
  elements.planSummary.textContent = `Intent: ${intent} | Plan: ${planText}${reason ? ` | Reason: ${reason}` : ""}`;
}

function renderTools(toolCalls) {
  elements.toolList.innerHTML = "";
  if (!toolCalls.length) {
    elements.toolList.textContent = "No tool calls executed.";
    return;
  }
  toolCalls.forEach((call) => {
    const card = document.createElement("div");
    card.className = "result-card";
    const duration = Number(call.duration_ms || 0).toFixed(2);
    card.innerHTML = `
      <div class="result-meta">${call.name} • ${duration} ms</div>
      <div class="result-json">Input:\n${formatJson(call.input)}</div>
      <div class="result-json">Output:\n${formatJson(call.output)}</div>
    `;
    elements.toolList.appendChild(card);
  });
}

function renderStructured(structured) {
  if (!structured || !Object.keys(structured).length) {
    elements.structuredOutput.textContent = "No structured output returned.";
    return;
  }
  elements.structuredOutput.textContent = formatJson(structured);
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

function renderAnswer(answer) {
  elements.answerText.textContent = answer;
}

function init() {
  loadConfig();
  elements.saveConfig.addEventListener("click", saveConfig);
  elements.invokeBtn.addEventListener("click", invoke);
}

init();
