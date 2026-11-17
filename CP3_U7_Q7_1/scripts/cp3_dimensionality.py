"""CP3 U7/Q7.1: reproducible PCA baseline vs UMAP protocol.

Run from the repository root:
    python CP3_U7_Q7_1/scripts/cp3_dimensionality.py
Reads the existing CP2 dataset from CP2_U7_Q7_1/data/.
Outputs CSVs and sample embeddings to results/cp3/.
"""
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness
from sklearn.preprocessing import StandardScaler

try:
    import umap
except ImportError as exc:
    raise SystemExit("Lipsește umap-learn. Rulează: python -m pip install umap-learn") from exc

ROOT = Path(__file__).resolve().parents[1]  # folder CP3_U7_Q7_1
REPO = ROOT.parent
DATA_CANDIDATES = [
    ROOT / "data" / "U7_Q7_1_lac_luna_2001_2021.csv.gz",
    REPO / "CP2_U7_Q7_1" / "data" / "U7_Q7_1_lac_luna_2001_2021.csv.gz",
]
DATA = next((p for p in DATA_CANDIDATES if p.exists()), DATA_CANDIDATES[-1])
OUT = ROOT / "results" / "cp3"
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = {
    "ERA5_Land": ["t2m_c", "precip_mm"],
    "Combinat": ["water_km2", "t2m_c", "precip_mm", "month_sin", "month_cos"],
}
SEEDS = [11, 23, 37, 51, 79]
N_TRAIN_UMAP = 10_000
N_TEST_EVAL = 5_000
K_VALUES = [5, 10, 15]
N_COMPONENTS = 2


def sample_rows(frame, n, seed):
    if len(frame) <= n:
        return frame.copy()
    return frame.sample(n=n, random_state=seed).sort_index()


def trust_at_k(high_dim, low_dim, k):
    # sklearn requires k < n/2. Smaller evaluation samples are handled safely.
    k_eff = min(k, max(1, (len(high_dim) - 1) // 2))
    return float(trustworthiness(high_dim, low_dim, n_neighbors=k_eff))


def reconstruction_rmse(estimator, z):
    try:
        reconstructed = estimator.inverse_transform(estimator.transform(z))
    except (AttributeError, NotImplementedError, ValueError):
        return np.nan
    return float(np.sqrt(np.mean(np.square(z - reconstructed))))


def run_view(frame, view_name, features):
    clean = frame.dropna(subset=features).copy()
    train = clean.loc[clean["year"] <= 2017]
    test = clean.loc[clean["year"] >= 2018]
    if train.empty or test.empty:
        raise ValueError(f"Split temporal gol pentru {view_name}.")

    scaler = StandardScaler().fit(train[features])
    z_train = scaler.transform(train[features])
    z_test = scaler.transform(test[features])

    # PCA is fitted on all training observations; its held-out metrics use a fixed sample.
    pca = PCA(n_components=N_COMPONENTS, svd_solver="full").fit(z_train)
    test_idx = sample_rows(test, N_TEST_EVAL, 2026).index
    z_test_eval = scaler.transform(test.loc[test_idx, features])
    pca_test_embedding = pca.transform(z_test_eval)
    pca_test_recon = pca.inverse_transform(pca_test_embedding)
    pca_rmse = float(np.sqrt(np.mean(np.square(z_test_eval - pca_test_recon))))

    for k in K_VALUES:
        yield {
            "view": view_name, "method": "PCA", "seed": "deterministic",
            "period": "test_2018_2021_11", "n_train": len(train), "n_test_eval": len(test_idx),
            "n_features": len(features), "trustworthiness_k": k,
            "trustworthiness": trust_at_k(z_test_eval, pca_test_embedding, k),
            "explained_variance_2d": float(pca.explained_variance_ratio_.sum()),
            "reconstruction_rmse_sd": pca_rmse,
            "umap_n_neighbors": np.nan, "umap_min_dist": np.nan,
        }

    # UMAP fit on a reproducible training sample, then transforms held-out test observations.
    train_sample = sample_rows(train, N_TRAIN_UMAP, 2026)
    z_train_sample = scaler.transform(train_sample[features])
    for seed in SEEDS:
        reducer = umap.UMAP(
            n_components=N_COMPONENTS, n_neighbors=15, min_dist=0.1,
            metric="euclidean", random_state=seed, transform_seed=seed,
            n_jobs=1, low_memory=True,
        )
        reducer.fit(z_train_sample)
        z_umap_test = reducer.transform(z_test_eval)
        rec_rmse = reconstruction_rmse(reducer, z_test_eval)
        for k in K_VALUES:
            yield {
                "view": view_name, "method": "UMAP", "seed": seed,
                "period": "test_2018_2021_11", "n_train": len(train_sample), "n_test_eval": len(test_idx),
                "n_features": len(features), "trustworthiness_k": k,
                "trustworthiness": trust_at_k(z_test_eval, z_umap_test, k),
                "explained_variance_2d": np.nan,
                "reconstruction_rmse_sd": rec_rmse,
                "umap_n_neighbors": 15, "umap_min_dist": 0.1,
            }
        # Save test embeddings for later plots; one CSV per view/seed, sampled and reproducible.
        emb = pd.DataFrame(z_umap_test, columns=["UMAP1", "UMAP2"], index=test_idx)
        meta = test.loc[test_idx, [c for c in ["Hylak_id", "month", "year"] if c in test.columns]]
        pd.concat([meta, emb], axis=1).to_csv(OUT / f"embedding_{view_name}_seed{seed}.csv", index=False)


def run_subperiod_checks(frame, view_name, features):
    """Compare neighborhood preservation inside two time windows.

    Each window is scaled and fitted independently. These are descriptive
    within-period checks (not out-of-period predictive tests).
    """
    output = []
    windows = {
        "2001_2010": (2001, 2010),
        "2011_2021_11": (2011, 2021),
    }
    for label, (start, end) in windows.items():
        subset = frame.loc[frame.year.between(start, end)].dropna(subset=features)
        if len(subset) < 50:
            warnings.warn(f"Prea puține observații pentru {view_name}/{label}; omit.")
            continue
        # Use a fixed, reproducible sample for a tractable and comparable check.
        sample = sample_rows(subset, min(5000, len(subset)), 2026)
        scaler = StandardScaler().fit(sample[features])
        z = scaler.transform(sample[features])
        pca = PCA(n_components=2, svd_solver="full").fit(z)
        pca_embedding = pca.transform(z)
        for k in K_VALUES:
            output.append({
                "view": view_name, "period": label, "method": "PCA",
                "seed": "deterministic", "n_sample": len(sample),
                "trustworthiness_k": k,
                "trustworthiness": trust_at_k(z, pca_embedding, k),
                "explained_variance_2d": float(pca.explained_variance_ratio_.sum()),
            })
        for seed in SEEDS:
            reducer = umap.UMAP(
                n_components=2, n_neighbors=15, min_dist=0.1,
                metric="euclidean", random_state=seed, transform_seed=seed,
                n_jobs=1, low_memory=True,
            ).fit(z)
            emb = reducer.embedding_
            for k in K_VALUES:
                output.append({
                    "view": view_name, "period": label, "method": "UMAP",
                    "seed": seed, "n_sample": len(sample),
                    "trustworthiness_k": k,
                    "trustworthiness": trust_at_k(z, emb, k),
                    "explained_variance_2d": np.nan,
                })
    return output


def main():
    if not DATA.exists():
        raise SystemExit(f"Nu găsesc datele CP2: {DATA}\nPune folderul CP3 lângă CP2_U7_Q7_1 și verifică existența CSV-ului din CP2/data/.")
    df = pd.read_csv(DATA)
    required = {"year", "water_km2", "t2m_c", "precip_mm", "month_sin", "month_cos"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Coloane absente din exportul CP2: {sorted(missing)}")

    results = []
    # JRC contains only one numeric source feature: PCA is trivial (100% variance in PC1),
    # and 1D->2D UMAP would not be a meaningful dimensionality reduction. Report this explicitly.
    results.append({
        "view": "JRC", "method": "Not applicable", "seed": "-",
        "period": "all", "n_train": int((df.year <= 2017).sum()), "n_test_eval": int((df.year >= 2018).sum()),
        "n_features": 1, "trustworthiness_k": np.nan, "trustworthiness": np.nan,
        "explained_variance_2d": 1.0, "reconstruction_rmse_sd": 0.0,
        "umap_n_neighbors": np.nan, "umap_min_dist": np.nan,
    })
    subperiod_results = []
    for view, features in FEATURES.items():
        print(f"Rulez PCA și UMAP: {view}, d={len(features)}")
        results.extend(run_view(df, view, features))
        subperiod_results.extend(run_subperiod_checks(df, view, features))

    metrics = pd.DataFrame(results)
    metrics.to_csv(OUT / "cp3_metrics.csv", index=False)
    summary = (metrics[metrics.method == "UMAP"]
               .groupby(["view", "trustworthiness_k"], as_index=False)
               .agg(trust_mean=("trustworthiness", "mean"), trust_sd=("trustworthiness", "std"),
                    seeds=("seed", "nunique")))
    summary.to_csv(OUT / "cp3_umap_stability.csv", index=False)
    subperiod = pd.DataFrame(subperiod_results)
    subperiod.to_csv(OUT / "cp3_subperiod_metrics.csv", index=False)
    (subperiod[subperiod.method == "UMAP"]
     .groupby(["view", "period", "trustworthiness_k"], as_index=False)
     .agg(trust_mean=("trustworthiness", "mean"), trust_sd=("trustworthiness", "std"),
          seeds=("seed", "nunique"))
     .to_csv(OUT / "cp3_subperiod_stability.csv", index=False))
    pd.DataFrame([
        {"view": "ERA5_Land", "features": ";".join(FEATURES["ERA5_Land"]), "n_features": 2,
         "decision": "Compare PCA and UMAP; UMAP maps 2D to 2D, so interpret primarily as neighborhood-preservation check."},
        {"view": "Combinat", "features": ";".join(FEATURES["Combinat"]), "n_features": 5,
         "decision": "Primary dimensionality-reduction comparison: 5D to 2D."},
        {"view": "JRC", "features": "water_km2", "n_features": 1,
         "decision": "Report PCA trivial 1D baseline; do not claim meaningful dimensionality reduction."},
    ]).to_csv(OUT / "cp3_view_definition.csv", index=False)
    print(f"Gata. Rezultate: {OUT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
