# === FILE: model/ml_deep.py ===
"""
Deep learning version (v2) of model/ml.py
- Unified architectures for base and meta models (meta uses same model type as selected)
- Improved architectures: stacked RNNs, compact Transformer, CNN + global pooling, deeper MLP
- Config option: "META_TYPE" to choose which model family to use as meta ("LSTM","GRU","CNN","MLP","TRANSFORMER")
- Better scaling, early stopping, and clearer saving

Requirements:
- pip install tensorflow scikit-learn joblib pandas numpy matplotlib

API: run_models(series, y_obs, config)
"""

import os
from copy import deepcopy
import joblib

import numpy as np
import pandas as pd

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score

# ---------------------- DEFAULT CONFIG ----------------------
DEFAULT_CONFIG = {
    "N_LAGS": 60,
    "N_FUTURE": 12,
    "N_TEST": 12,
    "TS_OOF_SPLITS": 4,
    "DO_TUNING": False,
    "RANDOM_STATE": 42,
    "VERBOSE": True,
    "OUT_DIR": "results",
    "PLOTS_DIR": "plots",
    "META_TYPE": "GRU",   # choose which model family to use as meta
    "TRAINING": {
        "epochs": 80,
        "batch_size": 32,
        "patience": 12,
        "validation_split": 0.12
    },
    "MODELS": {
        "LSTM": {"units": [128, 64], "dropout": 0.2},
        "GRU": {"units": [128, 64], "dropout": 0.2},
        "CNN": {"filters": 64, "kernel_size": 3, "pool_size": 2},
        "MLP": {"hidden_units": [128, 64, 32], "dropout": 0.3},
        "TRANSFORMER": {"embed_dim": 64, "num_heads": 4, "ff_dim": 128, "num_layers": 2}
    }
}

# ---------------------- UTILITIES ----------------------

def ensure_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def create_lagged_df(series, n_lags):
    cols = [series.shift(lag).rename(f"lag{lag}") for lag in range(1, n_lags + 1)]
    X = pd.concat(cols, axis=1)
    X.columns = [f"lag{lag}" for lag in range(1, n_lags + 1)]
    return X


# ---------------------- KERAS MODEL BUILDERS (UPGRADED) ----------------------

def build_lstm(input_shape, cfg):
    units = list(cfg.get("units", [128, 64]))
    dropout = float(cfg.get("dropout", 0.2))
    inp = keras.Input(shape=input_shape)
    x = inp
    # stacked LSTM: return_sequences True except last
    for i, u in enumerate(units):
        return_seq = (i < len(units) - 1)
        x = layers.LSTM(int(u), dropout=dropout, return_sequences=return_seq)(x)
    x = layers.Dense(units[-1] // 2, activation="relu")(x)
    out = layers.Dense(1)(x)
    model = keras.Model(inp, out)
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    return model


def build_gru(input_shape, cfg):
    units = list(cfg.get("units", [128, 64]))
    dropout = float(cfg.get("dropout", 0.2))
    inp = keras.Input(shape=input_shape)
    x = inp
    for i, u in enumerate(units):
        return_seq = (i < len(units) - 1)
        x = layers.GRU(int(u), dropout=dropout, return_sequences=return_seq)(x)
    x = layers.Dense(units[-1] // 2, activation="relu")(x)
    out = layers.Dense(1)(x)
    model = keras.Model(inp, out)
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    return model


def build_cnn(input_shape, cfg):
    filters = int(cfg.get("filters", 64))
    kernel_size = int(cfg.get("kernel_size", 3))
    pool_size = int(cfg.get("pool_size", 2))
    inp = keras.Input(shape=input_shape)
    x = layers.Conv1D(filters, kernel_size, activation="relu", padding="same")(inp)
    x = layers.Conv1D(filters, kernel_size, activation="relu", padding="same")(x)
    x = layers.MaxPooling1D(pool_size)(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(filters // 2, activation="relu")(x)
    out = layers.Dense(1)(x)
    model = keras.Model(inp, out)
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    return model


class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training=False):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)


def build_transformer(input_shape, cfg):
    embed_dim = int(cfg.get("embed_dim", 64))
    num_heads = int(cfg.get("num_heads", 4))
    ff_dim = int(cfg.get("ff_dim", 128))
    num_layers = int(cfg.get("num_layers", 2))
    inp = keras.Input(shape=input_shape)
    x = layers.Dense(embed_dim)(inp)
    for _ in range(num_layers):
        x = TransformerBlock(embed_dim, num_heads, ff_dim)(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(ff_dim // 2, activation="relu")(x)
    out = layers.Dense(1)(x)
    model = keras.Model(inp, out)
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    return model


def build_mlp(input_shape, cfg):
    hidden_units = list(cfg.get("hidden_units", [128, 64, 32]))
    dropout = float(cfg.get("dropout", 0.0))
    inp = keras.Input(shape=(input_shape[0],))
    x = inp
    for h in hidden_units:
        x = layers.Dense(int(h), activation="relu")(x)
        if dropout > 0:
            x = layers.Dropout(dropout)(x)
    out = layers.Dense(1)(x)
    model = keras.Model(inp, out)
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    return model


# ---------------------- OOF HELPER for Keras ----------------------

def get_oof_timeseries_keras(build_fn, build_cfg, X_vals, y_vals, n_splits=4, training_cfg=None, seed=42, verbose=0):
    tss = TimeSeriesSplit(n_splits=n_splits)
    n = X_vals.shape[0]
    oof = np.zeros(n)
    models = []
    for fold, (tr_idx, val_idx) in enumerate(tss.split(X_vals)):
        tf.keras.backend.clear_session()
        # build model per fold
        model = build_fn(X_vals.shape[1:], build_cfg) if len(X_vals.shape) > 2 else build_fn((X_vals.shape[1],), build_cfg)
        cb = [
            keras.callbacks.EarlyStopping(patience=training_cfg.get("patience", 8), restore_best_weights=True, monitor="val_loss")
        ]
        model.fit(
            X_vals[tr_idx], y_vals[tr_idx],
            validation_split=training_cfg.get("validation_split", 0.12),
            epochs=training_cfg.get("epochs", 80),
            batch_size=training_cfg.get("batch_size", 32),
            callbacks=cb,
            verbose=max(0, verbose-1)
        )
        preds = model.predict(X_vals[val_idx]).reshape(-1)
        oof[val_idx] = preds
        models.append(model)
        if verbose:
            print(f"[OOF] fold {fold+1}/{n_splits} done.")
    return oof, models


# ---------------------- META TRAINING (use same family as META_TYPE) ----------------------

def train_meta_models_keras_same_family(base_oofs, y_all, meta_type, builders, build_cfgs, training_cfg, verbose=True):
    base_names = list(base_oofs.keys())
    train_meta = np.vstack([base_oofs[n] for n in base_names]).T  # (n_samples, n_bases)

    allbase_meta_models = {}
    pure_meta_models = {}
    mix_meta_models = {}

    # choose builder for meta
    builder = builders.get(meta_type)
    build_cfg = build_cfgs.get(meta_type, {})

    if builder is None:
        raise ValueError(f"Unknown META_TYPE: {meta_type}")

    # allbase meta: train a single meta model of chosen family on full train_meta
    tf.keras.backend.clear_session()
    if meta_type == "MLP":
        model = builder((train_meta.shape[1],), build_cfg)
        fit_X = train_meta
    else:
        model = builder((train_meta.shape[1], 1), build_cfg)
        fit_X = train_meta.reshape((train_meta.shape[0], train_meta.shape[1], 1))

    model.fit(fit_X, y_all, epochs=training_cfg.get("epochs", 60), batch_size=training_cfg.get("batch_size", 32),
              validation_split=training_cfg.get("validation_split", 0.12),
              callbacks=[keras.callbacks.EarlyStopping(patience=training_cfg.get("patience", 8), restore_best_weights=True)],
              verbose=max(0, verbose-1))
    allbase_meta_models[meta_type] = model

    # pure meta: for each base oof, train a small meta of same family
    for i, base_col in enumerate(base_names):
        X_col = train_meta[:, i].reshape(-1, 1)
        tf.keras.backend.clear_session()
        if meta_type == "MLP":
            m = builder((1,), build_cfg)
            fit_X = X_col
        else:
            m = builder((1, 1), build_cfg)
            fit_X = X_col.reshape((X_col.shape[0], 1, 1))
        m.fit(fit_X, y_all, epochs=max(10, training_cfg.get("epochs", 40)), batch_size=training_cfg.get("batch_size", 32),
              validation_split=training_cfg.get("validation_split", 0.12),
              callbacks=[keras.callbacks.EarlyStopping(patience=max(4, training_cfg.get("patience", 6)), restore_best_weights=True)],
              verbose=max(0, verbose-1))
        pure_meta_models[(base_col, meta_type)] = m

    # mix meta: exclude each base and train
    for i, excluded in enumerate(base_names):
        X_mix = np.delete(train_meta, i, axis=1)
        tf.keras.backend.clear_session()
        if meta_type == "MLP":
            m = builder((X_mix.shape[1],), build_cfg)
            fit_X = X_mix
        else:
            m = builder((X_mix.shape[1], 1), build_cfg)
            fit_X = X_mix.reshape((X_mix.shape[0], X_mix.shape[1], 1))
        m.fit(fit_X, y_all, epochs=max(10, training_cfg.get("epochs", 40)), batch_size=training_cfg.get("batch_size", 32),
              validation_split=training_cfg.get("validation_split", 0.12),
              callbacks=[keras.callbacks.EarlyStopping(patience=max(4, training_cfg.get("patience", 6)), restore_best_weights=True)],
              verbose=max(0, verbose-1))
        mix_meta_models[(excluded, meta_type)] = m

    return train_meta, base_names, allbase_meta_models, pure_meta_models, mix_meta_models


# ---------------------- RECURSIVE FORECAST ----------------------

def recursive_forecast_dl(history_series, scaler, base_full_models, allbase_meta_models,
                          pure_meta_models, mix_meta_models, base_names,
                          n_future=12, n_lags=60, verbose=True):
    future_index = pd.date_range(start=history_series.index[-1] + pd.offsets.MonthBegin(1),periods=n_future, freq="MS")
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
        inp = last_vals[::-1].reshape(1, n_lags)  # (1, n_lags)
        inp_scaled = scaler.transform(inp)

        base_preds = {}
        for name, m in base_full_models.items():
            # choose input shape according to model
            if len(m.input_shape) == 3:
                X_in = inp_scaled.reshape((1, n_lags, 1))
            else:
                X_in = inp_scaled
            pred = float(m.predict(X_in).reshape(-1)[0])
            base_preds[name] = pred
            df_future.loc[future_index[t], f"Base_{name}"] = pred

        # all-base meta preds
        base_vec = np.array([base_preds[n] for n in base_names]).reshape(1, -1)
        allmeta_preds = {}
        for mname, mmodel in allbase_meta_models.items():
            if len(mmodel.input_shape) == 3:
                Xm = base_vec.reshape((1, base_vec.shape[1], 1))
            else:
                Xm = base_vec
            p = float(mmodel.predict(Xm).reshape(-1)[0])
            allmeta_preds[mname] = p
            df_future.loc[future_index[t], f"AllBaseMeta_{mname}"] = p

        # pure preds
        pure_vals = []
        for i, b in enumerate(base_names):
            single = np.array([[base_preds[b]]])
            for m in base_names:
                key = (b, b)
                if key not in pure_meta_models:
                    # fallback to any available key (if meta same for all)
                    key = next(iter(pure_meta_models))
                mdl = pure_meta_models[key]

                if len(mdl.input_shape) == 3:
                    Xs = single.reshape((1, 1, 1))
                else:
                    Xs = np.array([[base_preds[b]]])
                val = float(mdl.predict(Xs).reshape(-1)[0])
                df_future.loc[future_index[t], f"Pure_{b}->{m}"] = val
                pure_vals.append(val)

        # mix preds
        mix_vals = []
        for i, excluded in enumerate(base_names):
            feat = np.array([base_preds[n] for n in base_names if n != excluded]).reshape(1, -1)
            for m in base_names:
                if excluded == m:
                    continue
                mdl = mix_meta_models[(excluded, list(allbase_meta_models.keys())[0])]
                if len(mdl.input_shape) == 3:
                    Xm = feat.reshape((1, feat.shape[1], 1))
                else:
                    Xm = feat
                val = float(mdl.predict(Xm).reshape(-1)[0])
                df_future.loc[future_index[t], f"Mix_excl{excluded}->{m}"] = val
                mix_vals.append(val)

        # ensembles
        base_vals = np.array([base_preds[n] for n in base_names])
        base_ens = base_vals.mean()
        df_future.loc[future_index[t], "Ensemble_Base_avg"] = base_ens

        # safely aggregate meta predictions
        meta_vals = [allmeta_preds[n] for n in base_names if n in allmeta_preds]
        if len(meta_vals) > 0:
            meta_ens = np.mean(meta_vals)
        else:
            meta_ens = np.nan
            if verbose:
                print(f"[WARN] Missing meta predictions at step {t}, fallback to NaN.")
        df_future.loc[future_index[t], "Ensemble_Meta_avg"] = meta_ens


        pure_ens = np.array(pure_vals).mean() if len(pure_vals) > 0 else meta_ens
        mix_ens = np.array(mix_vals).mean() if len(mix_vals) > 0 else meta_ens
        df_future.loc[future_index[t], "Ensemble_Pure_avg"] = pure_ens
        df_future.loc[future_index[t], "Ensemble_Mix_avg"] = mix_ens

        all_ens = np.array([base_ens, meta_ens, pure_ens, mix_ens])
        grand_ens = all_ens.mean()
        df_future.loc[future_index[t], "Ensemble_Grand_avg"] = grand_ens

        # recursion: append base ensemble
        history_series.loc[future_index[t]] = base_ens

        if verbose:
            print(f"[FORECAST] step {t+1}/{n_future} -> Ensemble_Base_avg: {base_ens:.4f}")

    return df_future


# ---------------------- MAIN ENTRYPOINT ----------------------

def run_models(series, y_obs=None, config=None):
    cfg = deepcopy(DEFAULT_CONFIG)
    if config is not None:
        cfg.update(config)
        if "TRAINING" in config:
            cfg["TRAINING"].update(config["TRAINING"])
        if "MODELS" in config:
            cfg["MODELS"].update(config["MODELS"])

    N_LAGS = cfg["N_LAGS"]
    N_FUTURE = cfg["N_FUTURE"]
    N_TEST = cfg["N_TEST"]
    TS_OOF_SPLITS = cfg["TS_OOF_SPLITS"]
    META_TYPE = cfg.get("META_TYPE", "GRU")
    VERBOSE = cfg["VERBOSE"]
    OUT_DIR = cfg["OUT_DIR"]

    ensure_dirs(OUT_DIR, cfg["PLOTS_DIR"], os.path.join(OUT_DIR, "dl_models"), os.path.join(OUT_DIR, "csv"))

    # build supervised
    X_lags = create_lagged_df(series, N_LAGS)
    df_super = pd.concat([series.rename("RAINFALL"), X_lags], axis=1).dropna()
    if VERBOSE:
        print("[MAIN] Supervised shape:", df_super.shape)

    total_samples = df_super.shape[0]
    if N_TEST >= total_samples:
        raise ValueError("N_TEST must be smaller than total supervised samples")

    lag_cols = [f"lag{i}" for i in range(1, N_LAGS+1)]
    X_all_df = df_super[lag_cols].copy()
    y_all = df_super["RAINFALL"].values

    scaler = StandardScaler()
    X_all_flat = scaler.fit_transform(X_all_df.values)
    X_all_seq = X_all_flat.reshape((X_all_flat.shape[0], X_all_flat.shape[1], 1))

    # builders
    builders = {
        "LSTM": build_lstm,
        "GRU": build_gru,
        "CNN": build_cnn,
        "MLP": build_mlp,
        "TRANSFORMER": build_transformer
    }

    # generate OOF for each base model
    base_oofs = {}
    base_models_oof = {}
    for name, builder in builders.items():
        if VERBOSE:
            print(f"[OOF] Generating OOF for {name} ...")
        if name == "MLP":
            oof, models = get_oof_timeseries_keras(builders[name], cfg["MODELS"].get(name, {}), X_all_flat, y_all,
                                                  n_splits=TS_OOF_SPLITS, training_cfg=cfg["TRAINING"], seed=cfg["RANDOM_STATE"], verbose=1 if VERBOSE else 0)
        else:
            oof, models = get_oof_timeseries_keras(builders[name], cfg["MODELS"].get(name, {}), X_all_seq, y_all,
                                                  n_splits=TS_OOF_SPLITS, training_cfg=cfg["TRAINING"], seed=cfg["RANDOM_STATE"], verbose=1 if VERBOSE else 0)
        base_oofs[name] = oof
        base_models_oof[name] = models

    # Train final base models on full history
    base_full_models = {}
    for name, builder in builders.items():
        tf.keras.backend.clear_session()
        if name == "MLP":
            model = builder((X_all_flat.shape[1],), cfg["MODELS"].get(name, {}))
            model.fit(X_all_flat, y_all, epochs=max(10, cfg["TRAINING"].get("epochs", 60)), batch_size=cfg["TRAINING"].get("batch_size", 32),
                      validation_split=0.0, verbose=0)
        else:
            model = builder((X_all_seq.shape[1], 1), cfg["MODELS"].get(name, {}))
            model.fit(X_all_seq, y_all, epochs=max(10, cfg["TRAINING"].get("epochs", 60)), batch_size=cfg["TRAINING"].get("batch_size", 32),
                      validation_split=0.0, verbose=0)
        base_full_models[name] = model
        model.save(os.path.join(OUT_DIR, "dl_models", f"base_full_{name}.keras"))

    # train metas using same family as META_TYPE
    train_meta, base_names, allbase_meta_models, pure_meta_models, mix_meta_models = train_meta_models_keras_same_family(
        base_oofs, y_all, META_TYPE, builders, cfg["MODELS"], cfg["TRAINING"], verbose=VERBOSE
    )

    # save all-base meta model
    for k, m in allbase_meta_models.items():
        m.save(os.path.join(OUT_DIR, "dl_models", f"allbase_meta_{k}.keras"))

    # recursive forecast
    history_series = df_super["RAINFALL"].copy()
    df_future = recursive_forecast_dl(history_series, scaler, base_full_models,
                                      allbase_meta_models, pure_meta_models, mix_meta_models, base_names,
                                      n_future=N_FUTURE, n_lags=N_LAGS, verbose=VERBOSE)

    # save forecasts
    out_csv = os.path.join(OUT_DIR, "csv", "forecast_all_DL_models.csv")
    df_future.to_csv(out_csv)
    if VERBOSE:
        print("[MAIN] Saved forecasts to:", out_csv)

    # save scaler and config snapshot
    joblib.dump(scaler, os.path.join(OUT_DIR, "dl_models", "scaler.pkl"))

    return df_future




