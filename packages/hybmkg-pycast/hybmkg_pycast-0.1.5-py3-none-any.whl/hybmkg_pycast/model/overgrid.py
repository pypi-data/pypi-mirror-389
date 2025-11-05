import numpy as np
import pandas as pd
from tqdm import tqdm
import os

# Import modul-model
from model.stats import run_models as run_models_stats
from model.ml import run_models as run_models_ml
from model.dl import run_models as run_models_dl


def run_overgrid_array(data_array, config, steps=12, model_type="stats", save_csv=False, outdir="results/csv"):
    """
    Jalankan forecasting untuk setiap grid (lat, lon) dalam data 3D [time, lat, lon].
    
    Parameters
    ----------
    data_array : np.ndarray
        Array 3D [time, lat, lon] berisi data deret waktu (misalnya curah hujan).
    config : dict
        Konfigurasi model (misal: parameter model atau model list).
    steps : int
        Jumlah bulan ke depan untuk prediksi.
    model_type : str
        Jenis model yang digunakan: "stats", "ml", atau "dl".
    save_csv : bool
        Jika True, hasil disimpan ke CSV per model.
    outdir : str
        Direktori penyimpanan hasil CSV.

    Returns
    -------
    forecast_data : dict
        Dictionary dengan kunci = nama model, nilai = array [steps, lat, lon]
    """

    ntime, nlat, nlon = data_array.shape
    model_keys = list(config.keys())

    forecast_data = {m: np.full((steps, nlat, nlon), np.nan) for m in model_keys}

    print(f"🌀 Running forecasts over grid: {nlat} x {nlon} points using '{model_type}' models")

    # Loop lintang & bujur
    for i in tqdm(range(nlat), desc="Latitude loop"):
        for j in range(nlon):
            series = data_array[:, i, j]

            # Skip grid kosong
            if np.all(np.isnan(series)):
                continue

            # Isi NaN dengan interpolasi
            series = pd.Series(series).interpolate(limit_direction="both").bfill().ffill()

            try:
                # Pilih model sesuai tipe
                if model_type == "stats":
                    result = run_models_stats(series, config, steps=steps, save_csv=False)
                elif model_type == "ml":
                    result = run_models_ml(series, config, steps=steps, save_csv=False)
                elif model_type == "dl":
                    result = run_models_dl(series, config, steps=steps, save_csv=False)
                else:
                    raise ValueError(f"Invalid model_type: {model_type}")

                # Simpan hasil ke dictionary output
                for key in model_keys:
                    if key in result and len(result[key]) == steps:
                        forecast_data[key][:, i, j] = np.array(result[key])

            except Exception as e:
                print(f"[WARN] Grid ({i},{j}) failed: {e}")
                continue

    # # ======================================================
    # # Simpan hasil ke CSV per model (opsional)
    # # ======================================================
    # if save_csv:
    #     os.makedirs(outdir, exist_ok=True)
    #     for key in model_keys:
    #         # Konversi hasil menjadi DataFrame (flatten grid)
    #         arr = forecast_data[key].reshape(steps, -1)
    #         df = pd.DataFrame(arr)
    #         csv_path = os.path.join(outdir, f"forecast_{model_type.upper()}_{key}_results.csv")
    #         df.to_csv(csv_path, index_label="Step")
    #         print(f"[✅] Forecast results saved to: {csv_path}")

    return forecast_data
