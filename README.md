# Rwanda Cost-of-Living Navigator

*"NISR says inflation is 15.9%. But what is it doing to **my** household?"*
>This platform turns official statistics into an answer you can act on.

**NISR 2026 Big Data Hackathon**

**Track 2:** Financial Inclusion & Poverty Reduction

**Team:** CostNav RW  

**Members:** Marie Diane Habiyaremye · Samuel KURADUSENGE  

*---*

## Live Application

**Frontend:** https://kuradusengesamuel-create.github.io/rwanda-cost-of-living-navigator/

**Backend API:** https://rwanda-cost-of-living-navigator.onrender.com

> The backend runs on Render free tier — if slow on first visit, wait 60 seconds then refresh.

**API Docs:** https://rwanda-cost-of-living-navigator.onrender.com/docs

---

## The Problem

Every month NISR publishes the national inflation rate. It is one number for the whole country, at one point in time. A household, a shop owner or a policy analyst can see what inflation was, but not how it hits their situation, and not where it is heading.

A family that spends most of its money on food and transport feels inflation very differently from one that spends mostly on rent. Policymakers also need to know where pressure is building before it deepens poverty and inequality.

---

## What This Tool Does

The Rwanda Cost-of-Living Navigator transforms official NISR statistics (CPI + EICV7) into personalized cost-of-living intelligence for three types of users:

## What the Platform Does

| Tier | Built for | Question it answers |
|------|-----------|-------------------|
| 🏠 Personal | Households | "What is my inflation rate, and which spending category is hurting me most?" |
| 🏪 Business | Small business owners | "Which costs are rising fastest, and what should I plan for?" |
| 🏛️ Government | Policy analysts, social-protection teams | "Which districts and income groups face the most cost-of-living pressure?" |
| 🔮 Forecast | All of the above | "What are prices likely to do in the next 1–3 months?" |

Extra features: AI advice in English and Kinyarwanda, early-warning flags, comparison with typical household profiles, and a WhatsApp share button. No login is needed.

An integrated **AI Chat** (powered by Groq/Llama3) provides personalised cost-saving advice in English and Kinyarwanda.

---

## How It Works

- **Official data in:** Monthly CPI by category (NISR, August 2026) and the EICV7 household survey (2023–2024).
- **Personal inflation** = your spending shares × the inflation rate of each category. Spend more on a category that rose a lot, and your rate is higher than the national one.
- **District pressure index** = each district's typical spending basket (from EICV7) × current category inflation. District figures are modelled estimates, because NISR does not publish district-level CPI.
- **Forecast** = the median of the last 6 monthly price changes per category, tapered 5% and 10% for months 2 and 3, with a ±1.5 standard-deviation range. Chosen because it is simple, explainable, and tested better than alternatives.
- **Early warnings** flag districts above the High-pressure threshold, food inflation above 15% and transport inflation above 25%.

---

## How We Checked Our Own Work

| Check | Result |
|-------|--------|
| Forecast backtest (36 past months, 12 categories, 1–3 months ahead) | Median method: average miss of 0.94 percentage points a month. Weighted average missed by 1.24, "no change" by 1.05 |
| Forecast range | The stated range contained the real figure about 75% of the time |
| Government tier vs NISR's own Urban/Rural CPI (Aug 2026) | Our household-weighted index: Urban 16.4% (NISR 15.7%), Rural 15.7% (NISR 16.0%). District ranking agrees at 0.92–0.95 rank correlation |
| Basket sanity check | National basket close to NISR's CPI weights: food 41.7% vs 39.0%, housing 18.7% vs 18.3%, furnishings 3.3% vs 3.5% |

---

## Honest Limitations

- District and income-group figures are estimates built from national category inflation. Differences between districts are small (~15.1%–16.9%), so High/Medium/Lower labels are relative to the national rate, not absolute risk levels.
- Survey data under-reports alcohol and tobacco spending (0.2% of the basket against 6.8% in the CPI).
- Forecasts cover 1–3 months only and are model estimates, not official NISR figures.
- Data shown is August 2026. A monthly auto-refresh is planned but not yet built.
- AI advice is general guidance, Even Though it is planned, but not professional financial advice yet.

---

## Alignment with National Priorities

- **NST2 and Vision 2050:** evidence-based, proactive decision-making; inclusive economic growth.
- **SDG 1** (No Poverty), **SDG 8** (Decent Work & Economic Growth), **SDG 10** (Reduced Inequalities): shows which households and areas bear the highest cost pressure.

---


## Data Sources
## NISR Official Statistics

Consumer Price Index (CPI)

https://www.statistics.gov.rw/statistical-publications/subject/consumer-price-index

EICV7 Household Survey

https://microdata.statistics.gov.rw/index.php/catalog/119/get_microdata

Processed data files are in `backend/data/`. The full pipeline is in `codes/data_Pipeline/Collab_Notebook/`.

---

## Repository Structure

rwanda-cost-of-living-navigator/

├── frontend/ Static site ← HTML/CSS/JS(GitHub Pages): index, personal, business, government pages,

│ EN/RW language toggle

├── backend/

│ ├── app/ FastAPI app: main.py, config.py, models.py,

│ │ └── routers/ personal.py · business.py · government.py · ai_advice.py

│ └── data/ Processed CSV/JSON files the API serves

├── codes/ Data pipeline notebook and exploration script

├── demo/ Demo video (3-minute screen recording)

├── student_cards/ Eligibility documents for both members

└── README.md

---


## Run It Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
python -m http.server 5500      # then open http://localhost:5500
```

To use your own backend, change `BACKEND_URL` in `frontend/js/app.js` to `http://localhost:8000`.

The AI features need a Groq API key set as the environment variable `GEMINI_API_KEY`. Never commit keys to GitHub.

---

## Originality Declaration

This submission is our own original work, has not been submitted to any other competition, and all sources are acknowledged above.

---

## Team

| Name | Role |
|------|------|
| Marie Diane Habiyaremye | Frontend, AI integration, deployment |
| Samuel KURADUSENGE | Data pipeline, backend API, analysis (Team leader)|

**Department:** African Centre of Excellence in Data Science (ACE-DS), University of Rwanda

