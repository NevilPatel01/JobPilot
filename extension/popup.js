const DEFAULTS = {
  apiUrl: "http://localhost:8000",
  appUrl: "http://localhost:3000",
  apiToken: ""
};

const state = { settings: { ...DEFAULTS }, capture: null, result: null };
const $ = (id) => document.getElementById(id);

const categoryLabel = (value) => ({
  it_support: "IT Support",
  cloud_junior_devops: "Cloud / DevOps",
  fullstack_web: "Full-stack / Web",
  app_support_analyst: "Application Support",
  automation_scada: "Automation / SCADA"
}[value] || value || "Reviewing");

function showNotice(message) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}

function setBusy(busy) {
  $("save-inbox").disabled = busy;
  $("save-applied").disabled = busy;
  $("save-inbox").textContent = busy ? "Saving…" : "Save to Inbox";
}

function applyCapture(data, fallbackUrl = "") {
  state.capture = data;
  $("title").value = data.title || "";
  $("company").value = data.company || "";
  $("location").value = data.location || "";
  $("description").value = data.description || "";
  $("page-url").value = data.url || fallbackUrl;
  $("manual-url").value = data.url || fallbackUrl;
  $("selected-text").value = data.selected_text || "";
  $("source-site").textContent = (data.source_site || "current page").replaceAll("_", " ");
}

async function loadSettings() {
  state.settings = { ...DEFAULTS, ...(await chrome.storage.sync.get(DEFAULTS)) };
  $("api-url").value = state.settings.apiUrl;
  $("app-url").value = state.settings.appUrl;
  $("api-token").value = state.settings.apiToken;
}

async function saveSettings() {
  state.settings = {
    apiUrl: $("api-url").value.trim().replace(/\/$/, "") || DEFAULTS.apiUrl,
    appUrl: $("app-url").value.trim().replace(/\/$/, "") || DEFAULTS.appUrl,
    apiToken: $("api-token").value.trim()
  };
  await chrome.storage.sync.set(state.settings);
  $("settings").hidden = true;
  showNotice(state.settings.apiToken ? "Connection saved." : "Add an API token before capturing jobs.");
}

async function extractFromTab(tabId) {
  let response;
  try {
    response = await chrome.tabs.sendMessage(tabId, { type: "JOBPILOT_EXTRACT" });
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
    response = await chrome.tabs.sendMessage(tabId, { type: "JOBPILOT_EXTRACT" });
  }
  if (!response?.ok) throw new Error(response?.error || "Could not read this page.");
  return response.data;
}

async function extractCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("http")) {
    throw new Error("Open a job listing in a regular browser tab first.");
  }
  applyCapture(await extractFromTab(tab.id), tab.url);
}

function waitForTab(tabId) {
  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("The job page took too long to load."));
    }, 20000);
    const listener = (updatedId, changeInfo) => {
      if (updatedId !== tabId || changeInfo.status !== "complete") return;
      window.clearTimeout(timeout);
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    };
    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function loadPastedUrl() {
  const rawUrl = $("manual-url").value.trim();
  let url;
  try {
    url = new URL(rawUrl);
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error();
  } catch {
    showNotice("Enter a complete job URL beginning with https://");
    return;
  }

  const button = $("load-url");
  button.disabled = true;
  button.textContent = "Loading…";
  showNotice("Opening the listing briefly to extract its details…");
  let tab;
  try {
    tab = await chrome.tabs.create({ url: url.href, active: false });
    await waitForTab(tab.id);
    applyCapture(await extractFromTab(tab.id), url.href);
    showNotice("Listing loaded. Review the details, then save it.");
  } catch (error) {
    showNotice(error instanceof Error ? error.message : "Could not load this job URL.");
  } finally {
    if (tab?.id) await chrome.tabs.remove(tab.id).catch(() => {});
    button.disabled = false;
    button.textContent = "Load URL";
  }
}

async function api(path, options = {}) {
  if (!state.settings.apiToken) throw new Error("Open connection settings and add a JobPilot API token.");
  const response = await fetch(`${state.settings.apiUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": state.settings.apiToken,
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 404 && path.startsWith("/api/v1/extension/")) {
    throw new Error("Capture API not found. Deploy the latest JobPilot backend, then try again.");
  }
  if (!response.ok) throw new Error(payload.detail || `JobPilot returned ${response.status}`);
  return payload;
}

function capturePayload(action) {
  return {
    title: $("title").value.trim(),
    company: $("company").value.trim(),
    location: $("location").value.trim() || null,
    description: $("description").value.trim(),
    selected_text: $("selected-text").value,
    url: $("page-url").value,
    source_site: state.capture?.source_site || "generic",
    job_type: state.capture?.job_type || null,
    salary_min: state.capture?.salary_min || null,
    salary_max: state.capture?.salary_max || null,
    currency: state.capture?.currency || "CAD",
    action
  };
}

function showResult(result) {
  state.result = result;
  $("capture-form").hidden = true;
  $("result").hidden = false;
  $("result-title").textContent = result.duplicate ? "Already in JobPilot" : result.status === "applied" ? "Saved and tracked" : "Saved to Inbox";
  $("result-message").textContent = result.message;
  $("fit-score").textContent = result.fit_score == null ? "Pending" : `${result.fit_score} · ${result.fit_label}`;
  $("resume-category").textContent = categoryLabel(result.recommended_category);
  $("mark-applied").hidden = result.status === "applied";
}

async function submitCapture(event) {
  event.preventDefault();
  const action = event.submitter?.dataset.action || "inbox";
  showNotice("");
  setBusy(true);
  try {
    showResult(await api("/api/v1/extension/capture", { method: "POST", body: JSON.stringify(capturePayload(action)) }));
  } catch (error) {
    showNotice(error instanceof Error ? error.message : "Capture failed.");
  } finally {
    setBusy(false);
  }
}

async function updateStatus(action) {
  if (!state.result?.inbox_job_id) return;
  try {
    const result = await api(`/api/v1/extension/inbox/${state.result.inbox_job_id}`, {
      method: "PATCH",
      body: JSON.stringify({ action })
    });
    showResult(result);
  } catch (error) {
    showNotice(error instanceof Error ? error.message : "Update failed.");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadSettings();
  const commands = await chrome.commands.getAll();
  const captureCommand = commands.find((command) => command.name === "_execute_action");
  $("shortcut").textContent = captureCommand?.shortcut || "";
  $("settings-toggle").addEventListener("click", () => { $("settings").hidden = !$("settings").hidden; });
  $("save-settings").addEventListener("click", saveSettings);
  $("open-setup").addEventListener("click", () => chrome.tabs.create({ url: `${state.settings.appUrl}/extension` }));
  $("capture-form").addEventListener("submit", submitCapture);
  $("load-url").addEventListener("click", loadPastedUrl);
  $("manual-url").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      loadPastedUrl();
    }
  });
  $("open-inbox").addEventListener("click", () => chrome.tabs.create({ url: `${state.settings.appUrl}/inbox` }));
  $("mark-applied").addEventListener("click", () => updateStatus("applied"));
  $("archive").addEventListener("click", () => updateStatus("archived"));
  try {
    await extractCurrentPage();
    if (!state.settings.apiToken) {
      $("settings").hidden = false;
      showNotice("Add an API token once, then capture jobs from any supported listing page.");
    }
  } catch (error) {
    showNotice(error instanceof Error ? error.message : "Could not inspect this tab.");
  }
});
