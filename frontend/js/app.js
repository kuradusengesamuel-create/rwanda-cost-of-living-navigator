/* ============================================================
   app.js - Rwanda Cost-of-Living Navigator
   Main JavaScript file - shared utilities and landing page
   ============================================================ */

const CONFIG = {
  BACKEND_URL: "http://localhost:8000",
  TIMEOUT_MS: 10000,
  DATA_MONTH: "August 2026",
};

/* ============================================================
   API HELPER
   ============================================================ */
async function apiCall(endpoint, method, body) {
  method = method || "GET";
  var url = CONFIG.BACKEND_URL + endpoint;
  var options = {
    method: method,
    headers: { "Content-Type": "application/json" },
  };
  if (body && method === "POST") {
    options.body = JSON.stringify(body);
  }
  try {
    var response = await fetch(url, options);
    if (!response.ok) {
      console.error("API error: " + response.status + " on " + endpoint);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error("Network error on " + endpoint + ":", error);
    return null;
  }
}

/* ============================================================
   FORMAT HELPERS
   ============================================================ */
function formatRWF(amount) {
  return "RWF " + Math.round(amount).toLocaleString("en-RW");
}

function formatPct(value) {
  return parseFloat(value).toFixed(1) + "%";
}

function formatChange(value) {
  var rounded = parseFloat(value).toFixed(1);
  return (value >= 0 ? "+" : "") + rounded + "%";
}

function getRiskClass(level) {
  var map = {
    High: "danger",
    Medium: "warning",
    Lower: "success",
    Rising: "danger",
    Stable: "warning",
    Falling: "success",
  };
  return map[level] || "blue";
}

function getRiskEmoji(level) {
  var map = {
    High: "🔴",
    Medium: "🟡",
    Lower: "🟢",
    Rising: "🔴",
    Stable: "🟡",
    Falling: "🟢",
  };
  return map[level] || "⚪";
}

/* ============================================================
   UI HELPERS
   ============================================================ */
function buildProgressBar(label, value, maxValue, cssClass) {
  var pct = Math.min((value / maxValue) * 100, 100);
  var display = typeof value === "number" ? formatPct(value) : value;
  return (
    '<div class="progress-bar">' +
    '<span class="progress-label">' +
    label +
    "</span>" +
    '<div class="progress-track">' +
    '<div class="progress-fill ' +
    cssClass +
    '" style="width:' +
    pct +
    '%"></div>' +
    "</div>" +
    '<span class="progress-value">' +
    display +
    "</span>" +
    "</div>"
  );
}

function buildMetricCard(label, value, subtext, cssClass) {
  return (
    '<div class="metric-card">' +
    '<div class="metric-label">' +
    label +
    "</div>" +
    '<div class="metric-value ' +
    cssClass +
    '">' +
    value +
    "</div>" +
    (subtext ? '<div class="metric-sub">' + subtext + "</div>" : "") +
    "</div>"
  );
}

function buildBadge(text, level) {
  var cssClass = "badge-" + level.toLowerCase();
  return '<span class="badge ' + cssClass + '">' + text + "</span>";
}

function showLoading(elementId, message) {
  message = message || "Loading...";
  var el = document.getElementById(elementId);
  if (el) {
    el.innerHTML =
      '<div class="loading"><div class="spinner"></div><span>' +
      message +
      "</span></div>";
  }
}

function showError(elementId, message) {
  var el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = '<div class="error-msg">⚠ ' + message + "</div>";
  }
}

/* ============================================================
   WHATSAPP SHARE
   ============================================================ */
function shareOnWhatsApp(
  personalRate,
  nationalRate,
  biggestPressure,
  monthlyExtra,
) {
  var lang = getCurrentLanguage();
  var message = "";
  if (lang === "rw") {
    message =
      "🇷🇼 *Rwanda Cost-of-Living Navigator*\n\n" +
      "📊 Izamuka ry'ibiciro ryanjye: *" +
      formatPct(personalRate) +
      "*\n" +
      "🇷🇼 Igihugu: " +
      formatPct(nationalRate) +
      "\n" +
      "⚠ Ikibazo kinini: " +
      biggestPressure +
      "\n" +
      "💰 Amafaranga menshi: " +
      formatRWF(monthlyExtra) +
      "/ukwezi\n\n" +
      "Koresha igikoresho: rwanda-clnp.vercel.app\n" +
      "_Amakuru: NISR " +
      CONFIG.DATA_MONTH +
      "_";
  } else {
    message =
      "🇷🇼 *Rwanda Cost-of-Living Navigator*\n\n" +
      "📊 My personal inflation: *" +
      formatPct(personalRate) +
      "*\n" +
      "🇷🇼 National average: " +
      formatPct(nationalRate) +
      "\n" +
      "⚠ Biggest pressure: " +
      biggestPressure +
      "\n" +
      "💰 Extra cost: " +
      formatRWF(monthlyExtra) +
      "/month\n\n" +
      "Try it: rwanda-clnp.vercel.app\n" +
      "_Data: NISR " +
      CONFIG.DATA_MONTH +
      "_";
  }
  var encoded = encodeURIComponent(message);
  window.open("https://wa.me/?text=" + encoded, "_blank");
}

/* ============================================================
   LANDING PAGE - load live data into alert bar
   ============================================================ */
async function loadLandingPageData() {
  var data = await apiCall("/api/personal/what-changed");
  if (!data) {
    console.log("Backend offline - using static inflation figures");
    return;
  }
  try {
    var allCategories = data.rising.concat(data.stable).concat(data.falling);
    var findCat = function (keyword) {
      return allCategories.find(function (c) {
        return (
          c.category_name.toLowerCase().indexOf(keyword.toLowerCase()) !== -1
        );
      });
    };
    var food = findCat("Food");
    var transport = findCat("Transport");
    var housing = findCat("Housing");
    var health = findCat("Health");
    if (food) {
      var elF = document.getElementById("alert-food");
      if (elF)
        elF.innerHTML =
          "🥗 Food: <strong>" + formatChange(food.yoy_pct) + "</strong>";
    }
    if (transport) {
      var elT = document.getElementById("alert-transport");
      if (elT)
        elT.innerHTML =
          "🚌 Transport: <strong>" +
          formatChange(transport.yoy_pct) +
          "</strong>";
    }
    if (housing) {
      var elH = document.getElementById("alert-housing");
      if (elH)
        elH.innerHTML =
          "🏠 Housing: <strong>" + formatChange(housing.yoy_pct) + "</strong>";
    }
    if (health) {
      var elHe = document.getElementById("alert-health");
      if (elHe)
        elHe.innerHTML =
          "💊 Health: <strong>" + formatChange(health.yoy_pct) + "</strong>";
    }
  } catch (error) {
    console.log("Could not update alert bar:", error);
  }
}

/* ============================================================
   INITIALIZE
   ============================================================ */
document.addEventListener("DOMContentLoaded", function () {
  loadLandingPageData();
  console.log("Rwanda Cost-of-Living Navigator loaded - " + CONFIG.DATA_MONTH);
});
