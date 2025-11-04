# 🌦️ hybmkg-pycast

hybmkg-pycast is a hybrid machine learning and deep learning framework for climate and weather forecasting.
It is designed to integrate multiple forecasting approaches — from classical statistical models to modern deep learning architectures — and support research and operational applications at BMKG (Meteorological, Climatological, and Geophysical Agency of Indonesia).

# 🚀 Key Features

### Comprehensive Forecasting Models

Statistical: ARIMA, SARIMA, ANFIS, Wavelet-ARIMA, Wavelet-ANFIS, etc.

Machine Learning: Random Forest, XGBoost, LightGBM, SVR, KNN, MLP using multi-stacked approach.

Deep Learning: RNN, LSTM, GRU, CNN, Transformer, and hybrid approaches using multi-stacked approach.

### Flexible Data Input

Supports both NetCDF and CSV formats for climate and environmental datasets.

### Hybrid Framework

Combine traditional time series models with machine learning and deep learning methods for improved forecast accuracy.

### Visualization and Evaluation

Built-in utilities for plotting time series, model diagnostics, and forecast verification (correlation, RMSE, R²).

### Project-Oriented Directory Structure

hybmkg_pycast/

├── config/      # JSON configuration files

├── data/        # Input data (CSV, NetCDF)

├── model/       # Model scripts (statistical, ML, DL)

├── plots/       # Generated plots (PNG)

├── results/     # Output results (CSV, trained models)

├── run_all.ipynb

├── hybmkg_pycast.yaml  # Conda environment specification

# 🧩 Installation

### You can install the package using pip:

_pip install hybmkg-pycast_


### Or from source:

_git clone https://github.com/yourusername/hybmkg_pycast.git_

_cd hybmkg_pycast_

_pip install ._


### If you prefer Conda, use the provided environment file:

_conda env create -f hybmkg_pycast.yaml_

_conda activate hybmkg_pycast_


# 📊 Applications

Seasonal and sub-seasonal climate forecasting

ENSO (El Niño–Southern Oscillation) prediction

Rainfall variability and extreme events analysis

Climate change impact studies

# 👥 Authors and Acknowledgment

Developed by researchers at BMKG to support data-driven climate prediction and research collaboration.

# 📄 License

This project is licensed under the **MIT License.**
