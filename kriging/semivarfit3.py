import os
import csv
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from spherV import spherV 
from exponV import exponV

# Assumes the model functions are already defined/imported:
#   - spherV(b, h)
#   - exponV(b, h)


def semivarfit3(d, V, N, map_date_str, depth):
    """
    SEMIVARFIT3 fits and compares variogram models to empirical variograms.

    Parameters
    ----------
    d : array_like
        Mean distance of each lag distance class (shape: (m,))
    V : array_like
        Empirical semivariances corresponding to the lag distances (shape: (m,))
    N : array_like
        Number of elements/pairs in each bin (shape: (m,))
    map_date_str : str
        Date string 'yyyymmdd' to embed in output filenames
    depth : int or str
        Depth in cm (only used in filenames/labels)

    Returns
    -------
    model : str
        Name of the chosen model ('spherV' or 'exponV')
    param : ndarray
        Fitted parameters [nugget, sill, range] for the chosen model

    Side Effects
    ------------
    - Saves a PNG plot of empirical variogram and fitted models to:
        ../output/semivariogram/plots/semivariogram_{depth}cm_{map_date_str}.png
    - Saves a CSV with the chosen model on the first line, and the parameters on the second line to:
        ../output/semivariogram/model/model_{depth}cm_{map_date_str}.csv
    """
    d = np.asarray(d, dtype=float).ravel()
    V = np.asarray(V, dtype=float).ravel()
    N = np.asarray(N, dtype=float).ravel()
    depth_str = str(depth)

    # Models to compare (Gaussian removed per original notes)
    modelnamesgeo = ['spherV', 'exponV']

    # Initial guesses: [nugget, sill, range]
    # MATLAB: [min(V), range(V)/2, mean(d)], where range(V) = max(V)-min(V)
    vmin = np.nanmin(V)
    vmax = np.nanmax(V)
    vptp = vmax - vmin
    param0 = np.array([vmin, vptp / 2.0, np.nanmean(d)], dtype=float)

    # Bounds
    # lb = [0 0 0], ub = [max(V) max(V) 10*max(d)]
    lb = np.array([0.0, 0.0, 0.0], dtype=float)
    ub = np.array([vmax, vmax, 10.0 * np.nanmax(d)], dtype=float)

    # Helper to evaluate a named model
    def _eval_model(name, b, h):
        if name == 'spherV':
            return spherV(b, h)
        elif name == 'exponV':
            return exponV(b, h)
        else:
            raise ValueError(f"Unknown model '{name}'")

    # Fit each model using least squares with bounds, weighting residuals by N
    paramlist = []
    MSE = np.full(len(modelnamesgeo), np.nan, dtype=float)

    for i, mname in enumerate(modelnamesgeo):
        # Residuals weighted by N (mirrors (model - V) .* N)
        def residuals(b):
            return (_eval_model(mname, b, d) - V) * N

        res = least_squares(residuals, x0=param0, bounds=(lb, ub), verbose=0)
        paramlist.append(res.x)
        # res.cost = 0.5 * sum(residuals**2), so SSE = 2*cost
        sse = 2.0 * res.cost
        MSE[i] = sse / d.size

    # Choose the model with minimum weighted MSE
    model_idx = int(np.nanargmin(MSE))
    param = np.asarray(paramlist[model_idx], dtype=float)
    model = modelnamesgeo[model_idx]

    # ---- Plot empirical variograms and fitted models (invisible figure -> just save) ----
    os.makedirs("../output/semivariogram/plots/", exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.ravel()

    for i, mname in enumerate(modelnamesgeo):
        ax = axes[i]
        ax.set_fontsize = 14  # keep compatibility; we'll set sizes via labels/ticks
        ax.plot(d, V, 'ok', label='Empirical')
        k_alt = _eval_model(mname, np.asarray(paramlist[i], dtype=float), d)
        ax.plot(d, k_alt, '--b', label=mname)
        ax.set_xlabel('Lag distance (m)', fontsize=14)
        ax.set_ylabel(r'Semivariance ((cm$^{-3}$ cm$^{3}$)$^{2}$)', fontsize=14)
        ax.set_title(mname, fontsize=14)
        ax.tick_params(axis='both', labelsize=12)
        ax.legend(frameon=False)

    # If there are unused subplots (since we have 2 models), hide them
    for j in range(len(modelnamesgeo), len(axes)):
        axes[j].axis('off')

    fig.tight_layout()
    plot_path = f"../output/semivariogram/plots/semivariogram_{depth_str}cm_{map_date_str}.png"
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)

    # ---- Save model name and parameters to CSV ----
    os.makedirs("../output/semivariogram/model/", exist_ok=True)
    csv_path = f"../output/semivariogram/model/model_{depth_str}cm_{map_date_str}.csv"
    with open(csv_path, mode="w", newline="") as f:
        # First line: model name (like MATLAB fprintf then dlmwrite append)
        f.write(f"{model}\n")
        writer = csv.writer(f)
        writer.writerow([f"{param[0]:g}", f"{param[1]:g}", f"{param[2]:g}"])

    return model, param