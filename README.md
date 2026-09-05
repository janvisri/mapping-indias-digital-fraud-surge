# Mapping India's Digital Fraud Surge - INSIGHTRA

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR-USERNAME/mapping-indias-digital-fraud-surge/blob/main/notebooks/analysis.ipynb)

**State-wise analysis of cyber & financial fraud trends in India (2019–2024)** — cleaning a messy government-style dataset and analyzing national trends, the worst-hit states, how fast fraud is growing, which fraud types are taking over, and how well cases actually get prosecuted.

> ⚠️ **Synthetic data notice:** Real government data sources are cited below, but for portfolio purposes this project runs on a **synthetic dataset modeled on real published NCRP/NCRB statistics and trends** (see [`generate_data.py`](generate_data.py) for exactly how the numbers were grounded in real reported figures). The cleaning and analysis code is written to transfer directly to the real tables — swap the CSV and re-run.

## What's in this analysis

- **Data cleaning** — missing values, inconsistent state naming (`Delhi` / `NCT of Delhi`, `Puducherry` / `Pondicherry`), duplicate rows, and a data-integrity check (chargesheeted cases can't exceed registered cases)
- **National trend** — total cases registered, 2019–2024
- **Top states** — which states/UTs report the most cases, with an honest caveat about raw counts vs. population
- **Growth by state** — which states are growing fastest year-over-year, including a look at why Nagaland's numbers are misleading (a reporting-gap artifact, not a real surge)
- **Fraud-type mix** — how UPI Fraud overtook OTP Fraud as the dominant category
- **Conviction rates** — the gap between cases *registered* and cases that actually end in a *conviction*

## Headline findings

1. Cases nearly **tripled nationally between 2021 and 2024** (~7,500 → ~21,600 registered cases in this dataset), consistent with the real ~3x growth reported for cyber fraud complaints over the same period.
2. **Uttar Pradesh, Maharashtra, Telangana, and Karnataka** account for the largest share of total registered cases — but raw counts favor bigger states, so this isn't a clean "worst state" ranking without a population adjustment.
3. **UPI Fraud overtook OTP Fraud as the dominant fraud type**, rising from ~24% of cases in 2021 to ~48% in 2024, while OTP Fraud's share fell from 28% to 17% — tracking UPI's rapid adoption nationally.
4. **The national conviction rate is under 4%**, and even the best-performing states (Odisha, Goa, West Bengal) only reach 5–6% — registration and prosecution are two very different stories in this data.
5. **Nagaland's data shows a known reporting-gap pattern** (near-zero cases in 2019–2020, followed by more consistent reporting) rather than a genuine fraud surge — a reminder to sanity-check outliers before reading them as real trends.

See the notebook for the full walkthrough, charts, and the reasoning behind every cleaning decision.

## Data sources (for the real version of this project)

- [data.gov.in — Open Government Data Platform](https://data.gov.in) (National Cyber Crime Reporting Portal stats)
- [NCRB "Crime in India" reports](https://ncrb.gov.in)
- [Dataful.in](https://dataful.in) — pre-cleaned NCRB cyber crime datasets

## Project structure

```
mapping-indias-digital-fraud-surge/
├── README.md
├── requirements.txt
├── generate_data.py          # builds data/cyber_fraud_data.csv
├── data/
│   └── cyber_fraud_data.csv  # synthetic, NCRP/NCRB-grounded dataset
└── notebooks/
    └── analysis.ipynb        # cleaning + analysis walkthrough
```

## Running it

**Locally:**

```bash
git clone https://github.com/janvisri/mapping-indias-digital-fraud-surge.git
cd mapping-indias-digital-fraud-surge
pip install -r requirements.txt

# optional: regenerate data/cyber_fraud_data.csv from scratch
python generate_data.py

jupyter notebook notebooks/analysis.ipynb
```



## What I'd do next with more time / real data

- Pull the actual NCRP/NCRB tables from data.gov.in or Dataful.in and re-run this same notebook against them — the cleaning and analysis logic should transfer directly.
- Bring in state-wise population or UPI transaction volume to turn the raw case counts into a fairer per-capita or per-transaction comparison.
- Look at transaction-level data (if available) instead of yearly aggregates, to catch seasonal patterns (e.g. festival-season spikes in UPI fraud).
- Dig into *why* conviction rates are so low in the bottom states — is it a court backlog issue, an investigation-capacity issue, or a data-reporting issue? That needs qualitative context this dataset doesn't have.

## License

MIT — see [LICENSE](LICENSE).
