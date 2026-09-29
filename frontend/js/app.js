/* ============================================================
   app.js — Rwanda Cost-of-Living Navigator
   ============================================================
   This is the main JavaScript file for the landing page.

   What it does:
   - Connects to the backend API and loads live CPI data
   - Updates the inflation figures in the alert bar
   - Handles any general platform functionality
   - Provides shared helper functions used by all pages

   All API calls go through this file's helper functions
   so if the backend URL changes we only update it once.
   ============================================================ */


/* ============================================================
   1. API CONFIGURATION
   Change BACKEND_URL when deploying to production
   ============================================================ */
const CONFIG = {

  // Backend URL — change this when deployed to Render
  // During local development use: http://localhost:8000
  // After deployment use: https://your-app.onrender.com
  BACKEND_URL: "https://rwanda-clnp-api.onrender.com",

  // How long to wait for API response before showing error
  TIMEOUT_MS: 10000,

  // Data month — update when new CPI data is published
  DATA_MONTH: "August 2026",
};


/* ============================================================
   2. API HELPER — fetch data from the backend
   ============================================================ */

/**
 * Fetch data from the backend API.
 * Returns the JSON response or null if the request fails.
 * Never crashes the page — always handles errors gracefully.
 *
 * @param {string} endpoint - API path e.g. "/api/personal/what-changed"
 * @param {string} method   - HTTP method — "GET" or "POST"
 * @param {object} body     - Request body for POST requests
 */
async function apiCall(endpoint, method = "GET", body = null) {

  const url = CONFIG.BACKEND_URL + endpoint;

  const options = {
    method  : method,
    headers : {
      "Content-Type": "application/json",
    },
  };

  // Add body for POST requests
  if (body && method === "POST") {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);

    // Check if the request succeeded
    if (!response.ok) {
      console.error(
        `API error: ${response.status} on ${endpoint}`
      );
      return null;
    }

    return await response.json();

  } catch (error) {
    // Network error — backend may be offline or slow
    console.error(`Network error on ${endpoint}:`, error);
    return null;
  }
}


/* ============================================================
   3. FORMAT HELPERS — display numbers cleanly
   ============================================================ */

/**
 * Format a number as Rwanda Francs
 * Example: 26449 → "RWF 26,449"
 */
function formatRWF(amount) {
  return "RWF " + Math.round(amount).toLocaleString("en-RW");
}

/**
 * Format a percentage with one decimal place
 * Example: 16.657 → "16.7%"
 */
function formatPct(value) {
  return parseFloat(value).toFixed(1) + "%";
}

/**
 * Format a percentage change with + or - sign
 * Example: 2.5 → "+2.5%"  |  -0.8 → "-0.8%"
 */
function formatChange(value) {
  const rounded = parseFloat(value).toFixed(1);
  return (value >= 0 ? "+" : "") + rounded + "%";
}

/**
 * Get the CSS class for a risk level or trend
 * Used to color badges and values correctly
 */
function getRiskClass(level) {
  const map = {
    "High"    : "danger",
    "Medium"  : "warning",
    "Lower"   : "success",
    "Rising"  : "danger",
    "Stable"  : "warning",
    "Falling" : "success",
  };
  return map[level] || "blue";
}

/**
 * Get the emoji for a risk level or trend
 */
function getRiskEmoji(level) {
  const map = {
    "High"    : "🔴",
    "Medium"  : "🟡",
    "Lower"   : "🟢",
    "Rising"  : "🔴",
    "Stable"  : "🟡",
    "Falling" : "🟢",
  };
  return map[level] || "⚪";
}


/* ============================================================
   4. UI HELPERS — build common HTML components
   ============================================================ */

/**
 * Build a progress bar HTML string
 * Used in category breakdowns across all three tiers
 */
function buildProgressBar(label, value, maxValue, cssClass) {
  const pct     = Math.min((value / maxValue) * 100, 100);
  const display = typeof value === "number" ?
    formatPct(value) : value;

  return `
    <div class="progress-bar">
      <span class="progress-label">${label}</span>
      <div class="progress-track">
        <div class="progress-fill ${cssClass}"
             style="width: ${pct}%">
        </div>
      </div>
      <span class="progress-value">${display}</span>
    </div>
  `;
}

/**
 * Build a metric card HTML string
 * Used for big headline numbers
 */
function buildMetricCard(label, value, subtext, cssClass) {
  return `
    <div class="metric-card">
      <div class="metric-label">${label}</div>
      <div class="metric-value ${cssClass}">${value}</div>
      ${subtext
        ? `<div class="metric-sub">${subtext}</div>`
        : ""}
    </div>
  `;
}

/**
 * Build a status badge HTML string
 */
function buildBadge(text, level) {
  const cssClass = "badge-" + level.toLowerCase();
  return `<span class="badge ${cssClass}">${text}</span>`;
}

/**
 * Show a loading spinner inside an element
 */
function showLoading(elementId, message = "Loading...") {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <span>${message}</span>
      </div>
    `;
  }
}

/**
 * Show an error message inside an element
 */
function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = `
      <div class="error-msg">
        ⚠ ${message}
      </div>
    `;
  }
}


/* ============================================================
   5. WHATSAPP SHARE — generate share message
   ============================================================ */

/**
 * Generate and open a WhatsApp share message
 * with the user's inflation results
 */
function shareOnWhatsApp(personalRate, nationalRate,
                          biggestPressure, monthlyExtra) {

  const lang    = getCurrentLanguage();
  let message   = "";

  if (lang === "rw") {
    message = `🇷🇼 *Igikoresho cy'Ibiciro mu Rwanda*\n\n` +
      `📊 Inflation yanjye: *${formatPct(personalRate)}*\n` +
      `🇷🇼 Igihugu: ${formatPct(nationalRate)}\n` +
      `⚠ Ikibazo kinini: ${biggestPressure}\n` +
      `💰 Amafaranga menshi: ${formatRWF(monthlyExtra)}/ukwezi\n\n` +
      `Koresha igikoresho: rwanda-clnp.vercel.app\n` +
      `_Amakuru: NISR ${CONFIG.DATA_MONTH}_`;
  } else {
    message = `🇷🇼 *Rwanda Cost-of-Living Navigator*\n\n` +
      `📊 My personal inflation: *${formatPct(personalRate)}*\n` +
      `🇷🇼 National average: ${formatPct(nationalRate)}\n` +
      `⚠ Biggest pressure: ${biggestPressure}\n` +
      `💰 Extra cost: ${formatRWF(monthlyExtra)}/month\n\n` +
      `Try it: rwanda-clnp.vercel.app\n` +
      `_Data: NISR ${CONFIG.DATA_MONTH}_`;
  }

  const encoded = encodeURIComponent(message);
  window.open(`https://wa.me/?text=${encoded}`, "_blank");
}


/* ============================================================
   6. LANDING PAGE — load live data into the alert bar
   ============================================================ */

/**
 * Load the latest CPI figures and update the alert bar
 * with real numbers from the backend instead of hardcoded ones
 */
async function loadLandingPageData() {

  // Try to load what-changed data from the backend
  const data = await apiCall("/api/personal/what-changed");

  // If backend is offline, the hardcoded HTML values
