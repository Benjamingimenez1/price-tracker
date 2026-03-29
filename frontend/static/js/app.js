// ── CONFIG ────────────────────────────────────────────────
const API = "";  // same origin; change to "http://localhost:8000" for dev with separate servers

// ── STATE ─────────────────────────────────────────────────
let token     = localStorage.getItem("pt_token") || null;
let username  = localStorage.getItem("pt_username") || "";
let products  = [];
let chart     = null;
let selectedId = null;

// ── BOOT ──────────────────────────────────────────────────
(async () => {
  if (token) {
    showApp();
    await loadProducts();
  }
})();

// ── AUTH SCREEN ───────────────────────────────────────────
function switchTab(tab) {
  document.getElementById("tab-login").style.display    = tab === "login"    ? "block" : "none";
  document.getElementById("tab-register").style.display = tab === "register" ? "block" : "none";
  document.querySelectorAll(".auth-tab").forEach((el, i) => {
    el.classList.toggle("active", (i === 0) === (tab === "login"));
  });
}

async function doLogin() {
  const email    = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errEl    = document.getElementById("login-error");
  errEl.textContent = "";

  if (!email || !password) { errEl.textContent = "Completá todos los campos"; return; }

  setAuthLoading("login-spinner", true);
  const res = await apiFetch("/api/auth/login", "POST", { email, password }, false);
  setAuthLoading("login-spinner", false);

  if (res.error) { errEl.textContent = res.detail || res.error; return; }

  saveAuth(res.token, res.username);
  showApp();
  await loadProducts();
}

async function doRegister() {
  const email    = document.getElementById("reg-email").value.trim();
  const username = document.getElementById("reg-username").value.trim();
  const password = document.getElementById("reg-password").value;
  const errEl    = document.getElementById("reg-error");
  errEl.textContent = "";

  if (!email || !username || !password) { errEl.textContent = "Completá todos los campos"; return; }
  if (password.length < 6) { errEl.textContent = "La contraseña debe tener al menos 6 caracteres"; return; }

  setAuthLoading("reg-spinner", true);
  const res = await apiFetch("/api/auth/register", "POST", { email, username, password }, false);
  setAuthLoading("reg-spinner", false);

  if (res.error) { errEl.textContent = res.detail || res.error; return; }

  saveAuth(res.token, res.username);
  showApp();
  await loadProducts();
}

function logout() {
  localStorage.removeItem("pt_token");
  localStorage.removeItem("pt_username");
  token = null; username = ""; products = []; selectedId = null;
  document.getElementById("app").style.display = "none";
  document.getElementById("auth-screen").style.display = "flex";
}

function saveAuth(t, u) {
  token = t; username = u;
  localStorage.setItem("pt_token", t);
  localStorage.setItem("pt_username", u);
}

function showApp() {
  document.getElementById("auth-screen").style.display = "none";
  document.getElementById("app").style.display = "block";
  document.getElementById("username-label").textContent = username || "";
}

function setAuthLoading(spinnerId, on) {
  document.getElementById(spinnerId).style.display = on ? "inline-block" : "none";
}

// ── PRODUCTS ──────────────────────────────────────────────
async function loadProducts() {
  const data = await apiFetch("/api/products", "GET");
  if (data.error) { toast("Error al cargar productos", "error"); return; }
  products = data;
  if (!selectedId && products.length) selectedId = products[0].id;
  render();
}

async function addProduct() {
  const urlInput   = document.getElementById("url-input");
  const nameInput  = document.getElementById("name-input");
  const alertInput = document.getElementById("alert-input");
  const urlWrap    = document.getElementById("url-wrap");
  const btn        = document.getElementById("track-btn");
  const spinner    = document.getElementById("track-spinner");

  const url = urlInput.value.trim();
  if (!url.startsWith("http")) {
    urlWrap.classList.add("has-error");
    urlInput.classList.add("error");
    return;
  }
  urlWrap.classList.remove("has-error");
  urlInput.classList.remove("error");

  const alertPrice = parseFloat(alertInput.value) || null;
  const name       = nameInput.value.trim() || null;

  btn.disabled = true;
  spinner.style.display = "inline-block";
  btn.querySelector(".btn-text").textContent = "SCRAPING...";
  toast("Obteniendo precio real... puede tardar unos segundos ⚡", "alert");

  const res = await apiFetch("/api/products", "POST", { url, name, alert_price: alertPrice });

  btn.disabled = false;
  spinner.style.display = "none";
  btn.querySelector(".btn-text").textContent = "TRACK";

  if (res.error) {
    toast("Error: " + (res.detail || res.error), "error");
    return;
  }

  if (!res.scraped) {
    toast(`"${res.name}" agregado (scraping falló: ${res.scrape_error})`, "alert");
  } else {
    toast(`"${res.name}" → $${fmt(res.current_price)} (vía ${res.scrape_method})`, "success");
  }

  urlInput.value = ""; nameInput.value = ""; alertInput.value = "";

  if (!selectedId) selectedId = res.id;
  await loadProducts();
}

async function deleteProduct(id) {
  const res = await apiFetch(`/api/products/${id}`, "DELETE");
  if (res.error) { toast("Error al eliminar", "error"); return; }
  if (selectedId === id) selectedId = products.find(p => p.id !== id)?.id || null;
  toast("Producto eliminado", "error");
  await loadProducts();
}

async function refreshProduct(id) {
  const btn = document.getElementById(`refresh-btn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "..."; }

  const res = await apiFetch(`/api/products/${id}/refresh`, "POST");

  if (btn) { btn.disabled = false; btn.textContent = "↻"; }

  if (res.error) { toast("Error al actualizar", "error"); return; }

  if (res.success) {
    const change = res.change;
    const sign   = change < 0 ? "▼" : "▲";
    const type   = change < 0 ? "success" : "error";
    if (change !== null && change !== undefined) {
      toast(`Actualizado: ${sign} $${Math.abs(change).toFixed(0)} (${res.change_pct > 0 ? "+" : ""}${res.change_pct}%)`, type);
    } else {
      toast("Precio actualizado", "success");
    }
    if (res.alert_triggered) {
      toast("🔔 ¡ALERTA DE PRECIO ACTIVADA!", "alert");
    }
  } else {
    toast("No se pudo actualizar: " + res.error, "error");
  }
  await loadProducts();
}

async function refreshAll() {
  toast("Actualizando todos los productos...", "alert");
  for (const p of products) {
    await apiFetch(`/api/products/${p.id}/refresh`, "POST");
  }
  await loadProducts();
  toast("Todos los productos actualizados ✓", "success");
}

// ── CHART ─────────────────────────────────────────────────
function selectProduct(id) {
  selectedId = id;
  document.querySelectorAll(".chart-pill").forEach(p => {
    p.classList.toggle("active", parseInt(p.dataset.id) === id);
  });
  renderChart();
}

// ── RENDER ────────────────────────────────────────────────
function render() {
  renderStats();
  renderTable();
  renderChartPills();
  renderChart();
}

function renderStats() {
  const grid = document.getElementById("stats-grid");
  if (!products.length) { grid.style.display = "none"; return; }
  grid.style.display = "grid";

  document.getElementById("stat-count").textContent = products.length;

  // Best drop
  let bestPct = null;
  let totalSavings = 0;
  let lastUpdated = null;

  products.forEach(p => {
    const s = p.stats;
    if (!s || !s.total_change_pct) return;
    if (bestPct === null || s.total_change_pct < bestPct) bestPct = s.total_change_pct;
    totalSavings += (s.total_savings || 0);
    if (p.last_checked) {
      const d = new Date(p.last_checked);
      if (!lastUpdated || d > lastUpdated) lastUpdated = d;
    }
  });

  const bestEl = document.getElementById("stat-best");
  if (bestPct !== null && bestPct < 0) {
    bestEl.textContent = bestPct.toFixed(1) + "%";
    bestEl.className = "value green";
  } else if (bestPct !== null) {
    bestEl.textContent = "+" + bestPct.toFixed(1) + "%";
    bestEl.className = "value red";
  } else {
    bestEl.textContent = "—";
    bestEl.className = "value";
  }

  document.getElementById("stat-savings").textContent = "$" + fmt(totalSavings);
  document.getElementById("stat-updated").textContent = lastUpdated
    ? lastUpdated.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
    : "—";
}

function renderTable() {
  const empty = document.getElementById("empty-state");
  const table = document.getElementById("products-table");
  const badge = document.getElementById("count-badge");
  const body  = document.getElementById("table-body");

  badge.textContent = products.length + " producto" + (products.length !== 1 ? "s" : "");

  if (!products.length) {
    empty.style.display = "block";
    table.style.display = "none";
    return;
  }
  empty.style.display = "none";
  table.style.display = "table";

  body.innerHTML = products.map(p => {
    const s = p.stats || {};
    const change    = s.total_change;
    const changePct = s.total_change_pct;
    const price     = p.current_price;

    let changeTxt = "—", changeClass = "change-none";
    if (change !== undefined && change !== null) {
      const arrow = change < 0 ? "▼ " : "▲ ";
      changeTxt   = `${arrow}$${fmt(Math.abs(change))} (${changePct > 0 ? "+" : ""}${changePct}%)`;
      changeClass = change < 0 ? "change-down" : "change-up";
    }

    let alertHtml = '<span style="color:var(--muted);font-size:12px;">—</span>';
    if (p.alert_price) {
      const triggered = price !== null && price <= p.alert_price;
      alertHtml = `<span class="alert-badge${triggered ? " alert-triggered" : ""}">$${fmt(p.alert_price)}</span>`;
    }

    return `
      <tr class="product-row">
        <td>
          <div class="product-name" title="${esc(p.name)}">${esc(p.name)}</div>
          <a class="product-url" href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.url)}</a>
        </td>
        <td class="price-cell">${price !== null ? "$" + fmt(price) : '<span style="color:var(--muted)">—</span>'}</td>
        <td class="${changeClass}">${changeTxt}</td>
        <td style="font-family:var(--mono);font-size:13px;color:var(--accent);">
          ${s.min_price !== undefined ? "$" + fmt(s.min_price) : "—"}
        </td>
        <td>${alertHtml}</td>
        <td>
          <button class="refresh-btn" id="refresh-btn-${p.id}" onclick="refreshProduct(${p.id})">↻</button>
        </td>
        <td>
          <button class="del-btn" onclick="deleteProduct(${p.id})">✕</button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderChartPills() {
  const ctrl = document.getElementById("chart-controls");
  ctrl.innerHTML = products.map(p =>
    `<div class="chart-pill${p.id === selectedId ? " active" : ""}" data-id="${p.id}" onclick="selectProduct(${p.id})">${esc(p.name)}</div>`
  ).join("");
}

async function renderChart() {
  const canvas = document.getElementById("chart");
  const noData = document.getElementById("no-data-chart");

  const p = products.find(x => x.id === selectedId);
  if (!p) {
    canvas.style.display = "none";
    noData.style.display = "flex";
    if (chart) { chart.destroy(); chart = null; }
    return;
  }

  // Fetch real history from API
  const history = await apiFetch(`/api/products/${p.id}/history`, "GET");
  if (!history || history.error || !history.length) {
    canvas.style.display = "none";
    noData.style.display = "flex";
    if (chart) { chart.destroy(); chart = null; }
    return;
  }

  canvas.style.display = "block";
  noData.style.display = "none";

  const labels = history.map(h => {
    const d = new Date(h.recorded_at);
    return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit" }) +
           " " + d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
  });
  const data   = history.map(h => h.price);
  const first  = data[0];
  const last   = data[data.length - 1];
  const lineColor = last <= first ? "#00e5a0" : "#ff4757";
  const fillColor = last <= first ? "rgba(0,229,160,.07)" : "rgba(255,71,87,.07)";

  if (chart) chart.destroy();

  chart = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: p.name,
        data,
        borderColor:         lineColor,
        backgroundColor:     fillColor,
        borderWidth:         2,
        pointBackgroundColor: lineColor,
        pointBorderColor:    lineColor,
        pointRadius:         history.length > 30 ? 2 : 4,
        pointHoverRadius:    6,
        fill: true,
        tension: 0.35,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0d1520",
          borderColor:     "#1e2f45",
          borderWidth: 1,
          titleColor: "#c8daf0",
          bodyColor:  "#c8daf0",
          callbacks: {
            label: ctx => " $" + fmt(ctx.raw),
          },
        },
      },
      scales: {
        x: {
          grid:  { color: "rgba(30,47,69,.5)" },
          ticks: { color: "#4a6080", font: { family: "'Space Mono'", size: 10 }, maxTicksLimit: 8 },
        },
        y: {
          grid:  { color: "rgba(30,47,69,.5)" },
          ticks: {
            color: "#4a6080",
            font:  { family: "'Space Mono'", size: 10 },
            callback: v => "$" + fmt(v),
          },
        },
      },
    },
  });
}

// ── API HELPER ────────────────────────────────────────────
async function apiFetch(path, method = "GET", body = null, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && token) headers["Authorization"] = "Bearer " + token;

  try {
    const res = await fetch(API + path, {
      method,
      headers,
      ...(body ? { body: JSON.stringify(body) } : {}),
    });

    if (res.status === 401) { logout(); return { error: "No autorizado" }; }

    const data = await res.json();
    if (!res.ok) return { error: true, detail: data.detail || "Error del servidor" };
    return data;

  } catch (e) {
    console.error("API error:", e);
    document.getElementById("api-status").textContent = "API ERROR";
    document.getElementById("api-status").style.color = "var(--danger)";
    return { error: true, detail: "No se pudo conectar con el servidor" };
  }
}

// ── TOAST ─────────────────────────────────────────────────
function toast(msg, type = "success") {
  const icons = { success: "✓", error: "✕", alert: "🔔" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── UTILS ─────────────────────────────────────────────────
function fmt(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("es-AR", { maximumFractionDigits: 0 });
}

function esc(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
