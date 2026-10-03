(() => {
  "use strict";

  const PYODIDE_INDEX = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

  const chatLog = document.querySelector("#chat-log");
  const interactionPanel = document.querySelector("#interaction-panel");
  const typingIndicator = document.querySelector("#typing-indicator");
  const loadOverlay = document.querySelector("#load-overlay");
  const loadTitle = document.querySelector("#load-title");
  const runtimeStatus = document.querySelector("#runtime-status");
  const runtimeLed = document.querySelector(".tiny-led");
  const errorBox = document.querySelector("#input-error");
  const restartButton = document.querySelector("#restart-button");
  const phoneTime = document.querySelector("#phone-time");

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let pyodide;
  let startGamePy;
  let choosePy;
  let submitValuePy;
  let restartGamePy;
  let busy = false;

  const delay = (ms) =>
    prefersReducedMotion ? Promise.resolve() : new Promise((resolve) => setTimeout(resolve, ms));

  function updateClock() {
    const now = new Date();
    phoneTime.textContent = now.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function nowStamp() {
    return new Date().toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      chatLog.scrollTop = chatLog.scrollHeight;
    });
  }

  function addMessage(text, sender = "bestie") {
    const row = document.createElement("div");
    row.className = `message-row ${sender === "player" ? "player" : "bestie"}`;

    if (sender === "bestie") {
      const avatar = document.createElement("div");
      avatar.className = "message-avatar mini";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = "★";
      row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const copy = document.createElement("span");
    copy.textContent = text;

    const time = document.createElement("span");
    time.className = "message-time";
    time.textContent = nowStamp();

    bubble.append(copy, time);
    row.appendChild(bubble);
    chatLog.appendChild(row);
    scrollToBottom();
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function setTyping(visible) {
    typingIndicator.hidden = !visible;
    if (visible) scrollToBottom();
  }

  function clearInteraction() {
    interactionPanel.replaceChildren();
    clearError();
  }

  async function addBestieMessages(messages) {
    for (const message of messages) {
      setTyping(true);
      await delay(330);
      setTyping(false);
      addMessage(message, "bestie");
      await delay(90);
    }
  }

  function renderChoices(choices) {
    const fragment = document.createDocumentFragment();

    choices.forEach((choice) => {
      const button = document.createElement("button");
      button.className = "choice-button";
      button.type = "button";
      button.textContent = choice.label;
      button.addEventListener("click", () => handleChoice(choice));
      fragment.appendChild(button);
    });

    interactionPanel.appendChild(fragment);
  }

  function renderNumberInput(config) {
    const form = document.createElement("form");
    form.className = "number-form";

    const input = document.createElement("input");
    input.type = "number";
    input.inputMode = "numeric";
    input.placeholder = config.placeholder || "type a number";
    input.required = true;

    if (config.min !== undefined && config.min !== null) input.min = String(config.min);
    if (config.max !== undefined && config.max !== null) input.max = String(config.max);
    if (config.step !== undefined && config.step !== null) input.step = String(config.step);

    const button = document.createElement("button");
    button.className = "send-button";
    button.type = "submit";
    button.textContent = config.button || "send";

    form.append(input, button);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      handleNumberSubmit(input.value, input);
    });

    interactionPanel.appendChild(form);
    requestAnimationFrame(() => input.focus());
  }

  function renderEndingActions() {
    const actions = document.createElement("div");
    actions.className = "ending-actions";

    const again = document.createElement("button");
    again.className = "ending-button";
    again.type = "button";
    again.textContent = "play again";
    again.addEventListener("click", restartGame);

    const arcade = document.createElement("a");
    arcade.className = "ending-button secondary";
    arcade.href = "../../games.html";
    arcade.textContent = "back to arcade";

    actions.append(again, arcade);
    interactionPanel.appendChild(actions);
  }

  function renderInteraction(payload) {
    clearInteraction();

    if (payload.ended) {
      renderEndingActions();
      return;
    }

    if (payload.choices?.length) {
      renderChoices(payload.choices);
      return;
    }

    if (payload.input) {
      renderNumberInput(payload.input);
    }
  }

  async function renderPayload(payload, { skipMessages = false } = {}) {
    if (payload.error) {
      showError(payload.error);
      renderInteraction({ ...payload, error: null });
      return;
    }

    clearError();

    if (!skipMessages) {
      await addBestieMessages(payload.messages || []);
    }

    renderInteraction(payload);
  }

  async function handleChoice(choice) {
    if (busy) return;
    busy = true;

    clearInteraction();
    addMessage(choice.label, "player");

    try {
      const payload = JSON.parse(choosePy(choice.value));
      await renderPayload(payload);
    } catch (error) {
      handleRuntimeError(error);
    } finally {
      busy = false;
    }
  }

  async function handleNumberSubmit(value, input) {
    if (busy) return;
    clearError();

    if (value.trim() === "") {
      showError("Bestie needs a number.");
      input.focus();
      return;
    }

    busy = true;

    try {
      const payload = JSON.parse(submitValuePy(value));

      if (payload.error) {
        showError(payload.error);
        renderNumberInput(payload.input);
        return;
      }

      clearInteraction();
      addMessage(value, "player");
      await renderPayload(payload);
    } catch (error) {
      handleRuntimeError(error);
    } finally {
      busy = false;
    }
  }

  async function restartGame() {
    if (busy || !restartGamePy) return;
    busy = true;

    chatLog.replaceChildren();
    clearInteraction();

    try {
      const payload = JSON.parse(restartGamePy());
      await renderPayload(payload);
    } catch (error) {
      handleRuntimeError(error);
    } finally {
      busy = false;
    }
  }

  function handleRuntimeError(error) {
    console.error(error);
    runtimeStatus.textContent = "runtime error";
    runtimeLed.classList.remove("ready");
    runtimeLed.classList.add("error");
    loadOverlay.classList.remove("hidden");
    loadOverlay.classList.add("error");
    loadTitle.textContent = "bestie.exe crashed :(";

    const detail = document.createElement("span");
    detail.textContent = "Check the browser console, then reload the page.";
    loadOverlay.appendChild(detail);
  }

  async function initGame() {
    updateClock();
    setInterval(updateClock, 30_000);

    try {
      runtimeStatus.textContent = "loading python...";
      loadTitle.textContent = "loading bestie.exe...";

      pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX });

      runtimeStatus.textContent = "loading story...";
      loadTitle.textContent = "loading your questionable decisions...";

      const response = await fetch("./romantic_risk_assessment.py", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Could not load romantic_risk_assessment.py (${response.status})`);
      }

      const pythonSource = await response.text();
      await pyodide.runPythonAsync(pythonSource);

      startGamePy = pyodide.globals.get("start_game");
      choosePy = pyodide.globals.get("choose");
      submitValuePy = pyodide.globals.get("submit_value");
      restartGamePy = pyodide.globals.get("restart_game");

      runtimeStatus.textContent = "bestie.exe online";
      runtimeLed.classList.add("ready");

      const payload = JSON.parse(startGamePy());

      loadOverlay.classList.add("hidden");
      await delay(120);
      await renderPayload(payload);
    } catch (error) {
      handleRuntimeError(error);
    }
  }

  restartButton.addEventListener("click", restartGame);

  window.addEventListener("beforeunload", () => {
    [startGamePy, choosePy, submitValuePy, restartGamePy].forEach((proxy) => {
      if (proxy && typeof proxy.destroy === "function") proxy.destroy();
    });
  });

  initGame();
})();
