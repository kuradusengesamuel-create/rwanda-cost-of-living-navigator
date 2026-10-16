/* ============================================================
   government.js — Government Tier Dashboard
   Rwanda Cost-of-Living Navigator
   ============================================================
   Loads and displays all Government tier data:
   - National summary
   - Early warning flags
   - District pressure index with filters
   - Income group vulnerability
   - District detail view
   - CSV export
   ============================================================ */

// Store full district data for filtering and export
let allDistricts = [];


/* ============================================================
   1. LOAD NATIONAL SUMMARY
   ============================================================ */

async function loadNationalSummary() {

  const data = await apiCall("/api/government/summary");

  if (!data) {
    showError("national-summary-content",
      "Could not load national summary."
    );
    return;
  }

  const lang = getCurrentLanguage();

  document.getElementById("national-summary-content").innerHTML = `

    <div class="metrics-grid" style="margin-bottom:1rem;">
      ${buildMetricCard(
        lang === "rw"
          ? "Inflation rusange"
          : "National inflation",
        formatPct(data.national_inflation),
        data.data_month,
        "danger"
      )}
      ${buildMetricCard(
        lang === "rw"
          ? "Uturere tw'ibibazo binini"
          : "High risk areas",
        data.districts_at_high_risk + " of 60",
        "district-area combinations",
        "danger"
      )}
      ${buildMetricCard(
        lang === "rw"
          ? "Uturere tw'ibibazo bibiri"
          : "Medium risk areas",
        data.districts_at_medium_risk + " of 60",
        "district-area combinations",
        "warning"
      )}
    </div>

    <div style="display:grid;
                grid-template-columns:1fr 1fr;
                gap:1rem; margin-bottom:1rem;">

      <div style="background:#FDECEA; border-radius:8px;
                  padding:1rem;">
        <p style="font-size:0.75rem; color:#6B7280;
                  margin-bottom:0.25rem;">
          ${lang === "rw"
            ? "Akarere k'ibibazo binini"
            : "Highest pressure district"}
        </p>
        <p style="font-size:1rem; font-weight:700;
                  color:#D93025;">
          ${data.highest_pressure_district?.district}
          ${data.highest_pressure_district?.area_type}
        </p>
        <p style="font-size:0.875rem; color:#D93025;">
          ${formatPct(
            data.highest_pressure_district?.pressure_index
          )}
        </p>
      </div>

      <div style="background:#E6F7ED; border-radius:8px;
                  padding:1rem;">
        <p style="font-size:0.75rem; color:#6B7280;
                  margin-bottom:0.25rem;">
          ${lang === "rw"
            ? "Akarere k'ibibazo bike"
            : "Lowest pressure district"}
        </p>
        <p style="font-size:1rem; font-weight:700;
                  color:#20B257;">
          ${data.lowest_pressure_district?.district}
          ${data.lowest_pressure_district?.area_type}
        </p>
        <p style="font-size:0.875rem; color:#20B257;">
          ${formatPct(
            data.lowest_pressure_district?.pressure_index
          )}
        </p>
      </div>

    </div>

    <div style="background:#F8F9FA; border-radius:8px;
                padding:1rem;">
      <p style="font-size:0.75rem; font-weight:600;
                color:#6B7280; margin-bottom:0.5rem;">
        ${lang === "rw"
          ? "Icyiciro cy'ibibazo kinini"
          : "Highest inflation category"}
      </p>
      <p style="font-size:0.875rem; color:#1A1A2E;">
        ${data.highest_inflation_category?.category} —
        <strong style="color:#D93025;">
          ${formatPct(
            data.highest_inflation_category?.yoy_pct
          )}
        </strong>
      </p>
      <p style="font-size:0.75rem; color:#6B7280;
                margin-top:0.25rem;">
        Most stable: ${data.lowest_inflation_category?.category} —
        ${formatPct(data.lowest_inflation_category?.yoy_pct)}
      </p>
    </div>
  `;
}


/* ============================================================
   2. LOAD EARLY WARNINGS
   ============================================================ */

async function loadEarlyWarnings() {

  const data = await apiCall("/api/government/early-warnings");

  if (!data) {
    showError("early-warnings-content",
      "Could not load early warnings."
    );
    return;
  }

  const lang = getCurrentLanguage();

  if (data.total_warnings === 0) {
    document.getElementById("early-warnings-content").innerHTML = `
      <div style="background:#E6F7ED; border-radius:8px;
                  padding:1rem; text-align:center;">
        <p style="color:#20B257; font-weight:600;">
          ✅ No critical thresholds crossed this month.
        </p>
      </div>
    `;
    return;
  }

  let html = `
    <p style="font-size:0.875rem; font-weight:600;
              color:#D93025; margin-bottom:1rem;">
      ⚠ ${data.total_warnings} active warning
      ${data.total_warnings > 1 ? "s" : ""}
    </p>
  `;

  data.warnings.forEach(warning => {
    html += `
      <div style="background:#FDECEA;
                  border:1px solid #D93025;
                  border-radius:8px; padding:1rem;
                  margin-bottom:0.75rem;">

        <div style="display:flex; justify-content:space-between;
                    align-items:flex-start;
                    margin-bottom:0.5rem;">
          <span style="font-size:0.75rem; font-weight:700;
                       color:#D93025; text-transform:uppercase;">
            ${warning.warning_type}
          </span>
          <span style="font-size:0.875rem; font-weight:700;
                       color:#D93025;">
            ${formatPct(warning.pressure_index)}
          </span>
        </div>

        <p style="font-size:0.875rem; color:#1A1A2E;
                  margin-bottom:0.5rem; line-height:1.6;">
          ${warning.message}
        </p>

        <p style="font-size:0.75rem; color:#6B7280;
                  font-style:italic;">
          💡 ${warning.recommended_action}
        </p>

      </div>
    `;
  });

  html += `
    <p style="font-size:0.75rem; color:#6B7280;
              font-style:italic; margin-top:0.5rem;">
      Thresholds: District ≥${data.thresholds.high_pressure_district}%,
      Food ≥${data.thresholds.food_alert}%,
      Transport ≥${data.thresholds.transport_alert}%
    </p>
  `;

  document.getElementById("early-warnings-content").innerHTML = html;
}


/* ============================================================
   3. LOAD DISTRICT INDEX
   ============================================================ */

async function loadDistrictIndex() {

  const data = await apiCall("/api/government/district-index");

  if (!data) {
    showError("district-index-content",
      "Could not load district data."
    );
    return;
  }

  // Store for filtering and export
  allDistricts = data.districts;

  displayDistricts(allDistricts);
}


/* ============================================================
   4. DISPLAY DISTRICTS — used by load and filter
   ============================================================ */

function displayDistricts(districts) {

  const lang = getCurrentLanguage();

  if (districts.length === 0) {
    document.getElementById("district-index-content").innerHTML = `
      <p style="color:#6B7280; font-size:0.875rem;">
        No districts match the selected filters.
      </p>
    `;
    return;
  }

  let html = `
    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse;
                    font-size:0.875rem;">
        <thead>
          <tr style="border-bottom:2px solid #E0E0E0;
                     background:#F8F9FA;">
            <th style="text-align:left; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              ${lang === "rw" ? "Akarere" : "District"}
            </th>
            <th style="text-align:left; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              ${lang === "rw" ? "Intera" : "Area"}
            </th>
            <th style="text-align:right; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              ${lang === "rw" ? "Indango" : "Index"}
            </th>
            <th style="text-align:center; padding:0.625rem;
                       font-weight:600; color:#6B7280;">
              ${lang === "rw" ? "Inyito" : "Risk"}
            </th>
          </tr>
        </thead>
        <tbody>
  `;

  districts.forEach(d => {
    const cssClass = getRiskClass(d.risk_level);
    const emoji    = getRiskEmoji(d.risk_level);

    html += `
      <tr style="border-bottom:1px solid #F3F4F6;
                 cursor:pointer;"
          onclick="quickViewDistrict('${d.district}')">
        <td style="padding:0.625rem; font-weight:500;">
          ${d.district}
        </td>
        <td style="padding:0.625rem; color:#6B7280;">
          ${d.area_type}
        </td>
        <td style="padding:0.625rem; text-align:right;
                   font-weight:700;
                   color:var(--color-${cssClass});">
          ${formatPct(d.pressure_index)}
        </td>
        <td style="padding:0.625rem; text-align:center;">
          ${buildBadge(
            emoji + " " + d.risk_level,
            d.risk_level.toLowerCase()
          )}
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
      Click any row to see the full category breakdown.
      Showing ${districts.length} of ${allDistricts.length}
      district-area combinations.
    </p>
  `;

  document.getElementById("district-index-content").innerHTML = html;
}


/* ============================================================
   5. FILTER DISTRICTS
   ============================================================ */

function filterDistricts() {

  const riskFilter = document.getElementById(
    "filter-risk"
  ).value;
  const areaFilter = document.getElementById(
    "filter-area"
  ).value;

  let filtered = allDistricts;

  if (riskFilter) {
    filtered = filtered.filter(
      d => d.risk_level === riskFilter
    );
  }

  if (areaFilter) {
    filtered = filtered.filter(
      d => d.area_type === areaFilter
    );
  }

  displayDistricts(filtered);
}


/* ============================================================
   6. QUICK VIEW DISTRICT — click on a row
   ============================================================ */

function quickViewDistrict(districtName) {
  // Set the district selector and load detail
  document.getElementById("detail-district").value =
    districtName;
  loadDistrictDetail();

  // Scroll to the detail section
  document.getElementById("district-detail-content")
    .scrollIntoView({ behavior: "smooth" });
}


/* ============================================================
   7. LOAD DISTRICT DETAIL
   ============================================================ */

async function loadDistrictDetail() {

  const district = document.getElementById(
    "detail-district"
  ).value;

  if (!district) return;

  showLoading("district-detail-content",
    `Loading ${district} detail...`
  );

  const data = await apiCall(
    `/api/government/district/${district}`
  );

  if (!data) {
    showError("district-detail-content",
      `Could not load data for ${district}.`
    );
    return;
  }

  const lang = getCurrentLanguage();
  let html   = "";

  data.breakdown.forEach(area => {
    const cssClass = getRiskClass(area.risk_level);

    html += `
      <div style="margin-bottom:1.5rem;">

        <div style="display:flex; justify-content:space-between;
                    align-items:center; margin-bottom:1rem;
                    padding:0.75rem;
                    background:var(--color-${cssClass}-light,#F8F9FA);
                    border-radius:8px;">
          <span style="font-weight:700; font-size:1rem;">
            ${data.district} — ${area.area_type}
          </span>
          <div style="text-align:right;">
            <span style="font-size:1.25rem; font-weight:700;
                         color:var(--color-${cssClass});">
              ${formatPct(area.pressure_index)}
            </span>
            <br/>
            ${buildBadge(area.risk_level,
              area.risk_level.toLowerCase())}
          </div>
        </div>

        <p style="font-size:0.75rem; color:#6B7280;
                  margin-bottom:0.75rem; font-style:italic;">
          ${area.note}
        </p>

    `;

    // Sort categories by contribution
    const cats = [...area.categories].sort(
      (a, b) => b.contribution - a.contribution
    );

    cats.forEach(cat => {
      const catClass = getRiskClass(
        cat.yoy_inflation > 20 ? "High"
        : cat.yoy_inflation > 10 ? "Medium" : "Lower"
      );

      html += buildProgressBar(
        cat.category_name.substring(0, 20),
        cat.basket_share_pct,
        60,
        catClass
      );

      html += `
        <p style="font-size:0.7rem; color:#9CA3AF;
                  margin-bottom:0.5rem; margin-left:0;">
          ${formatPct(cat.yoy_inflation)} inflation ·
          contributes ${formatPct(cat.contribution)}
          to district index
        </p>
      `;
    });

    html += `</div>`;
  });

  document.getElementById("district-detail-content").innerHTML =
    html;
}


/* ============================================================
   8. LOAD VULNERABILITY SCORES
   ============================================================ */

async function loadVulnerability() {

  const data = await apiCall("/api/government/vulnerability");

  if (!data) {
    showError("vulnerability-content",
      "Could not load vulnerability scores."
    );
    return;
  }

  const lang = getCurrentLanguage();
  let html   = `
    <p style="font-size:0.875rem; color:#6B7280;
              margin-bottom:1rem;">
      ${lang === "rw"
        ? "Ingando z'ubukungu Q1 ni izikennye cyane, Q5 ni iz'abakire cyane."
        : "Q1 = poorest 20% of households. Q5 = richest 20%."}
    </p>
  `;

  data.quintiles.forEach(q => {
    const cssClass = getRiskClass(q.vulnerability);

    html += `
      <div style="display:flex; align-items:center;
                  gap:1rem; padding:0.75rem 0;
                  border-bottom:1px solid #F3F4F6;">

        <div style="width:40px; height:40px;
                    background:var(--color-blue-light);
                    border-radius:50%;
                    display:flex; align-items:center;
                    justify-content:center;
                    font-weight:700; color:var(--color-blue);
                    flex-shrink:0; font-size:0.875rem;">
          ${q.quintile}
        </div>

        <div style="flex:1;">
          <p style="font-size:0.875rem; font-weight:600;
                    color:#1A1A2E;">
            ${q.label}
          </p>
          <p style="font-size:0.75rem; color:#6B7280;">
            ${q.household_count.toLocaleString()} households surveyed
          </p>
        </div>

        <div style="text-align:right;">
          <p style="font-size:1rem; font-weight:700;
                    color:var(--color-${cssClass});">
            ${formatPct(q.inflation_rate)}
          </p>
          ${buildBadge(
            q.vulnerability,
            q.vulnerability.toLowerCase()
          )}
        </div>

      </div>
    `;
  });

  html += `
    <div class="estimate-note" style="margin-top:1rem;">
      ${data.methodology_note}
    </div>
  `;

  document.getElementById("vulnerability-content").innerHTML =
    html;
}


/* ============================================================
   9. EXPORT TO CSV
   ============================================================ */

function exportToCSV() {

  if (allDistricts.length === 0) return;

  // Build CSV content
  const headers = [
    "District",
    "Area Type",
    "Pressure Index (%)",
    "Risk Level",
    "Household Count"
  ];

  const rows = allDistricts.map(d => [
    d.district,
    d.area_type,
    d.pressure_index,
    d.risk_level,
    d.household_count,
  ]);

  const csvContent = [
    "# Rwanda Cost-of-Living Navigator — District Pressure Index",
    "# Data: NISR CPI August 2026 + NISR EICV7 2023-2024",
    "# Note: Modelled estimates — not directly measured district CPI",
    "",
    headers.join(","),
    ...rows.map(row => row.join(",")),
  ].join("\n");

  // Create download link
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url  = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href     = url;
  link.download = "rwanda_clnp_district_pressure_index.csv";
  link.click();

  URL.revokeObjectURL(url);
}


/* ============================================================
   10. INITIALIZE — load all sections when page opens
   ============================================================ */
document.addEventListener("DOMContentLoaded", async function() {

  // Load all sections in parallel
  await Promise.all([
    loadNationalSummary(),
    loadEarlyWarnings(),
    loadDistrictIndex(),
    loadVulnerability(),
  ]);

  console.log("Government dashboard loaded");
});
