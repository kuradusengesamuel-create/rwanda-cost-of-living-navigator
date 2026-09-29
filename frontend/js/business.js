/* ============================================================
   business.js — Business Tier
   Rwanda Cost-of-Living Navigator
   ============================================================
   Loads and displays all Business tier data:
   - Cost pressure ranking
   - What changed this month
   - 3-month forecast
   - Wage review signal
   - WhatsApp share
   ============================================================ */

// Store data for WhatsApp share
let businessData = null;


/* ============================================================
   1. LOAD COST PRESSURE
   ============================================================ */

async function loadCostPressure() {

  const data = await apiCall("/api/business/cost-pressure");

  if (!data) {
    showError("cost-pressure-content",
      "Could not load cost data. " +
      "Please check your connection."
    );
    return;
  }

  businessData = data;
  const lang   = getCurrentLanguage();
  let html     = "";

  data.categories.forEach(cat => {
    const cssClass = getRiskClass(cat.pressure_level);

    html += `
      <div style="margin-bottom:1rem; padding-bottom:1rem;
                  border-bottom:1px solid #F3F4F6;">

        <div style="display:flex; justify-content:space-between;
                    align-items:center; margin-bottom:0.5rem;">
          <span style="font-size:0.875rem; font-weight:600;
                       color:#1A1A2E;">
            ${cat.category_name}
          </span>
          <div style="display:flex; gap:0.5rem;
                      align-items:center;">
            ${buildBadge(
              cat.pressure_level,
              cat.pressure_level.toLowerCase()
                .replace(" ", "-")
            )}
            ${buildBadge(cat.trend, cat.trend.toLowerCase())}
          </div>
        </div>

        ${buildProgressBar(
          formatPct(cat.yoy_pct) + " YoY",
          cat.yoy_pct, 35, cssClass
        )}

        <p style="font-size:0.75rem; color:#6B7280;
                  margin-top:0.25rem;">
          Month-on-month: ${formatChange(cat.mom_pct)} ·
          Weight in basket: ${formatPct(cat.weight_pct)}
        </p>

      </div>
    `;
  });

  document.getElementById("cost-pressure-content").innerHTML = `
    <p style="font-size:0.75rem; color:#6B7280;
              margin-bottom:1rem; font-style:italic;">
      Sorted by year-on-year pressure — highest first.
      Source: NISR CPI ${data.data_month}.
    </p>
    ${html}
  `;
}


/* ============================================================
   2. LOAD WHAT CHANGED — BUSINESS VIEW
   ============================================================ */

async function loadWhatChangedBusiness() {

  const data = await apiCall("/api/business/what-changed");

  if (!data) {
    showError("what-changed-business",
      "Could not load monthly changes."
    );
    return;
  }

  const lang = getCurrentLanguage();

  const buildList = (items) => {
    if (items.length === 0) {
      return `<p style="font-size:0.875rem;
                        color:#6B7280;">None</p>`;
    }
    return items.map(item => `
      <div style="display:flex; justify-content:space-between;
                  padding:0.375rem 0;
                  border-bottom:1px solid #F3F4F6;">
        <span style="font-size:0.875rem;">
          ${item.category_name}
        </span>
        <span style="font-size:0.875rem; font-weight:600;">
          ${formatChange(item.mom_pct)}
        </span>
      </div>
    `).join("");
  };

  document.getElementById("what-changed-business").innerHTML = `
    <div style="display:grid;
                grid-template-columns:repeat(auto-fit,
                minmax(200px,1fr)); gap:1rem;">

      <div style="background:#FDECEA; border-radius:8px;
                  padding:1rem;">
        <p style="font-weight:700; color:#D93025;
                  margin-bottom:0.5rem; font-size:0.875rem;">
          🔴 ${lang === "rw" ? "Biriyongera" : "Rising costs"}
        </p>
        ${buildList(data.rising)}
      </div>

      <div style="background:#FFF3E0; border-radius:8px;
                  padding:1rem;">
        <p style="font-weight:700; color:#F5A623;
                  margin-bottom:0.5rem; font-size:0.875rem;">
          🟡 ${lang === "rw" ? "Biringanye" : "Stable costs"}
        </p>
        ${buildList(data.stable)}
      </div>

      <div style="background:#E6F7ED; border-radius:8px;
                  padding:1rem;">
        <p style="font-weight:700; color:#20B257;
                  margin-bottom:0.5rem; font-size:0.875rem;">
          🟢 ${lang === "rw" ? "Biragabanuka" : "Falling costs"}
        </p>
        ${buildList(data.falling)}
      </div>

    </div>
  `;
}


/* ============================================================
   3. LOAD FORECAST
   ============================================================ */

async function loadForecastBusiness() {

  const data = await apiCall("/api/business/forecast");

  if (!data) {
    showError("forecast-business-content",
      "Could not load forecast."
    );
    return;
  }

  const lang     = getCurrentLanguage();
  const forecasts = data.forecasts || [];

  let html = `
    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse;
                    font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:2px solid #E0E0E0;
                     background:#F8F9FA;">
            <th style="text-align:left; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              Category
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              Now (YoY)
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              Sep
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              Oct
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              Nov
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              ±
            </th>
          </tr>
        </thead>
        <tbody>
  `;

  forecasts.forEach(f => {
    const cssClass = getRiskClass(f.trend);
    html += `
      <tr style="border-bottom:1px solid #F3F4F6;">
        <td style="padding:0.625rem; font-size:0.8rem;">
          ${f.category_name.replace("v     ", "").trim()}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   font-weight:600;
                   color:var(--color-${cssClass});">
          ${formatPct(f.current_yoy)}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   color:#6B7280; font-size:0.8rem;">
          ${formatChange(f.forecast_month_1)}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   color:#6B7280; font-size:0.8rem;">
          ${formatChange(f.forecast_month_2)}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   color:#6B7280; font-size:0.8rem;">
          ${formatChange(f.forecast_month_3)}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   color:#9CA3AF; font-size:0.75rem;">
          ±${f.confidence_range}%
        </td>
      </tr>
    `;
  });

  html += `
        </tbody>
      </table>
    </div>
    <p style="font-size:0.75rem; color:#6B7280;
              margin-top:0.75rem; font-style:italic;">
      Sep/Oct/Nov values show projected month-on-month change.
      ± shows the uncertainty range around each forecast.
    </p>
  `;

  document.getElementById(
    "forecast-business-content"
  ).innerHTML = html;
}


/* ============================================================
   4. LOAD WAGE SIGNAL
   ============================================================ */

async function loadWageSignal() {

  const data = await apiCall("/api/business/wage-signal");

  if (!data) {
    showError("wage-signal-content",
      "Could not load wage signal."
    );
    return;
  }

  const lang = getCurrentLanguage();

  document.getElementById("wage-signal-content").innerHTML = `

    <div class="metrics-grid" style="margin-bottom:1rem;">
      ${buildMetricCard(
        "Inflation since last year",
        formatPct(data.inflation_since),
        data.comparison_month + " → " + data.latest_month,
        "danger"
      )}
      ${buildMetricCard(
        "Purchasing power lost",
        formatPct(data.purchasing_power_loss),
        "Real value decline",
        "warning"
      )}
    </div>

    <div style="background:#FFF3E0; border-radius:8px;
                padding:1rem; border-left:4px solid #F5A623;
                margin-bottom:1rem;">
      <p style="font-size:0.875rem; color:#1A1A2E;
                line-height:1.7;">
        💼 ${data.wage_signal}
      </p>
    </div>

    <p style="font-size:0.75rem; color:#6B7280;
              font-style:italic;">
      ${data.note}
    </p>

    <div style="margin-top:1rem;">
      <label class="form-label">
        Compare from a specific month (YYYY-MM):
      </label>
      <div style="display:flex; gap:0.5rem; margin-top:0.5rem;">
        <input class="form-input" type="text"
               id="wage-month-input"
               placeholder="e.g. 2025-01"
               style="flex:1;" />
        <button class="btn btn-secondary"
                style="width:auto; padding:0.5rem 1rem;"
                onclick="loadCustomWageSignal()">
          Check
        </button>
      </div>
    </div>
  `;
}


/* ============================================================
   5. CUSTOM WAGE SIGNAL — user picks a month
   ============================================================ */

async function loadCustomWageSignal() {

  const month = document.getElementById(
    "wage-month-input"
  ).value.trim();

  if (!month) return;

  const data = await apiCall(
    `/api/business/wage-signal?since_month=${month}`
  );

  if (!data) {
    showError("wage-signal-content",
      `No data found for month: ${month}. ` +
      "Use format YYYY-MM e.g. 2025-01"
    );
    return;
  }

  // Update just the wage signal section
  document.querySelector(
    "#wage-signal-content .metrics-grid"
  ).innerHTML = `
    ${buildMetricCard(
      "Inflation since " + month,
      formatPct(data.inflation_since),
      month + " → " + data.latest_month,
      "danger"
    )}
    ${buildMetricCard(
      "Purchasing power lost",
      formatPct(data.purchasing_power_loss),
      "Real value decline",
      "warning"
    )}
  `;
}


/* ============================================================
   6. WHATSAPP SHARE — business summary
   ============================================================ */

function shareBusinessSummary() {

  if (!businessData) return;

  const lang    = getCurrentLanguage();
  const topCats = businessData.categories.slice(0, 3);

  let message = lang === "rw"
    ? `🇷🇼 *Ubucuruzi — Amakuru y'Ibiciro*\n\n`
    : `🇷🇼 *Rwanda Business Cost Summary*\n\n`;

  message += lang === "rw"
    ? `📊 Inflation rusange: *${formatPct(businessData.national_inflation)}*\n\n`
    : `📊 National inflation: *${formatPct(businessData.national_inflation)}*\n\n`;

  message += lang === "rw"
    ? `Ibibazo binini by'ibiciro:\n`
    : `Top cost pressures:\n`;

  topCats.forEach((cat, i) => {
    message += `${i + 1}. ${cat.category_name}: ` +
               `${formatPct(cat.yoy_pct)} ` +
               `(${cat.trend})\n`;
  });

  message += `\n${lang === "rw"
    ? "Reba byinshi: rwanda-clnp.vercel.app"
    : "Full analysis: rwanda-clnp.vercel.app"}`;

  message += `\n_${lang === "rw"
    ? "Amakuru"
    : "Data"}: NISR August 2026_`;

  const encoded = encodeURIComponent(message);
  window.open(`https://wa.me/?text=${encoded}`, "_blank");
}


/* ============================================================
   7. INITIALIZE — load all sections when page opens
   ============================================================ */
document.addEventListener("DOMContentLoaded", async function() {

  // Load all four sections in parallel for speed
  await Promise.all([
    loadCostPressure(),
    loadWhatChangedBusiness(),
    loadForecastBusiness(),
    loadWageSignal(),
  ]);

  console.log("Business tier loaded");
});
