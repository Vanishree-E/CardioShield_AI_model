/*
 * CardioXAI Doctor Triage
 * Standalone client-side module.
 *
 * Reads the probability displayed by the existing prediction result
 * and adds a four-level doctor triage panel.
 *
 * Thresholds are application/demo thresholds and should be validated
 * before any real clinical use.
 */

(function () {
  "use strict";

  const TRIAGE_LEVELS = {
    LOW: {
      min: 0,
      max: 0.25,
      label: "LOW",
      className: "doctor-triage-low",
      icon: "●",
      title: "Lower risk pattern",
      message:
        "The model estimates a relatively lower probability pattern. Routine clinical review may be appropriate.",
      action: "Continue normal clinical assessment."
    },

    BORDERLINE: {
      min: 0.25,
      max: 0.50,
      label: "BORDERLINE",
      className: "doctor-triage-borderline",
      icon: "●",
      title: "Borderline risk pattern",
      message:
        "The estimated probability is in the borderline range and should be reviewed together with the patient's clinical information.",
      action: "Review symptoms, history and relevant measurements."
    },

    HIGH: {
      min: 0.50,
      max: 0.75,
      label: "HIGH RISK",
      className: "doctor-triage-high",
      icon: "●",
      title: "Elevated risk pattern",
      message:
        "The model estimates an elevated probability pattern.",
      action:
        "Doctor review is recommended. Consider the complete clinical picture."
    },

    VERY_HIGH: {
      min: 0.75,
      max: 1.01,
      label: "HIGH RISK — DOCTOR ALERT",
      className: "doctor-triage-critical",
      icon: "!",
      title: "High-risk model result",
      message:
        "The model probability is in the highest triage range.",
      action:
        "Prompt doctor review is recommended. Do not use this model result alone to make a diagnosis or treatment decision."
    }
  };

  function getTriageLevel(probability) {
    const p = Number(probability);

    if (!Number.isFinite(p)) {
      return null;
    }

    const value = Math.max(0, Math.min(1, p));

    if (value < TRIAGE_LEVELS.BORDERLINE.min) {
      return TRIAGE_LEVELS.LOW;
    }

    if (value < TRIAGE_LEVELS.HIGH.min) {
      return TRIAGE_LEVELS.BORDERLINE;
    }

    if (value < TRIAGE_LEVELS.VERY_HIGH.min) {
      return TRIAGE_LEVELS.HIGH;
    }

    return TRIAGE_LEVELS.VERY_HIGH;
  }

  function createTriagePanel() {
    if (document.getElementById("doctor-triage-panel")) {
      return document.getElementById("doctor-triage-panel");
    }

    const panel = document.createElement("div");

    panel.id = "doctor-triage-panel";
    panel.className = "doctor-triage-panel";
    panel.setAttribute("aria-live", "polite");

    panel.innerHTML = `
      <div class="doctor-triage-header">
        <div>
          <div class="doctor-triage-eyebrow">DOCTOR TRIAGE</div>
          <h3 class="doctor-triage-heading">Risk classification</h3>
        </div>
        <div id="doctor-triage-status" class="doctor-triage-status"></div>
      </div>

      <div class="doctor-triage-body">
        <div class="doctor-triage-probability">
          <span>Model probability</span>
          <strong id="doctor-triage-probability">—</strong>
        </div>

        <div class="doctor-triage-scale">
          <div class="doctor-triage-scale-track">
            <span class="doctor-triage-marker marker-low"></span>
            <span class="doctor-triage-marker marker-borderline"></span>
            <span class="doctor-triage-marker marker-high"></span>
            <span class="doctor-triage-marker marker-critical"></span>
            <div id="doctor-triage-scale-indicator"></div>
          </div>

          <div class="doctor-triage-scale-labels">
            <span>LOW</span>
            <span>BORDERLINE</span>
            <span>HIGH</span>
            <span>ALERT</span>
          </div>
        </div>

        <div class="doctor-triage-message">
          <strong id="doctor-triage-title"></strong>
          <p id="doctor-triage-message"></p>
        </div>

        <div class="doctor-triage-action">
          <span class="doctor-triage-action-label">Suggested review</span>
          <p id="doctor-triage-action"></p>
        </div>

        <div class="doctor-triage-disclaimer">
          Decision-support display only. This classification is based on
          the model probability and should not be treated as a standalone
          medical diagnosis.
        </div>
      </div>
    `;

    const resultPanel = document.getElementById("result-panel");

    if (resultPanel && resultPanel.parentNode) {
      resultPanel.parentNode.insertBefore(panel, resultPanel.nextSibling);
    } else {
      document.body.appendChild(panel);
    }

    return panel;
  }

  function updateTriage(probability) {
    const level = getTriageLevel(probability);

    if (!level) {
      return;
    }

    const panel = createTriagePanel();

    const percent = Math.round(
      Math.max(0, Math.min(1, Number(probability))) * 100
    );

    const status = document.getElementById("doctor-triage-status");
    const probabilityElement = document.getElementById(
      "doctor-triage-probability"
    );
    const title = document.getElementById("doctor-triage-title");
    const message = document.getElementById("doctor-triage-message");
    const action = document.getElementById("doctor-triage-action");
    const indicator = document.getElementById(
      "doctor-triage-scale-indicator"
    );

    if (
      !status ||
      !probabilityElement ||
      !title ||
      !message ||
      !action ||
      !indicator
    ) {
      return;
    }

    Object.values(TRIAGE_LEVELS).forEach(function (item) {
      panel.classList.remove(item.className);
    });

    panel.classList.add(level.className);

    status.textContent = level.icon + " " + level.label;
    probabilityElement.textContent = percent + "%";
    title.textContent = level.title;
    message.textContent = level.message;
    action.textContent = level.action;
    indicator.style.left = percent + "%";
    panel.style.display = "block";

    if (level === TRIAGE_LEVELS.VERY_HIGH) {
      console.warn(
        "[CardioXAI Doctor Alert] High-risk model result:",
        percent + "%"
      );
    }
  }

  function readProbabilityFromExistingResult() {
    const caption = document.getElementById("prob-caption");

    if (!caption) {
      return null;
    }

    const text = caption.textContent || "";

    const match = text.match(
      /(\d+(?:\.\d+)?)%\s*chance\s+of\s+heart\s+disease/i
    );

    if (!match) {
      return null;
    }

    const percent = parseFloat(match[1]);

    if (!Number.isFinite(percent)) {
      return null;
    }

    return percent / 100;
  }

  function observeExistingResult() {
    const resultContent = document.getElementById("result-content");

    if (!resultContent) {
      return;
    }

    const observer = new MutationObserver(function () {
      const probability = readProbabilityFromExistingResult();

      if (probability !== null) {
        updateTriage(probability);
      }
    });

    observer.observe(resultContent, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true
    });

    const initialProbability = readProbabilityFromExistingResult();

    if (initialProbability !== null) {
      updateTriage(initialProbability);
    }
  }

  function init() {
    createTriagePanel();
    observeExistingResult();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.CardioXAITriage = {
    update: updateTriage,
    getLevel: getTriageLevel
  };
})();
