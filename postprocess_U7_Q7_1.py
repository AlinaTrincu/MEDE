"""Build X, coverage report and training-only scaling from the GEE CSV.

Run in Google Colab after downloading U7_Q7_1_lac_luna_2001_2021.csv from Drive:
  1) upload CSV to Colab
  2) set INPUT_CSV to the uploaded filename
  3) run this file / notebook cell

Uses pandas and scikit-learn, available in Google Colab. Missing data are reported,
not imputed. For the main X, rows with missing predictors or zero JRC valid area are
excluded and counted in coverage.csv. Split: train 2001-2017, test 2018-2021.
The scaler is fitted on train only to prevent temporal leakage.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

INPUT_CSV = "U7_Q7_1_lac_luna_2001_2021.csv"
OUT_DIR = Path("U7_Q7_1_outputs")
FEATURES = ["water_km2", "t2m_c", "precip_mm", "month_sin", "month_cos"]
KEYS = ["Hylak_id", "month", "year", "month_number"]

OUT_DIR.mkdir(exist_ok=True)
df = pd.read_csv(INPUT_CSV)
required = set(KEYS + FEATURES + ["valid_area_km2"])
missing_columns = sorted(required - set(df.columns))
if missing_columns:
    raise ValueError(f"CSV missing expected columns: {missing_columns}")

df["year"] = pd.to_numeric(df["year"], errors="coerce")
for col in FEATURES + ["valid_area_km2"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# JRC area is missing when the source has no valid pixel coverage in that lake-month.
df.loc[df["valid_area_km2"].fillna(0) <= 0, "water_km2"] = np.nan
expected_months = 252
n_lakes = df["Hylak_id"].nunique(dropna=True)
expected_rows = n_lakes * expected_months
complete_mask = df[FEATURES].notna().all(axis=1) & df["Hylak_id"].notna() & df["year"].notna()
complete = df.loc[complete_mask].copy()

coverage = pd.DataFrame([{
    "selected_lakes_in_export": n_lakes,
    "months_expected_per_lake": expected_months,
    "rows_expected_for_exported_lakes": expected_rows,
    "rows_exported": len(df),
    "rows_with_complete_X": len(complete),
    "rows_excluded_from_X": len(df) - len(complete),
    "row_coverage_fraction": (len(df) / expected_rows) if expected_rows else np.nan,
    "complete_X_fraction_of_export": (len(complete) / len(df)) if len(df) else np.nan,
    "lakes_with_at_least_one_complete_row": complete["Hylak_id"].nunique(),
}])
coverage.to_csv(OUT_DIR / "coverage.csv", index=False)

# X contains only numeric exploration features. Keys remain metadata alongside X.
X = complete[KEYS + FEATURES].sort_values(["Hylak_id", "year", "month_number"])
X.to_csv(OUT_DIR / "X_raw.csv", index=False)
train_mask = X["year"] <= 2017
test_mask = X["year"] >= 2018
if not train_mask.any() or not test_mask.any():
    raise ValueError("Temporal split is empty. Check that the GEE export covers 2001-2021.")

scaler = StandardScaler()
scaler.fit(X.loc[train_mask, FEATURES])
scaled = X[KEYS].copy()
scaled[FEATURES] = scaler.transform(X[FEATURES])
scaled.loc[train_mask].to_csv(OUT_DIR / "X_train_scaled.csv", index=False)
scaled.loc[test_mask].to_csv(OUT_DIR / "X_test_scaled.csv", index=False)

params = pd.DataFrame({
    "feature": FEATURES,
    "train_mean": scaler.mean_,
    "train_scale": scaler.scale_,
})
params.to_csv(OUT_DIR / "scaling_parameters_train_only.csv", index=False)

with open(OUT_DIR / "shape_and_coverage.txt", "w", encoding="utf-8") as f:
    f.write(f"X shape (complete rows x features): {len(X)} x {len(FEATURES)}\n")
    f.write(f"Train shape: {int(train_mask.sum())} x {len(FEATURES)} (2001-2017)\n")
    f.write(f"Test shape: {int(test_mask.sum())} x {len(FEATURES)} (2018-2021)\n")
    f.write("Features: " + ", ".join(FEATURES) + "\n")
    f.write("Scaling: z-score, fit on training rows only; test transformed with train parameters.\n")
    f.write(f"Expected months per lake: {expected_months}\n")
print(coverage.to_string(index=False))
print((OUT_DIR / "shape_and_coverage.txt").read_text(encoding="utf-8"))
