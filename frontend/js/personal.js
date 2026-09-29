/* ============================================================
   personal.js — Personal Tier Calculator
   Rwanda Cost-of-Living Navigator
   ============================================================
   This file powers everything on personal.html:

   - Reads the user's spending inputs from the form
   - Sends them to the backend API
   - Displays the personal inflation rate and breakdown
   - Shows what changed this month
   - Loads budgeting tips
   - Compares to profile groups
   - Shows the forecast
   - Handles AI advice (Level 1) and questions (Level 2)
   - Generates the WhatsApp share message

   All results are stored in this variable so the
   WhatsApp share and AI advice can access them:
   ============================================================ */

// Stores the last calculated result
// so other functions can access it
let lastResult = null;


/* ============================================================
   1. READ FORM — collect what the user typed
   ============================================================ */

/**
 * Read all spending values from the form.
 * Returns an object matching the HouseholdSpending model
 * in our backend models.py
 */
function readForm() {
  return {
    monthly_income  : parseFloat(document.getElementById("monthly_income").value)  || 0,
    food            : parseFloat(document.getElementById("food").value)            || 0,
    housing         : parseFloat(document.getElementById("housing").value)         || 0,
    transport       : parseFloat(document.getElementById("transport").value)       || 0,
    health          : parseFloat(document.getElementById("health").value)          || 0,
    education       : parseFloat(document.getElementById("education").value)       || 0,
    clothing        : parseFloat(document.getElementById("clothing").value)        || 0,
    communication   : parseFloat(document.getElementById("communication").value)   || 0,
    furnishing      : parseFloat(document.getElementById("furnishing").value)      || 0,
    recreation      : parseFloat(document.getElementById("recreation").value)      || 0,
    restaurants     : parseFloat(document.getElementById("restaurants").value)     || 0,
    miscellaneous   : parseFloat(document.getElementById("miscellaneous").value)   || 0,
    alcohol_tobacco : parseFloat(document.getElementById("alcohol_tobacco").value) || 0,
    district        : document.getElementById("district").value   || null,
    area_type       : document.getElementById("area_type").value  || null,
    language        : getCurrentLanguage(),
  };
}


/* ============================================================
   2. VALIDATE FORM — check inputs before sending
   ============================================================ */

/**
 * Check that the user entered at least one spending amount.
 * Returns true if valid, false if not.
 */
function validateForm(spending) {

  const spendingFields = [
    "food", "housing", "transport", "health",
    "education", "clothing", "communication",
    "furnishing", "recreation", "restaurants",
    "miscellaneous", "alcohol_tobacco"
  ];

  const totalSpend = spendingFields.reduce(
    (sum, field) => sum + (spending[field] || 0), 0
  );

  const errorEl = document.getElementById("form-error");

  if (totalSpend === 0) {
    errorEl.textContent =
      "Please enter at least one spending amount to calculate your inflation rate.";
    errorEl.style.display = "block";
    return false;
  }

  errorEl.style.display = "none";
  return true;
}


/* ============================================================
   3. MAIN CALCULATION — called when user clicks Calculate
   ============================================================ */

async function calculateInflation() {

  // Read and validate the form
  const spending = readForm();
  if (!validateForm(spending)) return;

  // Disable the button to prevent double-clicking
  const btn = document.getElementById("calculate-btn");
  btn.disabled   = true;
  btn.textContent = "Calculating...";

  // Show the results section with a loading state
  const resultsSection = document.getElementById("results-section");
  resultsSection.style.display = "block";
  showLoading("headline-result", "Calculating your personal inflation rate...");

  try {

    // ── Call the backend API ────────────────────────────────
    const result = await apiCall(
      "/api/personal/inflation", "POST", spending
    );

    if (!result) {
      showError("headline-result",
        "Could not connect to the server. " +
        "Please check your internet connection and try again."
      );
      return;
    }

    // Save result for WhatsApp and AI functions
    lastResult = result;

    // ── Display all sections ────────────────────────────────
    displayHeadlineResult(result);
    displayPressureSpotlight(result);
    displayCategoryBreakdown(result);

    // Load additional data in parallel
    await Promise.all([
      loadWhatChanged(),
      loadBudgetingTips(spending),
      loadProfileComparison(spending),
      loadForecast(),
    ]);

    // Scroll to results smoothly
    resultsSection.scrollIntoView({ behavior: "smooth" });

  } finally {
    // Re-enable the button
    btn.disabled    = false;
    btn.textContent = getCurrentLanguage() === "rw"
      ? "Bara inflation yanjye"
      : "Calculate my inflation rate";
  }
}


/* ============================================================
   4. DISPLAY HEADLINE RESULT
   ============================================================ */

function displayHeadlineResult(result) {

  const diff      = result.difference_from_national;
  const diffSign  = diff >= 0 ? "+" : "";
  const diffClass = diff > 2 ? "danger" : diff > 0 ? "warning" : "success";
  const lang      = getCurrentLanguage();

  document.getElementById("headline-result").innerHTML = `

    <div class="metrics-grid">
      ${buildMetricCard(
        lang === "rw" ? "Inflation yawe" : "Your personal inflation",
        formatPct(result.personal_inflation_rate),
        lang === "rw" ? "Kanama 2026" : "August 2026",
        "danger"
      )}
      ${buildMetricCard(
        lang === "rw" ? "Uburinganire bw'igihugu" : "National average",
        formatPct(result.national_average),
        "NISR",
        "blue"
      )}
      ${buildMetricCard(
        lang === "rw" ? "Itandukaniro" : "Difference",
        diffSign + formatPct(diff),
        diff > 0
          ? (lang === "rw" ? "Hejuru y'igihugu" : "Above national")
          : (lang === "rw" ? "Munsi y'igihugu" : "Below national"),
        diffClass
      )}
    </div>

    <div style="background:#FFF3E0; border-left:4px solid #F5A623;
                padding:1rem; border-radius:0 8px 8px 0;
                margin-top:1rem;">
      <p style="font-size:0.875rem; color:#1A1A2E;">
        💰 ${lang === "rw"
          ? `Inflation iramarira <strong>${formatRWF(result.monthly_extra_cost)}</strong> buri kwezi — ni <strong>${formatRWF(result.annual_extra_cost)}</strong> ku mwaka, ku bintu bimwe bimwe uko byari kera.`
          : `Inflation is costing you an extra <strong>${formatRWF(result.monthly_extra_cost)}</strong> per month — that is <strong>${formatRWF(result.annual_extra_cost)}</strong> per year, for exactly the same spending.`
        }
      </p>
    </div>
  `;
}


/* ============================================================
   5. DISPLAY PRESSURE SPOTLIGHT
   ============================================================ */

function displayPressureSpotlight(result) {

  const lang = getCurrentLanguage();
  const top  = result.breakdown[0];

  if (!top) return;

  document.getElementById("pressure-spotlight").innerHTML = `
    <div style="background:#FDECEA; border:1px solid #D93025;
                border-radius:8px; padding:1rem;">
      <p style="font-size:0.875rem; font-weight:700;
                color:#D93025; margin-bottom:0.5rem;">
        ⚠ ${lang === "rw" ? "Ikibazo kinini" : "Biggest pressure this month"}:
        ${top.category_name}
      </p>
      <p style="font-size:0.875rem; color:#1A1A2E;">
        ${lang === "rw"
          ? `<strong>${top.category_name}</strong> ifata <strong>${formatPct(top.share_pct)}</strong> y'ingengo y'imari yawe kandi yiyongereje <strong>${formatPct(top.yoy_inflation)}</strong> uyu mwaka — birakwiriye <strong>${formatRWF(top.monthly_extra)}</strong> menshi buri kwezi.`
          : `<strong>${top.category_name}</strong> takes <strong>${formatPct(top.share_pct)}</strong> of your budget and rose <strong>${formatPct(top.yoy_inflation)}</strong> this year — that is <strong>${formatRWF(top.monthly_extra)}</strong> extra every month for the same thing.`
        }
      </p>
    </div>
  `;
}


/* ============================================================
   6. DISPLAY CATEGORY BREAKDOWN
   ============================================================ */

function displayCategoryBreakdown(result) {

  const maxContribution = Math.max(
    ...result.breakdown.map(b => b.contribution)
  );

  let html = "";

  result.breakdown.forEach(item => {
    const cssClass = getRiskClass(item.trend);
    const pct      = (item.contribution / maxContribution) * 100;

    html += `
      <div style="margin-bottom:0.75rem;">
        <div style="display:flex; justify-content:space-between;
                    align-items:center; margin-bottom:0.25rem;">
          <span style="font-size:0.875rem; font-weight:600;">
            ${item.category_name}
          </span>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            ${buildBadge(item.trend, item.trend.toLowerCase())}
            <span style="font-size:0.75rem; color:#6B7280;">
              +${formatPct(item.yoy_inflation)} YoY
            </span>
          </div>
        </div>
        ${buildProgressBar(
          formatPct(item.share_pct) + " of budget",
          pct, 100, cssClass
        )}
        <p style="font-size:0.75rem; color:#6B7280; margin-top:0.25rem;">
          Contributes ${formatPct(item.contribution)} to your personal rate
          · Extra cost: ${formatRWF(item.monthly_extra)}/month
        </p>
      </div>
    `;
  });

  document.getElementById("category-breakdown").innerHTML = html;
}


/* ============================================================
   7. LOAD WHAT CHANGED THIS MONTH
   ============================================================ */

async function loadWhatChanged() {

  showLoading("what-changed-content", "Loading...");

  const data = await apiCall("/api/personal/what-changed");

  if (!data) {
    showError("what-changed-content",
      "Could not load monthly changes."
    );
    return;
  }

  const lang = getCurrentLanguage();

  const buildList = (items, colorClass, emoji) => {
    if (items.length === 0) return "<p style='font-size:0.875rem; color:#6B7280;'>None</p>";
    return items.map(item => `
      <div style="display:flex; justify-content:space-between;
                  padding:0.375rem 0; border-bottom:1px solid #F3F4F6;">
        <span style="font-size:0.875rem;">${item.category_name}</span>
        <span style="font-size:0.875rem; font-weight:600;
                     color:var(--color-${colorClass});">
          ${formatChange(item.mom_pct)} this month
        </span>
      </div>
    `).join("");
  };

  document.getElementById("what-changed-content").innerHTML = `
    <div style="display:grid;
                grid-template-columns:repeat(auto-fit, minmax(200px,1fr));
                gap:1rem;">

      <div style="background:#FDECEA; border-radius:8px; padding:1rem;">
        <p style="font-weight:700; color:#D93025; margin-bottom:0.5rem;">
          🔴 ${lang === "rw" ? "Biriyongera" : "Rising"}
        </p>
        ${buildList(data.rising, "danger", "🔴")}
      </div>

      <div style="background:#FFF3E0; border-radius:8px; padding:1rem;">
        <p style="font-weight:700; color:#F5A623; margin-bottom:0.5rem;">
          🟡 ${lang === "rw" ? "Biringanye" : "Stable"}
        </p>
        ${buildList(data.stable, "warning", "🟡")}
      </div>

      <div style="background:#E6F7ED; border-radius:8px; padding:1rem;">
        <p style="font-weight:700; color:#20B257; margin-bottom:0.5rem;">
          🟢 ${lang === "rw" ? "Biragabanuka" : "Falling"}
        </p>
        ${buildList(data.falling, "success", "🟢")}
      </div>

    </div>
    <p style="font-size:0.75rem; color:#6B7280; margin-top:0.75rem;
              font-style:italic;">
      Based on month-on-month change — August vs July 2026.
      Source: NISR CPI.
    </p>
  `;
}


/* ============================================================
   8. LOAD BUDGETING TIPS
   ============================================================ */

async function loadBudgetingTips(spending) {

  showLoading("budgeting-tips", "Loading tips...");

  const data = await apiCall(
    "/api/personal/tips", "POST", spending
  );

  if (!data || data.length === 0) {
    showError("budgeting-tips", "Could not load tips.");
    return;
  }

  const lang = getCurrentLanguage();
  let html   = "";

  data.forEach((tip, index) => {
    html += `
      <div style="border-left:4px solid var(--color-blue);
                  padding:1rem; margin-bottom:1rem;
                  background:#F8F9FA; border-radius:0 8px 8px 0;">

        <p style="font-weight:700; color:#0066CC;
                  margin-bottom:0.5rem; font-size:0.875rem;">
          #${index + 1} — ${tip.category.toUpperCase()}
        </p>

        <p style="font-size:0.875rem; margin-bottom:0.75rem;">
          💡 <strong>${lang === "rw" ? "Inama" : "Tip"}:</strong>
          ${tip.tip}
        </p>

        <p style="font-size:0.875rem; margin-bottom:0.75rem;">
          📋 <strong>${lang === "rw" ? "Inshingano" : "Challenge"}:</strong>
          ${tip.challenge}
        </p>

        <p style="font-size:0.875rem; margin-bottom:0.75rem;">
          💰 <strong>${lang === "rw" ? "Amafaranga" : "Saving"}:</strong>
          ${tip.saving_tip}
        </p>

        <p style="font-size:0.875rem; color:#6B7280;">
          🇷🇼 <strong>${lang === "rw" ? "mu Rwanda" : "Locally"}:</strong>
          ${tip.local_tip}
        </p>

      </div>
    `;
  });

  document.getElementById("budgeting-tips").innerHTML = html;
}


/* ============================================================
   9. LOAD PROFILE COMPARISON
   ============================================================ */

async function loadProfileComparison(spending) {

  showLoading("profile-comparison", "Comparing...");

  const data = await apiCall(
    "/api/personal/compare", "POST", spending
  );

  if (!data || data.length === 0) {
    showError("profile-comparison",
      "Could not load profile comparison."
    );
    return;
  }

  const lang = getCurrentLanguage();
  let html   = "";

  data.forEach(profile => {
    const cssClass = profile.direction === "above"
      ? "danger" : "success";
    const arrow    = profile.direction === "above" ? "↑" : "↓";

    html += `
      <div style="display:flex; justify-content:space-between;
                  align-items:center; padding:0.75rem 0;
                  border-bottom:1px solid #F3F4F6;">
        <span style="font-size:0.875rem; color:#1A1A2E;">
          ${profile.profile_name}
        </span>
        <div style="text-align:right;">
          <span style="font-size:0.875rem; font-weight:600;">
            ${formatPct(profile.profile_inflation)}
          </span>
          <span style="font-size:0.75rem; margin-left:0.5rem;
                       color:var(--color-${cssClass});">
            ${arrow} You are ${formatPct(profile.difference)}
            ${profile.direction}
          </span>
        </div>
      </div>
    `;
  });

  document.getElementById("profile-comparison").innerHTML = `
    <div style="margin-bottom:0.75rem; padding:0.75rem;
                background:#E6F0FF; border-radius:8px;">
      <p style="font-size:0.875rem; font-weight:700;
                color:#0066CC;">
        ${lang === "rw" ? "Inflation yawe" : "Your rate"}:
        ${formatPct(lastResult?.personal_inflation_rate || 0)}
      </p>
    </div>
    ${html}
    <p style="font-size:0.75rem; color:#6B7280; margin-top:0.75rem;
              font-style:italic;">
      Profiles derived from NISR EICV7 2023-2024 household
      spending patterns.
    </p>
  `;
}


/* ============================================================
   10. LOAD FORECAST
   ============================================================ */

async function loadForecast() {

  showLoading("forecast-content", "Loading forecast...");

  const data = await apiCall("/api/business/forecast");

  if (!data) {
    showError("forecast-content",
      "Could not load forecast."
    );
    return;
  }

  const lang     = getCurrentLanguage();
  const forecasts = data.forecasts || [];

  // Show only top 5 categories by current inflation
  const top5 = forecasts.slice(0, 5);

  let html = `
    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse;
                    font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:2px solid #E0E0E0;">
            <th style="text-align:left; padding:0.5rem;
                       color:#6B7280; font-weight:600;">
              ${lang === "rw" ? "Icyiciro" : "Category"}
            </th>
            <th style="text-align:right; padding:0.5rem;
                       color:#6B7280; font-weight:600;">
              ${lang === "rw" ? "Ubu" : "Now"}
            </th>
            <th style="text-align:right; padding:0.5rem;
                       color:#6B7280; font-weight:600;">
              Sep
            </th>
            <th style="text-align:right; padding:0.5rem;
                       color:#6B7280; font-weight:600;">
              ${lang === "rw" ? "Ingingo" : "Trend"}
            </th>
          </tr>
        </thead>
        <tbody>
  `;

  top5.forEach(f => {
    const trendClass = getRiskClass(f.trend);
    const trendEmoji = getRiskEmoji(f.trend);

    html += `
      <tr style="border-bottom:1px solid #F3F4F6;">
        <td style="padding:0.5rem;">
          ${f.category_name.replace("v     ", "").trim()}
        </td>
        <td style="padding:0.5rem; text-align:right;
                   font-weight:600;
                   color:var(--color-${trendClass});">
          ${formatPct(f.current_yoy)}
        </td>
        <td style="padding:0.5rem; text-align:right;
                   color:#6B7280;">
          ${formatChange(f.forecast_month_1)}/mo
        </td>
        <td style="padding:0.5rem; text-align:right;">
          ${trendEmoji} ${f.trend}
        </td>
      </tr>
    `;
  });

  html += `
        </tbody>
      </table>
    </div>
  `;

  document.getElementById("forecast-content").innerHTML = html;
}


/* ============================================================
   11. AI ADVICE — Level 1
   ============================================================ */

async function getAIAdvice() {

  if (!lastResult) return;

  const btn = document.getElementById("ai-btn");
  btn.disabled    = true;
  btn.textContent = "Getting AI advice...";

  showLoading("ai-advice-content", "Claude AI is thinking...");

  const top = lastResult.breakdown[0];

  const requestBody = {
    personal_inflation_rate : lastResult.personal_inflation_rate,
    national_average        : lastResult.national_average,
    biggest_pressure        : lastResult.biggest_pressure,
    biggest_pressure_yoy    : top ? top.yoy_inflation : 0,
    biggest_pressure_share  : top ? top.share_pct : 0,
    monthly_extra_cost      : lastResult.monthly_extra_cost,
    district                : document.getElementById("district").value || null,
    area_type               : document.getElementById("area_type").value || null,
    language                : getCurrentLanguage(),
  };

  const data = await apiCall("/api/ai/advice", "POST", requestBody);

  if (!data) {
    showError("ai-advice-content",
      "AI service temporarily unavailable. " +
      "Please try again in a moment."
    );
  } else {
    document.getElementById("ai-advice-content").innerHTML = `
      <div style="background:#E6F0FF; border-radius:8px;
                  padding:1rem; border-left:4px solid #0066CC;">
        <p style="font-size:0.875rem; line-height:1.7;
                  color:#1A1A2E;">
          ${data.advice}
        </p>
        <p style="font-size:0.75rem; color:#6B7280;
                  margin-top:0.75rem; font-style:italic;">
          ${data.disclaimer}
        </p>
      </div>
    `;
  }

  btn.disabled    = false;
  btn.textContent = getCurrentLanguage() === "rw"
    ? "🤖 Bona inama z'AI"
    : "🤖 Get personalized AI advice";
}


/* ============================================================
   12. ASK A QUESTION — Level 2
   ============================================================ */

async function askQuestion() {

  const question = document.getElementById("user-question").value.trim();

  if (!question || question.length < 5) {
    showError("question-answer",
      "Please type a question of at least 5 characters."
    );
    return;
  }

  const btn       = document.getElementById("question-btn");
  btn.disabled    = true;
  btn.textContent = "Thinking...";

  showLoading("question-answer", "Claude AI is answering...");

  const requestBody = {
    question                : question,
    personal_inflation_rate : lastResult?.personal_inflation_rate || null,
    biggest_pressure        : lastResult?.biggest_pressure || null,
    district                : document.getElementById("district").value || null,
    language                : getCurrentLanguage(),
  };

  const data = await apiCall(
    "/api/ai/question", "POST", requestBody
  );

  if (!data) {
    showError("question-answer",
      "AI service temporarily unavailable."
    );
  } else {
    document.getElementById("question-answer").innerHTML = `
      <div style="background:#F8F9FA; border-radius:8px;
                  padding:1rem; border-left:4px solid #20B257;">
        <p style="font-size:0.75rem; color:#6B7280;
                  margin-bottom:0.5rem;">
          Q: ${data.question}
        </p>
        <p style="font-size:0.875rem; line-height:1.7;
                  color:#1A1A2E;">
          ${data.answer}
        </p>
        <p style="font-size:0.75rem; color:#6B7280;
                  margin-top:0.5rem; font-style:italic;">
          ${data.disclaimer}
        </p>
      </div>
    `;
  }

  btn.disabled    = false;
  btn.textContent = getCurrentLanguage() === "rw"
    ? "💬 Baza ikibazo"
    : "💬 Ask a question";
}


/* ============================================================
   13. WHATSAPP SHARE
   ============================================================ */

function handleShare() {
  if (!lastResult) return;

  shareOnWhatsApp(
    lastResult.personal_inflation_rate,
    lastResult.national_average,
    lastResult.biggest_pressure,
    lastResult.monthly_extra_cost
  );
}


/* ============================================================
   14. INITIALIZE
   ============================================================ */
document.addEventListener("DOMContentLoaded", function() {
  // Page is ready — user can start entering their spending
  console.log("Personal calculator ready");
});
