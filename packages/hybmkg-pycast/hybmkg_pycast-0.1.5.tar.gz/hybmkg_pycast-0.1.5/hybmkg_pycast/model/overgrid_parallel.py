import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm
import os

from model.stats import run_models as run_models_stats
from model.ml import run_models as run_models_ml
from model.dl import run_models as run_models_dl


def process_grid_point(i, j, data_array, config, steps, model_type):
    """Fungsi untuk memproses satu titik grid (i, j)"""
    series = data_array[:, i, j]

    # Skip grid kosong
    if np.all(np.isnan(series)):
        return i, j, None

    # Isi NaN
    series = pd.Series(series).interpolate(limit_direction="both").bfill().ffill()

    try:
        # Jalankan model sesuai tipe
        if model_type == "stats":
            result = run_models_stats(series, config, steps=steps, save_csv=False)
        elif model_type == "ml":
            result = run_models_ml(series, config, steps=steps, save_csv=False)
        elif model_type == "dl":
            result = run_models_dl(series, config, steps=steps, save_csv=False)
        else:
            raise ValueError(f"Invalid model_type: {model_type}")
        return i, j, result

    except Exception as e:
        print(f"[WARN] Grid ({i},{j}) failed: {e}")
        return i, j, None


def run_overgrid_array_parallel(data_array, config, steps=12, model_type="stats", n_jobs=-1, save_csv=False):
    """
    Versi parallel dari run_overgrid_array untuk mempercepat proses forecasting.

    Parameters
    ----------
    data_array : np.ndarray
        Array 3D [time, lat, lon]
    config : dict
        Konfigurasi model
    steps : int
        Jumlah langkah prediksi
    model_type : str
        Jenis model: 'stats', 'ml', atau 'dl'
    n_jobs : int
        Jumlah CPU core yang digunakan (-1 = semua)
    save_csv : bool
        Simpan hasil dalam format CSV (opsional)
    """

    ntime, nlat, nlon = data_array.shape
    model_keys = list(config.keys())
    forecast_data = {m: np.full((steps, nlat, nlon), np.nan) for m in model_keys}

    print(f"⚡ Parallel forecasting over {nlat}x{nlon} grid points using {model_type.upper()} models...")

    # ========================
    # Jalankan parallel loop
    # ========================
    results = Parallel(n_jobs=n_jobs, backend="loky", verbose=0)(
        delayed(process_grid_point)(i, j, data_array, config, steps, model_type)
        for i in range(nlat)
        for j in range(nlon)
    )

    # ========================
    # Gabungkan hasil
    # ========================
    for i, j, result in tqdm(results, total=len(results), desc="Combining results"):
        if result is None:
            continue
        for key in model_keys:
            if key in result and len(result[key]) == steps:
                forecast_data[key][:, i, j] = np.array(result[key])

    # ========================
    # Simpan ke CSV (opsional)
    # ========================
    if save_csv:
        result_dir = os.path.abspath("results/csv")
        os.makedirs(result_dir, exist_ok=True)
        for key in model_keys:
            arr = forecast_data[key].reshape(steps, -1)
            df = pd.DataFrame(arr)
            csv_path = os.path.join(result_dir, f"forecast_{model_type.upper()}_{key}_results.csv")
            df.to_csv(csv_path, index_label="Step")
            print(f"[✅] Forecast results saved to: {csv_path}")

    return forecast_data
