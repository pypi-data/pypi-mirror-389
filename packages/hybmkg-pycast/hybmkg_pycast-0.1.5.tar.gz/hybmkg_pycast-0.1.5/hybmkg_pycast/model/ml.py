"""
model/ml.py
Full modular implementation ported from forecast_mswep.py
Features implemented:
- build supervised dataset from pandas Series (lags)
- small randomized tuning (TimeSeriesSplit) for base learners
- generate OOF features for stacking (time-series-safe)
- train allbase / pure / mix meta models
- refit base models on full history and perform recursive forecasting
- save models (joblib) and outputs (CSV)
- run_models(series, y_obs, config) as main entrypoint

Returns:
- df_future: pandas.DataFrame with columns for Base_, AllBaseMeta_, Pure_, Mix_, and ensemble averages

Usage: called by run.py
"""

import os
import joblib
from glob import glob
from collections import defaultdict

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
from scipy.stats import randint, uniform

# --------------------------- DEFAULT CONFIG ---------------------------

DEFAULT_CONFIG = {
    "N_LAGS": 60,
    "N_FUTURE": 12,
    "N_TEST": 12,
    "TS_OOF_SPLITS": 5,
    "DO_TUNING": True,
    "N_ITER_RS": 8,
    "RANDOM_STATE": 42,
    "VERBOSE": True,
    "OUT_DIR": "results",
    "PLOTS_DIR": "plots",  # kept for compatibility but unused
}

# --------------------------- UTILS ---------------------------

def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def create_lagged_df(series, n_lags):
    cols = [series.shift(lag).rename(f"lag{lag}") for lag in range(1, n_lags + 1)]
    X = pd.concat(cols, axis=1)
    X.columns = [f"lag{lag}" for lag in range(1, n_lags + 1)]
    return X

# --------------------------- TUNING / BASE ---------------------------

def tune_base_models(X, y, protos, param_dists, n_iter=8, n_splits=5, random_state=42, verbose=True):
    bests = {}
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for name, proto in protos.items():
        params = param_dists.get(name)
        if verbose:
            print(f"[TUNE] {name} ...")
        if params is None:
            if verbose:
                print(f"[TUNE] No params for {name}, fitting default.")
            m = clone(proto).fit(X, y)
            bests[name] = m
            continue
        rs = RandomizedSearchCV(clone(proto), param_distributions=params, n_iter=n_iter,
                                cv=tscv, scoring="neg_root_mean_squared_error",
                                random_state=random_state, n_jobs=-1, verbose=0)
        rs.fit(X, y)
        bests[name] = rs.best_estimator_
        if verbose:
            print(f"[TUNE] {name} done. best params: {rs.best_params_} | CV RMSE {-rs.best_score_:.3f}")
    return bests

# --------------------------- OOF / STACKING helpers ---------------------------

def get_oof_timeseries_full(model_proto, X_vals, y_vals, n_splits=5):
    """Generate out-of-fold predictions over full X (TimeSeriesSplit) using clone(model_proto)."""
    tss = TimeSeriesSplit(n_splits=n_splits)
    n = X_vals.shape[0]
    oof = np.zeros(n)
    for tr_idx, val_idx in tss.split(X_vals):
        m = clone(model_proto)
        m.fit(X_vals[tr_idx], y_vals[tr_idx])
        oof[val_idx] = m.predict(X_vals[val_idx])
    return oof


def train_meta_models(best_bases, X_all, y_all, n_splits_oof=5, verbose=True):
    """
    Create OOF features and train:
       - allbase_meta_models (all base OOF columns -> meta)
       - pure_meta_models (single base OOF column -> meta)
       - mix_meta_models (train meta excluding one base column)
    Returns: (train_meta_matrix, base_names, allbase_meta_models, pure_meta_models, mix_meta_models)
    """
    base_names = list(best_bases.keys())
    if verbose:
        print("[META] Generating OOF features for bases ...")
    oof_list = []
    for name in base_names:
        if verbose:
            print("  OOF for", name)
        oof = get_oof_timeseries_full(best_bases[name], X_all, y_all, n_splits=n_splits_oof).reshape(-1, 1)
        oof_list.append(oof)
    train_meta = np.hstack(oof_list)

    allbase_meta_models = {}
    pure_meta_models = {}
    mix_meta_models = {}

    if verbose:
        print("[META] Training allbase meta models ...")
    for meta_name, proto in best_bases.items():
        m_all = clone(proto)
        m_all.fit(train_meta, y_all)
        allbase_meta_models[meta_name] = m_all

    if verbose:
        print("[META] Training pure meta models ...")
    for i, base_col in enumerate(base_names):
        X_col = train_meta[:, i].reshape(-1, 1)
        for meta_name, proto in best_bases.items():
            m = clone(proto)
            m.fit(X_col, y_all)
            pure_meta_models[(base_col, meta_name)] = m

    if verbose:
        print("[META] Training mix meta models ...")
    for i, excluded in enumerate(base_names):
        X_mix = np.delete(train_meta, i, axis=1)
        for meta_name, proto in best_bases.items():
            m = clone(proto)
            m.fit(X_mix, y_all)
            mix_meta_models[(excluded, meta_name)] = m

    return train_meta, base_names, allbase_meta_models, pure_meta_models, mix_meta_models

# --------------------------- RECURSIVE FORECAST ---------------------------

def recursive_forecast(history_series, scaler, base_full_models, allbase_meta_models,
                       pure_meta_models, mix_meta_models, base_names,
                       n_future=12, n_lags=60, verbose=True):
    future_index = pd.date_range(start=history_series.index[-1] + pd.offsets.MonthBegin(1),
                                 periods=n_future, freq="MS")
    df_future = pd.DataFrame(index=future_index)

    for b in base_names:
        df_future[f"Base_{b}"] = np.nan
    for m in base_names:
        df_future[f"AllBaseMeta_{m}"] = np.nan
    for b in base_names:
        for m in base_names:
            df_future[f"Pure_{b}->{m}"] = np.nan
            if b != m:
                df_future[f"Mix_excl{b}->{m}"] = np.nan

    df_future["Ensemble_Base_avg"] = np.nan
    df_future["Ensemble_Meta_avg"] = np.nan
    df_future["Ensemble_Pure_avg"] = np.nan
    df_future["Ensemble_Mix_avg"] = np.nan
    df_future["Ensemble_Grand_avg"] = np.nan

    for t in range(n_future):
        last_vals = history_series.values[-n_lags:]
        inp = last_vals[::-1].reshape(1, -1)
        inp_scaled = scaler.transform(inp)

        base_preds = {}
        for name, m in base_full_models.items():
            base_preds[name] = m.predict(inp_scaled)[0]
            df_future.loc[future_index[t], f"Base_{name}"] = base_preds[name]

        base_vec = np.array([base_preds[n] for n in base_names]).reshape(1, -1)
        allmeta_preds = {}
        for mname, mmodel in allbase_meta_models.items():
            allmeta_preds[mname] = mmodel.predict(base_vec)[0]
            df_future.loc[future_index[t], f"AllBaseMeta_{mname}"] = allmeta_preds[mname]

        pure_vals, mix_vals = [], []
        for i, b in enumerate(base_names):
            single = np.array([[base_preds[b]]])
            for m in base_names:
                val = pure_meta_models[(b, m)].predict(single)[0]
                df_future.loc[future_index[t], f"Pure_{b}->{m}"] = val
                pure_vals.append(val)

        for i, excluded in enumerate(base_names):
            feat = np.array([base_preds[n] for n in base_names if n != excluded]).reshape(1, -1)
            for m in base_names:
                if excluded == m:
                    continue
                val = mix_meta_models[(excluded, m)].predict(feat)[0]
                df_future.loc[future_index[t], f"Mix_excl{excluded}->{m}"] = val
                mix_vals.append(val)

        base_ens = np.mean(list(base_preds.values()))
        meta_ens = np.mean(list(allmeta_preds.values()))
        pure_ens = np.mean(pure_vals)
        mix_ens = np.mean(mix_vals)
        grand_ens = np.mean([base_ens, meta_ens, pure_ens, mix_ens])

        df_future.loc[future_index[t], "Ensemble_Base_avg"] = base_ens
        df_future.loc[future_index[t], "Ensemble_Meta_avg"] = meta_ens
        df_future.loc[future_index[t], "Ensemble_Pure_avg"] = pure_ens
        df_future.loc[future_index[t], "Ensemble_Mix_avg"] = mix_ens
        df_future.loc[future_index[t], "Ensemble_Grand_avg"] = grand_ens

        history_series.loc[future_index[t]] = base_ens
        if verbose:
            print(f"[FORECAST] step {t+1}/{n_future} -> Base ensemble: {base_ens:.3f}")

    return df_future

# --------------------------- MAIN ENTRYPOINT ---------------------------

def run_models(series, y_obs=None, config=None):
    """
    Main entrypoint (used by run.py)
    Returns: df_future (DataFrame only, metrics removed)
    """
    cfg = DEFAULT_CONFIG.copy()
    if config is not None:
        cfg.update(config)

    N_LAGS = cfg["N_LAGS"]
    N_FUTURE = cfg["N_FUTURE"]
    TS_OOF_SPLITS = cfg["TS_OOF_SPLITS"]
    DO_TUNING = cfg["DO_TUNING"]
    N_ITER_RS = cfg["N_ITER_RS"]
    RANDOM_STATE = cfg["RANDOM_STATE"]
    VERBOSE = cfg["VERBOSE"]
    OUT_DIR = cfg["OUT_DIR"]

    ensure_dirs(OUT_DIR, os.path.join(OUT_DIR, "ml_models"), os.path.join(OUT_DIR, "csv"))

    # build supervised dataset
    X_lags = create_lagged_df(series, N_LAGS)
    df_super = pd.concat([series.rename("RAINFALL"), X_lags], axis=1).dropna()
    print("[MAIN] Supervised shape:", df_super.shape)

    lag_cols = [f"lag{i}" for i in range(1, N_LAGS + 1)]
    X_all_df = df_super[lag_cols]
    y_all = df_super["RAINFALL"].values

    scaler = StandardScaler()
    X_all = scaler.fit_transform(X_all_df)

    BASE_PROTOS = {
        "DT": DecisionTreeRegressor(random_state=RANDOM_STATE),
        "RF": RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1),
        "Ada": AdaBoostRegressor(random_state=RANDOM_STATE),
        "XGB": XGBRegressor(random_state=RANDOM_STATE, verbosity=0, n_jobs=-1),
        "KNN": KNeighborsRegressor(),
    }

    PARAM_DISTS = {
        "DT": {"max_depth": randint(3, 12)},
        "RF": {"n_estimators": randint(100, 500)},
        "XGB": {"n_estimators": randint(100, 800)},
        "KNN": {"n_neighbors": randint(3, 30)},
    }

    best_bases = (
        tune_base_models(X_all, y_all, BASE_PROTOS, PARAM_DISTS,
                         n_iter=N_ITER_RS, n_splits=TS_OOF_SPLITS,
                         random_state=RANDOM_STATE, verbose=VERBOSE)
        if DO_TUNING else
        {n: clone(p).fit(X_all, y_all) for n, p in BASE_PROTOS.items()}
    )

    # save base models
    joblib.dump(best_bases, os.path.join(OUT_DIR, "ml_models", "best_bases.pkl"))

    # meta models
    train_meta, base_names, allbase_meta_models, pure_meta_models, mix_meta_models = train_meta_models(
        best_bases, X_all, y_all, n_splits_oof=TS_OOF_SPLITS, verbose=VERBOSE
    )

    joblib.dump(allbase_meta_models, os.path.join(OUT_DIR, "ml_models", "allbase_meta_models.pkl"))
    joblib.dump(pure_meta_models, os.path.join(OUT_DIR, "ml_models", "pure_meta_models.pkl"))
    joblib.dump(mix_meta_models, os.path.join(OUT_DIR, "ml_models", "mix_meta_models.pkl"))

    # refit all base models
    base_full_models = {}
    for name, model in best_bases.items():
        m = clone(model)
        m.fit(X_all, y_all)
        base_full_models[name] = m
    joblib.dump(base_full_models, os.path.join(OUT_DIR, "ml_models", "base_full_models.pkl"))

    # forecast
    history_series = df_super["RAINFALL"].copy()
    df_future = recursive_forecast(
        history_series, scaler, base_full_models,
        allbase_meta_models, pure_meta_models, mix_meta_models,
        base_names, n_future=N_FUTURE, n_lags=N_LAGS, verbose=VERBOSE
    )

    out_csv = os.path.join(OUT_DIR, "csv", "forecast_all_ML_models.csv")
    df_future.to_csv(out_csv)
    if VERBOSE:
        print("[MAIN] Saved forecasts to:", out_csv)

    return df_future
