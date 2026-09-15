const form = document.getElementById("predict-form");
let shapChart = null;
let limeChart = null;
let lastPredictPayload = null;   // patient inputs from the most recent /predict call
let lastPredictResult = null;    // full response from the most recent /predict call

const COLOR_RISK = "#E8664E";     // pushes toward disease
const COLOR_PROTECT = "#3FBFAE";  // pushes toward no disease

function fieldValues() {
  const fd = new FormData(form);
  const data = {};
  for (const [key, val] of fd.entries()) {
    if (key === "model_name") { data[key] = val; continue; }
    data[key] = key === "oldpeak" ? parseFloat(val) : parseInt(val, 10);
  }
  return data;
}

function renderResult(res) {
  const badge = document.getElementById("result-badge");
  const isHigh = res.prediction === 1;
  badge.className = "result-badge " + (isHigh ? "high" : "low");
  badge.textContent = isHigh
    ? `Higher risk pattern — estimated ${(res.probability_disease * 100).toFixed(1)}% chance of heart disease`
    : `Lower risk pattern — estimated ${(res.probability_disease * 100).toFixed(1)}% chance of heart disease`;

  document.getElementById("prob-fill").style.width = (res.probability_disease * 100).toFixed(1) + "%";
  document.getElementById("prob-caption").textContent =
    `Estimated using the ${res.model_used} model · ${(res.probability_disease * 100).toFixed(1)}% chance of heart disease vs ${(res.probability_no_disease * 100).toFixed(1)}% chance of no heart disease · This is a statistical estimate, not a diagnosis.`;

  document.getElementById("result-empty").style.display = "none";
  document.getElementById("result-content").style.display = "block";
}

function renderPlan(plan, quote) {
  if (!plan) return;
  const panel = document.getElementById("plan-panel");
  panel.style.display = "block";

  const badge = document.getElementById("plan-stage-badge");
  const isRisky = plan.stage === "elevated" || plan.stage === "high";
  badge.className = "tag " + (isRisky ? "high" : "low");
  badge.textContent = plan.stage_label;

  const altList = document.getElementById("plan-alternatives");
  altList.innerHTML = "";
  plan.alternatives.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    altList.appendChild(li);
  });

  const dietList = document.getElementById("plan-diet");
  dietList.innerHTML = "";
  plan.diet.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    dietList.appendChild(li);
  });

  document.getElementById("plan-quote").textContent = quote ? `“${quote}”` : "";
}

function renderShapChart(shapValues) {
  const sorted = [...shapValues].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));
  const labels = sorted.map(d => `${d.feature} = ${d.value}`);
  const values = sorted.map(d => d.shap_value);
  const colors = values.map(v => (v > 0 ? COLOR_RISK : COLOR_PROTECT));

  document.getElementById("shap-empty").style.display = "none";
  const ctx = document.getElementById("shap-chart").getContext("2d");
  if (shapChart) shapChart.destroy();
  shapChart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderRadius: 3 }] },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `SHAP value: ${item.raw.toFixed(4)} (${item.raw > 0 ? "→ higher risk" : "→ lower risk"})`
          }
        }
      },
      scales: {
        x: { grid: { color: "#2A4347" }, ticks: { color: "#8FA8A6", font: { family: "IBM Plex Mono", size: 11 } } },
        y: { grid: { display: false }, ticks: { color: "#E9F1EF", font: { family: "IBM Plex Mono", size: 11 } } }
      }
    }
  });
}

function renderLimeChart(limeValues) {
  const sorted = [...limeValues].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const labels = sorted.map(d => d.condition);
  const values = sorted.map(d => d.contribution);
  const colors = values.map(v => (v > 0 ? COLOR_RISK : COLOR_PROTECT));

  document.getElementById("lime-empty").style.display = "none";
  const ctx = document.getElementById("lime-chart").getContext("2d");
  if (limeChart) limeChart.destroy();
  limeChart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderRadius: 3 }] },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `Contribution: ${item.raw.toFixed(4)} (${item.raw > 0 ? "→ higher risk" : "→ lower risk"})`
          }
        }
      },
      scales: {
        x: { grid: { color: "#2A4347" }, ticks: { color: "#8FA8A6", font: { family: "IBM Plex Mono", size: 11 } } },
        y: { grid: { display: false }, ticks: { color: "#E9F1EF", font: { family: "IBM Plex Mono", size: 11 } } }
      }
    }
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const submitBtn = form.querySelector("button[type=submit]");
  const originalText = submitBtn.textContent;
  submitBtn.textContent = "Checking...";
  submitBtn.disabled = true;

  try {
    const payload = fieldValues();
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || "Prediction failed");
    }
    const res = await response.json();
    renderResult(res);
    renderShapChart(res.shap_values);
    renderLimeChart(res.lime_values);
    renderPlan(res.plan, res.quote);

    // Remember this result so the "Ask AI to explain" button has something
    // to send, and reset the explain panel back to its un-clicked state --
    // a stale explanation from a previous prediction should never linger.
    lastPredictPayload = payload;
    lastPredictResult = res;
    document.getElementById("explain-panel").style.display = "block";
    document.getElementById("explain-content").style.display = "none";
    document.getElementById("explain-loading").style.display = "none";
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// "Ask AI to explain" -- sends the SHAP data from the last prediction to
// /explain, which either calls a real LLM (if configured server-side) or
// falls back to a rule-based generator. Either way it returns readable text
// plus a "mode" flag so we can label the source honestly.
// ---------------------------------------------------------------------------
const explainBtn = document.getElementById("explain-btn");
if (explainBtn) {
  explainBtn.addEventListener("click", async () => {
    if (!lastPredictResult || !lastPredictPayload) return;

    const loading = document.getElementById("explain-loading");
    const content = document.getElementById("explain-content");
    loading.style.display = "flex";
    content.style.display = "none";
    explainBtn.disabled = true;

    try {
      const response = await fetch("/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          payload: lastPredictPayload,
          shap_values: lastPredictResult.shap_values,
          prediction: lastPredictResult.prediction,
          probability_disease: lastPredictResult.probability_disease
        })
      });
      if (!response.ok) throw new Error("explain failed");
      const res = await response.json();

      const badge = document.getElementById("explain-source-badge");
      const isLlm = res.mode === "llm";
      badge.className = "tag " + (isLlm ? "low" : "high");
      badge.textContent = isLlm
        ? (window.I18N ? window.I18N.explainSourceLlm : "AI-generated (Claude)")
        : (window.I18N ? window.I18N.explainSourceTemplate : "Rule-based (offline)");

      document.getElementById("explain-text").textContent = res.explanation;
      content.style.display = "block";
    } catch (err) {
      document.getElementById("explain-text").textContent =
        window.I18N ? window.I18N.explainError : "Couldn't generate an explanation right now. Please try again.";
      content.style.display = "block";
    } finally {
      loading.style.display = "none";
      explainBtn.disabled = false;
    }
  });
}
