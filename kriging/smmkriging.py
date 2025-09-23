import os
import csv
import warnings
import numpy as np
from krig_in_parts import krig_in_parts
from crossvalidation import crossvalidation


# Assumes the following functions are already defined/imported in your environment:
#   - krig_in_parts(obs, pred, beta, maxpoints, maxdist, Gmodel, Kmodel)
#   - crossvalidation(obs, beta, maxpoints, maxdist, Gmodel, Kmodel)

def smmkriging(grid, map_date_str, resid_data, depth, model, param):
    """
    smmkriging
    ----------
    Orchestrates kriging for statewide soil moisture mapping:
      1) Prepare inputs
      2) Kriging (in parts)
      3) Cross-validation
      4) Export CSVs

    Parameters
    ----------
    grid : object or mapping
        Must provide attributes/keys 'x' and 'y' for grid coordinates.
    map_date_str : str
        Date string in 'yyyymmdd' format.
    resid_data : object or mapping
        Must provide 'x', 'y', and f"resid_{depth}".
    depth : str or int
        Depth in cm (used to select residual column and to name outputs).
    model : str or callable
        Variogram model name ('spherV', 'exponV', ...) or a callable (b, h) -> gamma.
    param : array_like
        Variogram parameters [nugget, sill, range].

    Returns
    -------
    krigResult : (n, 4) ndarray
        Columns: x, y, Z (prediction), Zvar (kriging variance).
    """
    warnings.filterwarnings("ignore")  # mirror MATLAB's warning('off','all')

    # ----- 1. Set up inputs for kriging -----
    depth_str = str(depth)

    def _col(obj, name):
        if hasattr(obj, "__getitem__") and name in obj:
            return np.asarray(obj[name], dtype=float)
        if hasattr(obj, name):
            return np.asarray(getattr(obj, name), dtype=float)
        raise KeyError(f"Required field '{name}' not found.")

    # get data
    zVar = _col(resid_data, f"resid_{depth_str}")
    mesX = _col(resid_data, "x")
    mesY = _col(resid_data, "y")

    # remove missing data
    mask = ~np.isnan(zVar)
    zVar = zVar[mask]
    mesX = mesX[mask]
    mesY = mesY[mask]
    obs = np.column_stack([mesX, mesY, zVar])  # [x, y, z]

    # get grid
    gridX = _col(grid, "x").astype(float)
    gridY = _col(grid, "y").astype(float)
    pred = np.column_stack([gridX, gridY])     # [x, y] for predictions

    # set kriging parameters
    beta = np.asarray(param, dtype=float)  # [nugget, sill, range]
    maxpoints = 10
    maxdist = 200000.0
    Gmodel = model
    Kmodel = "ordinary"

    # ----- 2. Kriging -----
    Zpred, Vpred, x, y = krig_in_parts(obs, pred, beta, maxpoints, maxdist, Gmodel, Kmodel)
    krigResult = np.column_stack([x, y, Zpred, Vpred])

    # ----- 3. Cross validation -----
    RMSE, RMSEn, RMSEz = crossvalidation(obs, beta, maxpoints, maxdist, Gmodel, Kmodel)
    os.makedirs("../output/kriging_cross_validation/", exist_ok=True)
    rmse_path = f"../output/kriging_cross_validation/rmse_{depth_str}cm_{map_date_str}.csv"
    with open(rmse_path, mode="w", newline="") as f:
        f.write(f"{RMSE:g}")

    # ----- 4. Export data -----
    os.makedirs("../output/kriging_residual/", exist_ok=True)
    out_path = f"../output/kriging_residual/kriged_{depth_str}cm_{map_date_str}.csv"
    headers = ["x", "y", "Z", "Zvar"]

    # write header
    with open(out_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # write data
        for row in krigResult:
            writer.writerow([f"{row[0]:g}", f"{row[1]:g}", f"{row[2]:g}", f"{row[3]:g}"])

    return krigResult