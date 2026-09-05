"""
generate_data.py
=================
Builds the synthetic dataset used in notebooks/analysis.ipynb
(data/cyber_fraud_data.csv).

Why synthetic data?
-------------------
The real numbers behind this project's narrative (national case totals,
the UPI-fraud takeover, the ~4% conviction rate, etc.) are drawn from
publicly reported NCRP/NCRB figures and commentary -- see the sources
listed in the README. Rather than scrape/reformat those government PDFs
and portals (which are inconsistent about state-level breakdowns and
change format year to year), this script generates a state x year x
fraud-type dataset that is *grounded in those reported topline trends*:

  - national cases registered roughly tripling between 2021 and 2024
  - UPI Fraud overtaking OTP Fraud as the largest category over 2019-2024
  - a low (~4%) national conviction rate
  - a handful of the largest, most digitally-active states (UP,
    Maharashtra, Telangana, Karnataka, ...) accounting for the most cases

On top of that realistic backbone, it deliberately injects the kind of
messiness real government reporting data actually has, so the cleaning
section of the notebook has real problems to solve:
  - a few missing values in `cases_convicted` / `amount_saved_inr`
  - two spellings each for Delhi and Puducherry
  - one exact duplicate row
  - two rows where `cases_chargesheeted` > `cases_registered`
  - a genuine reporting-gap artifact in Nagaland's 2019-2020 numbers

Run:
    python generate_data.py

Output:
    data/cyber_fraud_data.csv
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

OUT_PATH = "data/cyber_fraud_data.csv"

YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

FRAUD_TYPES = [
    "UPI Fraud",
    "OTP Fraud",
    "Online Banking Fraud",
    "Card Fraud",
    "Identity Theft",
    "Other",
]

# National case totals by year (roughly tracks the ~3x rise in cyber
# fraud complaints reported nationally between 2021 and 2024).
YEARLY_TOTALS = {
    2019: 4608,
    2020: 5992,
    2021: 7478,
    2022: 12118,
    2023: 18208,
    2024: 21567,
}

# National fraud-type mix by year, as a % of that year's cases.
# UPI Fraud climbs from ~10% to ~48%; OTP Fraud fades from ~35% to ~17%.
FRAUD_SHARE_BY_YEAR = {
    2019: {"UPI Fraud": 9.8, "OTP Fraud": 35.3, "Online Banking Fraud": 24.9,
           "Card Fraud": 14.8, "Identity Theft": 8.2, "Other": 7.0},
    2020: {"UPI Fraud": 16.2, "OTP Fraud": 32.0, "Online Banking Fraud": 21.8,
           "Card Fraud": 14.0, "Identity Theft": 9.1, "Other": 6.9},
    2021: {"UPI Fraud": 24.0, "OTP Fraud": 28.1, "Online Banking Fraud": 17.7,
           "Card Fraud": 13.2, "Identity Theft": 10.1, "Other": 6.9},
    2022: {"UPI Fraud": 32.3, "OTP Fraud": 24.2, "Online Banking Fraud": 15.1,
           "Card Fraud": 12.1, "Identity Theft": 9.1, "Other": 7.2},
    2023: {"UPI Fraud": 42.1, "OTP Fraud": 19.9, "Online Banking Fraud": 12.0,
           "Card Fraud": 11.1, "Identity Theft": 8.0, "Other": 6.9},
    2024: {"UPI Fraud": 47.8, "OTP Fraud": 17.0, "Online Banking Fraud": 10.1,
           "Card Fraud": 10.0, "Identity Theft": 8.1, "Other": 7.0},
}

# Relative "how much digital-fraud activity happens here" weight per
# state/UT -- loosely modeled on population + digital-payment adoption,
# tuned so the biggest, most digitally-active states land on top.
STATE_WEIGHTS = {
    "Uttar Pradesh": 10.5, "Maharashtra": 9.6, "Telangana": 9.3,
    "Karnataka": 8.3, "Tamil Nadu": 7.5, "Delhi": 7.4, "Gujarat": 6.1,
    "West Bengal": 5.8, "Rajasthan": 5.8, "Haryana": 5.0, "Kerala": 4.0,
    "Madhya Pradesh": 3.8, "Punjab": 3.2, "Bihar": 3.0,
    "Andhra Pradesh": 2.8, "Odisha": 2.2, "Assam": 1.6, "Jharkhand": 1.5,
    "Chhattisgarh": 1.3, "Uttarakhand": 1.1, "Himachal Pradesh": 0.8,
    "Goa": 0.6, "Puducherry": 0.5, "Tripura": 0.4, "Manipur": 0.35,
    "Meghalaya": 0.3, "Nagaland": 0.3, "Mizoram": 0.25, "Sikkim": 0.2,
    "Arunachal Pradesh": 0.25,
}
STATES = list(STATE_WEIGHTS.keys())

# Nagaland is a known real-world reporting-gap case: very low recorded
# cases in 2019-2020, then a jump once reporting caught up. We model
# that as a temporarily depressed weight in those two years.
NAGALAND_DEPRESSED_YEARS = {2019, 2020}
NAGALAND_DEPRESSION_FACTOR = 0.32

# A few states saw digital-fraud reporting climb faster than the
# national average over 2019-2024 (rapid UPI/smartphone adoption
# outpacing their starting base). Modeled as a gently rising weight
# multiplier by year, on top of the static base weight above.
STATE_GROWTH_TREND = {
    "Uttarakhand": 0.16,
    "Uttar Pradesh": 0.055,
    "Madhya Pradesh": 0.11,
}

# Rough chargesheet rate and per-case recovery amount by fraud type.
# UPI/OTP scams tend to involve anonymous mule accounts and cross-state
# / cross-border actors, so they are harder to chargesheet and recover
# money from than, say, card fraud or identity theft.
FRAUD_TYPE_PROFILE = {
    "UPI Fraud":             {"chargesheet_rate": 0.42, "avg_amount": 9_000,  "conv_mult": 0.6},
    "OTP Fraud":              {"chargesheet_rate": 0.45, "avg_amount": 14_000, "conv_mult": 0.7},
    "Online Banking Fraud":   {"chargesheet_rate": 0.55, "avg_amount": 55_000, "conv_mult": 1.0},
    "Card Fraud":             {"chargesheet_rate": 0.60, "avg_amount": 22_000, "conv_mult": 1.1},
    "Identity Theft":         {"chargesheet_rate": 0.58, "avg_amount": 70_000, "conv_mult": 1.2},
    "Other":                  {"chargesheet_rate": 0.50, "avg_amount": 18_000, "conv_mult": 0.9},
}

# States that, per the (synthetic) data, prosecute relatively well or
# relatively poorly -- gives the conviction-rate chart real spread
# instead of uniform noise.
STATE_CONVICTION_MULT = {
    "Odisha": 1.42, "Goa": 1.39, "West Bengal": 1.20, "Kerala": 1.05,
    "Himachal Pradesh": 1.02,
}
STATE_CONVICTION_MULT_LOW = {
    "Bihar": 0.35, "Uttar Pradesh": 0.45, "Jharkhand": 0.4,
    "Manipur": 0.4, "Arunachal Pradesh": 0.45,
}
BASE_CONVICTION_RATE = 0.053  # tuned so the *volume-weighted* national
                              # average lands close to the ~4% reported figure
                              # (UPI Fraud has the lowest conv_mult and is
                              # also the fastest-growing share of cases, which
                              # pulls the volume-weighted average down)
CONVICTION_NOISE_STD = 0.10   # relative std-dev of per-row conviction-rate noise


def largest_remainder_round(values, total):
    """Round an array of non-negative floats to integers that sum exactly
    to `total`, using the largest-remainder (Hamilton) apportionment
    method so no single category absorbs all the rounding error."""
    floors = np.floor(values).astype(int)
    remainder = int(total - floors.sum())
    if remainder > 0:
        fracs = values - floors
        top_idx = np.argsort(-fracs)[:remainder]
        floors[top_idx] += 1
    elif remainder < 0:
        fracs = values - floors
        bottom_idx = np.argsort(fracs)[: (-remainder)]
        floors[bottom_idx] -= 1
    return floors


def build_registered_cases():
    """Allocate each year's national total down to fraud_type, then down
    to state/UT, using the weights/shares above plus a bit of noise."""
    rows = []
    for year in YEARS:
        year_total = YEARLY_TOTALS[year]
        shares = FRAUD_SHARE_BY_YEAR[year]
        type_names = list(shares.keys())
        type_shares = np.array([shares[t] for t in type_names])
        type_targets = type_shares / type_shares.sum() * year_total
        type_counts = largest_remainder_round(type_targets, year_total)

        for fraud_type, type_total in zip(type_names, type_counts):
            weights = np.array([STATE_WEIGHTS[s] for s in STATES], dtype=float)

            # Apply Nagaland's reporting-gap depression for 2019-2020.
            if year in NAGALAND_DEPRESSED_YEARS:
                weights[STATES.index("Nagaland")] *= NAGALAND_DEPRESSION_FACTOR

            # Apply the gentle multi-year growth trend for fast-rising states.
            year_index = YEARS.index(year)
            for state, trend in STATE_GROWTH_TREND.items():
                weights[STATES.index(state)] *= (1 + trend * year_index)

            # A little per-state noise so it doesn't look mechanically smooth.
            noise = RNG.normal(1.0, 0.10, size=len(STATES)).clip(0.6, 1.5)
            weights = weights * noise
            weights = weights / weights.sum()

            state_targets = weights * type_total
            state_counts = largest_remainder_round(state_targets, int(type_total))

            for state, count in zip(STATES, state_counts):
                rows.append(
                    {"state_ut": state, "year": year, "fraud_type": fraud_type,
                     "cases_registered": int(count)}
                )
    return pd.DataFrame(rows)


def add_downstream_columns(df):
    df = df.copy()

    chargesheeted, convicted, arrested, amounts, complaints = [], [], [], [], []

    for _, row in df.iterrows():
        profile = FRAUD_TYPE_PROFILE[row["fraud_type"]]
        registered = row["cases_registered"]

        # Chargesheeted cases.
        rate = np.clip(RNG.normal(profile["chargesheet_rate"], 0.08), 0.05, 0.95)
        cs = int(round(registered * rate))
        cs = min(cs, registered)

        # Convictions: base national rate, adjusted by fraud-type
        # difficulty and by how well that state's justice system performs.
        state_mult = STATE_CONVICTION_MULT.get(row["state_ut"], 1.0)
        state_mult = STATE_CONVICTION_MULT_LOW.get(row["state_ut"], state_mult)
        conv_rate = BASE_CONVICTION_RATE * profile["conv_mult"] * state_mult
        conv_rate = np.clip(RNG.normal(conv_rate, conv_rate * CONVICTION_NOISE_STD), 0, 0.95)
        conv = int(round(registered * conv_rate))
        conv = min(conv, cs) if cs > 0 else 0

        # Persons arrested tends to track chargesheeted cases, with some
        # cases involving multiple arrests and others none.
        arr = int(round(cs * RNG.uniform(0.8, 1.9)))

        # Amount saved/recovered by police action (INR), varies a lot by
        # fraud type and case volume.
        amt = round(registered * profile["avg_amount"] * RNG.uniform(0.6, 1.4), 2)

        # Not every complaint becomes a registered case (some are
        # duplicates, withdrawn, or resolved informally).
        comp = int(round(registered / RNG.uniform(0.55, 0.85)))

        chargesheeted.append(cs)
        convicted.append(conv)
        arrested.append(arr)
        amounts.append(amt)
        complaints.append(comp)

    df["cases_chargesheeted"] = chargesheeted
    df["cases_convicted"] = convicted
    df["persons_arrested"] = arrested
    df["amount_saved_inr"] = amounts
    df["complaints_count"] = complaints
    return df


def inject_data_quality_issues(df):
    """Add the realistic messiness the cleaning section of the notebook
    is built to catch."""
    df = df.copy()

    # --- Two chargesheeted > registered violations -------------------
    def force_violation(state, year, fraud_type, registered, chargesheeted):
        mask = (
            (df["state_ut"] == state)
            & (df["year"] == year)
            & (df["fraud_type"] == fraud_type)
        )
        df.loc[mask, "cases_registered"] = registered
        df.loc[mask, "cases_chargesheeted"] = chargesheeted

    force_violation("Manipur", 2023, "Online Banking Fraud", 10, 23)
    force_violation("Sikkim", 2021, "OTP Fraud", 5, 20)

    # --- Inconsistent state naming: two spellings each ----------------
    delhi_recode = (df["state_ut"] == "Delhi") & (df["year"].isin([2019, 2020]))
    df.loc[delhi_recode, "state_ut"] = "NCT of Delhi"

    pon_recode = (df["state_ut"] == "Puducherry") & (df["year"].isin([2019, 2020, 2021]))
    df.loc[pon_recode, "state_ut"] = "Pondicherry"

    # --- Missing values: a handful of rows in two columns -------------
    convicted_nan_idx = RNG.choice(df.index, size=4, replace=False)
    df.loc[convicted_nan_idx, "cases_convicted"] = np.nan

    remaining_idx = df.index.difference(convicted_nan_idx)
    amount_nan_idx = RNG.choice(remaining_idx, size=4, replace=False)
    df.loc[amount_nan_idx, "amount_saved_inr"] = np.nan

    # --- One exact duplicate row ---------------------------------------
    dup_source_idx = RNG.choice(
        df.index.difference(convicted_nan_idx.tolist() + amount_nan_idx.tolist()),
        size=1,
    )
    dup_row = df.loc[dup_source_idx]
    df = pd.concat([df, dup_row], ignore_index=True)

    return df


def main():
    df = build_registered_cases()
    df = add_downstream_columns(df)
    df = inject_data_quality_issues(df)

    # Shuffle row order so it doesn't look artificially grouped by
    # state/year/fraud_type, then reset the index.
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    column_order = [
        "state_ut", "year", "fraud_type", "cases_registered",
        "cases_chargesheeted", "cases_convicted", "persons_arrested",
        "amount_saved_inr", "complaints_count",
    ]
    df = df[column_order]

    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")
    print(f"  Unique state_ut labels (raw, pre-cleaning): {df['state_ut'].nunique()}")
    print(f"  Duplicate rows: {df.duplicated().sum()}")
    print(f"  Missing values: {df.isnull().sum().sum()}")


if __name__ == "__main__":
    main()
