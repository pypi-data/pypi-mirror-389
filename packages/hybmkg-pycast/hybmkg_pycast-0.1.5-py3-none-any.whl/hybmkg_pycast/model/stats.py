import numpy as np
import pandas as pd
import os
import pywt
import warnings
from itertools import product
from sklearn.metrics import mean_squared_error

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from pmdarima import auto_arima
from simpful import FuzzySystem, LinguisticVariable, FuzzySet, Triangular_MF

warnings.filterwarnings("ignore")


# ==============================================================
# Utility Functions
# ==============================================================

def forecast_model(model_obj, steps=12):
    """Fit and forecast using statsmodels-compatible model."""
    fitted = model_obj.fit()
    y_forecast = fitted.forecast(steps=steps)
    return y_forecast, fitted

# ==============================================================
# Main Runner
# ==============================================================

def run_models(series, config, steps=12, forecast_index=None, save_csv=True):
    """Run complete suite of statistical + fuzzy forecasting models."""
    results = {}

    # ========== ARIMA FAMILY ==========
    try:
        model_ar = ARIMA(series, **config["AR"])
        results["AR"], _ = forecast_model(model_ar, steps)
    except Exception:
        results["AR"] = np.repeat(np.nan, steps)

    try:
        model_ma = ARIMA(series, **config["MA"])
        results["MA"], _ = forecast_model(model_ma, steps)
    except Exception:
        results["MA"] = np.repeat(np.nan, steps)

    try:
        model_arma = ARIMA(series, **config["ARMA"])
        results["ARMA"], _ = forecast_model(model_arma, steps)
    except Exception:
        results["ARMA"] = np.repeat(np.nan, steps)

    try:
        model_sarima = SARIMAX(series, **config["SARIMA"])
        results["SARIMA"], _ = forecast_model(model_sarima, steps)
    except Exception:
        results["SARIMA"] = np.repeat(np.nan, steps)

    try:
        model_sarimax = SARIMAX(series, **config["SARIMAX"])
        results["SARIMAX"], _ = forecast_model(model_sarimax, steps)
    except Exception:
        results["SARIMAX"] = np.repeat(np.nan, steps)

    try:
        auto_model = auto_arima(series, **config["AUTO_ARIMA"])
        results["AUTO_ARIMA"] = auto_model.predict(n_periods=steps)
    except Exception:
        results["AUTO_ARIMA"] = np.repeat(np.nan, steps)


    # ========== WAVELET–ARIMA ==========
    try:
        coeffs = pywt.wavedec(series, wavelet="db4", level=2)
        reconstructed = []
        for c in coeffs:
            model = ARIMA(c, order=(1, 0, 0))
            fitted = model.fit()
            fc = fitted.forecast(steps=steps)
            reconstructed.append(fc)
        wavelet_arima = np.sum([np.pad(fc, (0, max(0, steps - len(fc)))) for fc in reconstructed], axis=0)
        results["WAVELET_ARIMA"] = wavelet_arima[:steps]
    except Exception:
        results["WAVELET_ARIMA"] = np.repeat(np.nan, steps)

    # ========== ANFIS (Universal Stable Version) ==========
    try:
        data = np.asarray(series, dtype=float)
        data = pd.Series(data).interpolate(limit_direction="both").bfill().ffill().values

        data_min, data_max = np.min(data), np.max(data)
        if np.isclose(data_min, data_max):
            # Jika datanya konstan (flat)
            results["ANFIS"] = np.repeat(data[-1], steps)
        else:
            # Normalisasi ke 0–1
            norm = (data - data_min) / (data_max - data_min)

            # Tentukan slope/tren rata-rata terakhir
            trend = np.mean(np.diff(norm[-6:])) if len(norm) >= 6 else 0.0

            # Membership function sederhana (tanpa dependency simpful)
            def fuzz_low(x): return max(0.0, 1 - 2 * x)
            def fuzz_med(x): return max(0.0, 1 - abs(2 * x - 1))
            def fuzz_high(x): return max(0.0, 2 * x - 1)

            # Bobot awal
            w_low, w_med, w_high = 0.8, 1.0, 1.2

            # Training ringan (delta rule)
            lr = 0.01
            for t in range(1, len(norm)):
                x = norm[t - 1]
                y_true = norm[t]
                mu_l, mu_m, mu_h = fuzz_low(x), fuzz_med(x), fuzz_high(x)
                denom = mu_l + mu_m + mu_h + 1e-6
                y_pred = (w_low * mu_l * 0.2 + w_med * mu_m * 0.5 + w_high * mu_h * 0.8) / denom
                err = y_true - y_pred
                w_low += lr * err * mu_l
                w_med += lr * err * mu_m
                w_high += lr * err * mu_h

            # Forecast iteratif
            x = norm[-1]
            forecast_norm = []
            for _ in range(steps):
                mu_l, mu_m, mu_h = fuzz_low(x), fuzz_med(x), fuzz_high(x)
                denom = mu_l + mu_m + mu_h + 1e-6
                y_pred = (w_low * mu_l * 0.2 + w_med * mu_m * 0.5 + w_high * mu_h * 0.8) / denom
                y_pred = np.clip(y_pred, 0, 1)
                forecast_norm.append(y_pred)
                x = y_pred + 0.3 * trend  # sedikit mengikuti tren

            forecast = np.array(forecast_norm) * (data_max - data_min) + data_min
            results["ANFIS"] = forecast

    except Exception as e:
        print(f"[WARN] ANFIS failed safely: {e}")
        results["ANFIS"] = np.repeat(enso_series.iloc[-1], steps)


# ========== WAVELET–ANFIS (Balanced Reconstruction) ==========
    config_wavelet_anfis = config.get("WAVELET_ANFIS", {})
    if config_wavelet_anfis.get("enabled", False):
        try:
            wavelet = config_wavelet_anfis.get("wavelet", "db4")
            level = config_wavelet_anfis.get("level", 2)
            ar_order = config_wavelet_anfis.get("ar_order", 3)
            weight_mode = config_wavelet_anfis.get("weight_mode", "energy")
            denoise = config_wavelet_anfis.get("denoise", False)
            trend_factor = config_wavelet_anfis.get("trend_factor", 0.3)

            coeffs_w = pywt.wavedec(series, wavelet=wavelet, level=level)
            energies = [np.sum(np.abs(c)) for c in coeffs_w]
            total_energy = np.sum(energies)
            if weight_mode == "sqrt":
                weights = [np.sqrt(e) / np.sum(np.sqrt(energies)) for e in energies]
            elif weight_mode == "equal":
                weights = [1/len(coeffs_w)] * len(coeffs_w)
            else:  # default energy
                weights = [e / total_energy for e in energies]

            wavelet_anfis = np.zeros(steps)

            def ar_forecast(series, steps, p=ar_order):
                y = np.asarray(series, dtype=float)
                if len(y) <= p:
                    return np.repeat(y[-1], steps)
                X = np.column_stack([y[p - k - 1:len(y) - k - 1] for k in range(p)])
                y_target = y[p:]
                coef, *_ = np.linalg.lstsq(X, y_target, rcond=None)
                last_vals = list(y[-p:])
                preds = []
                for _ in range(steps):
                    xvec = np.array(last_vals[-p:][::-1])
                    nextv = xvec.dot(coef)
                    preds.append(nextv)
                    last_vals.append(nextv)
                return np.array(preds)

            for i, c in enumerate(coeffs_w):
                c = np.asarray(c, dtype=float)
                if denoise and i > 0:
                    thr = np.std(c) * np.sqrt(2 * np.log(len(c)+1))
                    c = pywt.threshold(c, thr, mode='soft')

                if np.allclose(c, c[0]):
                    sub_forecast = np.repeat(c[-1], steps)
                else:
                    c_demean = c - np.mean(c)
                    sub_forecast = ar_forecast(c_demean, steps, p=ar_order) + np.mean(c)
                
                wavelet_anfis += weights[i] * (sub_forecast + trend_factor * np.mean(np.diff(c[-6:])))

            wavelet_anfis = np.interp(
                wavelet_anfis,
                (np.min(wavelet_anfis), np.max(wavelet_anfis)),
                (np.min(series), np.max(series))
            )

            results["WAVELET_ANFIS"] = wavelet_anfis

        except Exception as e:
            print("[WARN] Wavelet–ANFIS failed:", e)
            results["WAVELET_ANFIS"] = np.repeat(np.nan, steps)


    # ========== ENSEMBLE MEAN ==========
    df_future = pd.DataFrame(results, index=forecast_index)
    df_future["ENSEMBLE"] = df_future.mean(axis=1, skipna=True)

    # ========== SAVE OUTPUT ==========
    if save_csv:
        result_dir = os.path.abspath("results/csv")
        os.makedirs(result_dir, exist_ok=True)
        csv_path = os.path.join(result_dir, "forecast_STATS_results.csv")
        df_future.to_csv(csv_path, index_label="Date")
        print(f"[✅] Forecast results saved to: {csv_path}")

    return df_future
