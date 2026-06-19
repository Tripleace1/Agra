// Agra frontend — vanilla JS, no framework, keeps RAM low.
const state = {
  lang: localStorage.getItem("agra.lang") || "en",
  history: [],
  i18n: {},
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

async function loadI18n(lang) {
  try {
    const r = await fetch(`/static/i18n/${lang}.json`);
    state.i18n = await r.json();
  } catch (e) {
    console.warn("i18n load failed", e);
    state.i18n = {};
  }
  applyI18n();
}

function t(key, fallback = "") {
  return state.i18n[key] || fallback || key;
}

function applyI18n() {
  $$("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const v = state.i18n[key];
    if (v) el.textContent = v;
  });
  $$("[data-i18n-attr]").forEach(el => {
    const raw = el.getAttribute("data-i18n-attr");
    const [attr, key] = raw.split("|");
    const v = state.i18n[key];
    if (v && attr) el.setAttribute(attr, v);
  });
  document.documentElement.setAttribute("lang", state.lang);
}

// Routing
function showView(name) {
  $$(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
  if (name === "ledger") refreshBatches();
}

$$(".nav-btn").forEach(b => b.addEventListener("click", () => showView(b.dataset.view)));

// Language toggle
$$(".lang-btn").forEach(b => b.addEventListener("click", async () => {
  $$(".lang-btn").forEach(x => x.classList.toggle("active", x === b));
  state.lang = b.dataset.lang;
  localStorage.setItem("agra.lang", state.lang);
  await loadI18n(state.lang);
}));

// Health
async function refreshHealth() {
  try {
    const r = await fetch("/api/health");
    const j = await r.json();
    const el = $("#model-status");
    if (!j.model_present) { el.textContent = "Missing"; el.className = "badge bad"; return; }
    if (j.model_loaded) { el.textContent = "Loaded"; el.className = "badge ok"; }
    else { el.textContent = "Ready"; el.className = "badge warn"; }
  } catch {
    $("#model-status").textContent = "—";
  }
}

// Soil — real-time validation
// Realistic field ranges for agricultural soil tests (mg/kg, except pH).
const SOIL_RANGES = {
  ph: { min: 0, max: 14, typical: [3.5, 9.0],
        msg: { en: "pH outside realistic field range",
               yo: "pH ko si ni iwon ile gidi" } },
  n:  { min: 0, max: 500, typical: [0, 200],
        msg: { en: "Unusually high N — re-check the test",
               yo: "N po ju — wo idanwo naa lekansi" } },
  p:  { min: 0, max: 300, typical: [0, 150],
        msg: { en: "Unusually high P — re-check the test",
               yo: "P po ju — wo idanwo naa lekansi" } },
  k:  { min: 0, max: 600, typical: [0, 400],
        msg: { en: "Unusually high K — re-check the test",
               yo: "K po ju — wo idanwo naa lekansi" } },
};

function ensureHint(input) {
  let hint = input.parentElement.querySelector(".field-hint");
  if (!hint) {
    hint = document.createElement("small");
    hint.className = "field-hint";
    input.parentElement.appendChild(hint);
  }
  return hint;
}

function validateField(input) {
  const name = input.name;
  const cfg = SOIL_RANGES[name];
  if (!cfg) return true;
  const v = parseFloat(input.value);
  const hint = ensureHint(input);

  if (Number.isNaN(v)) {
    input.classList.remove("invalid", "warning", "valid");
    hint.textContent = "";
    hint.className = "field-hint";
    return false;
  }
  if (v < cfg.min || v > cfg.max) {
    input.classList.add("invalid");
    input.classList.remove("warning", "valid");
    hint.textContent = `${cfg.msg[state.lang] || cfg.msg.en} (${cfg.min}–${cfg.max})`;
    hint.className = "field-hint error";
    return false;
  }
  if (v < cfg.typical[0] || v > cfg.typical[1]) {
    input.classList.add("warning");
    input.classList.remove("invalid", "valid");
    hint.textContent = `${cfg.msg[state.lang] || cfg.msg.en} (typical ${cfg.typical[0]}–${cfg.typical[1]})`;
    hint.className = "field-hint warn";
    return true;
  }
  input.classList.add("valid");
  input.classList.remove("invalid", "warning");
  hint.textContent = "";
  hint.className = "field-hint";
  return true;
}

const soilForm = $("#soil-form");
["ph", "n", "p", "k"].forEach(n => {
  const el = soilForm.querySelector(`[name="${n}"]`);
  if (el) {
    el.addEventListener("input", () => validateField(el));
    el.addEventListener("blur", () => validateField(el));
  }
});

soilForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);

  // Run all validators; block submit on hard errors only (warnings allowed).
  let hardFail = false;
  ["ph", "n", "p", "k"].forEach(n => {
    const el = soilForm.querySelector(`[name="${n}"]`);
    validateField(el);
    if (el.classList.contains("invalid")) hardFail = true;
  });
  if (hardFail) {
    $("#soil-results").innerHTML =
      `<p class="muted error-msg">Fix the highlighted inputs first.</p>`;
    return;
  }

  const payload = {
    soil_type: fd.get("soil_type"),
    ph: parseFloat(fd.get("ph")),
    n: parseFloat(fd.get("n")),
    p: parseFloat(fd.get("p")),
    k: parseFloat(fd.get("k")),
    summarize: fd.get("summarize") === "on",
    lang: state.lang,
  };
  const out = $("#soil-results");
  out.innerHTML = `<p class="muted"><span class="spinner"></span>${t("chat.thinking", "Working…")}</p>`;
  try {
    const r = await fetch("/api/soil/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "diagnose failed");
    renderSoil(j);
  } catch (err) {
    out.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
});

function renderSoil(j) {
  const out = $("#soil-results");
  const top = j.crops.slice(0, 6);
  const cropHtml = top.map(c => {
    const cls = c.suitability.toLowerCase();
    const name = state.lang === "yo" ? c.name_yo : c.name;
    return `
      <div class="crop-row">
        <span class="crop-name">${name}</span>
        <span class="pill ${cls}">${c.suitability}</span>
        <span class="muted">${c.score}</span>
        <div class="reasons">${c.reasons.join(" · ")}</div>
      </div>`;
  }).join("");
  const corrHtml = `<div class="corrections">
    <strong>${t("soil.results.corrections", "Nutrient Corrections")}</strong>
    <ul>${j.corrections.map(c => `<li>${c}</li>`).join("")}</ul>
  </div>`;
  const sumHtml = j.summary
    ? `<div class="summary"><strong>${t("soil.results.summary", "AI Summary")}:</strong> ${j.summary}</div>`
    : "";
  out.innerHTML = cropHtml + corrHtml + sumHtml;
}

// Chat — streams tokens via /api/chat/stream, then fetches sources via /api/chat
$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chat-prompt");
  const prompt = input.value.trim();
  if (!prompt) return;
  input.value = "";
  appendMsg("user", prompt);
  const placeholder = appendMsg("assistant", `<span class="spinner"></span>${t("chat.thinking", "Thinking…")}`);

  const historySnapshot = state.history.slice();
  let answer = "";
  let firstTok = true;

  try {
    const r = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, lang: state.lang, history: historySnapshot }),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      throw new Error(j.error || `stream failed (${r.status})`);
    }
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (firstTok) { placeholder.innerHTML = ""; firstTok = false; }
      answer += chunk;
      placeholder.innerHTML = escapeHtml(answer).replace(/\n/g, "<br>") +
        '<span class="caret">▍</span>';
      $("#chat-log").scrollTop = $("#chat-log").scrollHeight;
    }

    state.history.push({ role: "user", content: prompt });
    state.history.push({ role: "assistant", content: answer });

    // Pull sources separately — cheap FTS5 hit, no LLM cost.
    let srcHtml = "";
    try {
      const sr = await fetch("/api/chat/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, lang: state.lang }),
      });
      if (sr.ok) {
        const sj = await sr.json();
        if (sj.sources && sj.sources.length) {
          const tags = sj.sources.map(s => `<span class="tag">${escapeHtml(s.title)}</span>`).join("");
          srcHtml = `<div class="sources">${t("chat.sources", "Sources")}: ${tags}</div>`;
        }
      }
    } catch {}
    placeholder.innerHTML = escapeHtml(answer).replace(/\n/g, "<br>") + srcHtml;
  } catch (err) {
    placeholder.innerHTML = `<span style="color:var(--danger)">${err.message}</span>`;
  }
});

function appendMsg(role, html) {
  const log = $("#chat-log");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = html;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Ledger
$("#trace-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd.entries());
  payload.weight_kg = parseFloat(payload.weight_kg);
  const result = $("#trace-result");
  result.innerHTML = `<p class="muted"><span class="spinner"></span>...</p>`;
  try {
    const r = await fetch("/api/trace/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "register failed");
    result.innerHTML = `<div class="trace-result">${t("ledger.registered", "Batch registered. Trace ID:")} <span class="trace-id">${j.trace_id}</span></div>`;
    e.target.reset();
    refreshBatches();
  } catch (err) {
    result.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
});

$("#trace-search-btn").addEventListener("click", refreshBatches);
$("#trace-search").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); refreshBatches(); }
});

async function refreshBatches() {
  const q = $("#trace-search").value.trim();
  const list = $("#trace-list");
  list.innerHTML = `<p class="muted"><span class="spinner"></span>...</p>`;
  try {
    const r = await fetch(`/api/trace/list?q=${encodeURIComponent(q)}`);
    const j = await r.json();
    if (!j.batches.length) {
      list.innerHTML = `<div class="empty-state">${t("ledger.list.empty", "No batches yet.")}</div>`;
      return;
    }
    const rows = j.batches.map(b => `
      <tr>
        <td class="trace-id">${b.trace_id}</td>
        <td>${escapeHtml(b.farmer_name)}</td>
        <td>${escapeHtml(b.crop_type)}</td>
        <td>${b.weight_kg} kg</td>
        <td>${b.quality_grade}</td>
        <td>${b.harvest_date}</td>
      </tr>`).join("");
    list.innerHTML = `<table class="batches">
      <thead><tr>
        <th>${t("ledger.list.id", "Trace ID")}</th>
        <th>${t("ledger.list.farmer", "Farmer")}</th>
        <th>${t("ledger.list.crop", "Crop")}</th>
        <th>${t("ledger.list.weight", "Weight")}</th>
        <th>${t("ledger.list.grade", "Grade")}</th>
        <th>${t("ledger.list.date", "Date")}</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  } catch (err) {
    list.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
}

// Boot
(async () => {
  // Set initial lang button state
  $$(".lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === state.lang));
  await loadI18n(state.lang);
  refreshHealth();
  setInterval(refreshHealth, 8000);
})();
