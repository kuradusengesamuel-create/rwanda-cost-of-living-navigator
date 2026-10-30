# Rwanda Cost-of-Living Navigator

*"NISR says inflation is 15.9%. But what is it doing to **my** household?"*
>This platform turns official statistics into an answer you can act on.

**NISR 2026 Big Data Hackathon**
**Track 2:** Financial Inclusion & Poverty Reduction
**Team:** CostNav RW  
**Members:** Marie Diane Habiyaremye · Samuel KURADUSENGE  

*---*

## What This Tool Does

The Rwanda Cost-of-Living Navigator transforms official NISR statistics (CPI + EICV7) into personalized cost-of-living intelligence for three types of users:

| Tier | Who It Serves | What It Answers |
|------|---------------|-----------------|
| 🏠 Personal | Rwandan households | "How much more am I spending this month vs last year?" |
| 🏢 Business | SMEs and enterprises | "Which cost categories are squeezing my margins most?" |
| 🏛️ Government | Policy makers, analysts | "Which districts face the highest inflation pressure?" |

An integrated **AI Chat** (powered by Groq/Llama3) provides personalised cost-saving advice in English and Kinyarwanda.

---

## Live Application

**Frontend:** https://kuradusengesamuel-create.github.io/rwanda-cost-of-living-navigator/

**Backend API:** https://rwanda-cost-of-living-navigator.onrender.com

> The backend runs on Render free tier — if slow on first visit, wait 60 seconds then refresh.

**API Docs:** https://rwanda-cost-of-living-navigator.onrender.com/docs

---

## Data Sources

| Dataset | Source |
|---------|--------|
| Consumer Price Index (CPI) | [NISR Official Statistics](https://www.statistics.gov.rw/statistical-publications/subject/consumer-price-index) |
| EICV7 Household Survey | [NISR EICV7](https://www.statistics.gov.rw/survey/integrated-household-living-conditions-survey-eicv7) |

Processed data files are in `backend/data/`. The full pipeline is in `codes/data_Pipeline/Collab_Notebook/`.

---

## Repository Structure
