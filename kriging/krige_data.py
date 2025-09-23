# krige_data.py
# Usage:
#   python krige_data.py 2024-04-18 25
#
# Steps (mirrors MATLAB krige_data.m):
#  0) (Optional) add geostats toolbox folder to path
#  1) Load grid
#  2) Load residuals for date
#  3) Build empirical semivariogram
#  4) Fit theoretical semivariogram model
#  5) Krige to predict on grid (and save outputs)

import os
import sys
import argparse
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.io import loadmat

# --------- Required functions (assumed available in your project) ----------
# If these live in separate modules, import them instead of defining here:
# from geostats_toolbox.empvario import empvario
# from geostats_toolbox.semivarfit3 import semivarfit3
# from geostats_toolbox.smmkriging import smmkriging
#
# Below we assume you've already pasted/defined these earlier in your codebase:
from empvario import empvario            # returns (d, V, N) and saves semivariogram data CSV
from semivarfit3 import semivarfit3      # returns (model, param) and saves plots/model CSV
from smmkriging import smmkriging        # returns krigResult and saves outputs

# ---------------------------------------------------------------------------

def _find_grid_xy_from_mat(matdict):
    """Best-effort loader to extract x,y from a MATLAB .mat grid file."""
    # direct fields
    if 'x' in matdict and 'y' in matdict:
        return matdict['x'], matdict['y']

    # search for a struct with fields x,y
    for k, v in matdict.items():
        if k.startswith("__"):
            continue
        # MATLAB structs often come as object arrays with dtype=object or np.void
        if isinstance(v, np.ndarray):
            # Case: scalar struct -> array with dtype=object, shape () or (1,1)
            if v.dtype.names:  # structured dtype
                names = v.dtype.names
                if 'x' in names and 'y' in names:
                    x = v['x'].squeeze()
                    y = v['y'].squeeze()
                    return x, y
            # Case: nested cell/struct; try to dig a bit
            if v.size == 1 and hasattr(v, 'item'):
                try:
                    vv = v.item()
                    if isinstance(vv, dict) and 'x' in vv and 'y' in vv:
                        return vv['x'], vv['y']
                except Exception:
                    pass
    raise KeyError("Could not find 'x' and 'y' in the provided .mat grid file.")


def _to_column_vector(a):
    """Flatten any array to a 1-D column-like vector (preserve MATLAB intent)."""
    arr = np.asarray(a).squeeze()
    # If it's a 2D grid mesh, you likely want every point; flatten:
    return arr.ravel(order='F')  # column-major flatten to mimic MATLAB memory order


def krige_data(map_date_str, depth):
    """
    Python equivalent of MATLAB krige_data.m

    Parameters
    ----------
    map_date_str : str
        Date string like '2024-04-18' (will be converted to 'yyyymmdd' for filenames).
    depth : int or str
        Depth in cm, e.g., 5, 25, 60. Used to select 'resid_{depth}' column.

    Returns
    -------
    krigResult : ndarray of shape (n, 4)
        Columns: x, y, Z (prediction), Zvar (kriging variance).
    """
    # ---- STEP 0: (Optional) add geostats toolbox to path (only if you keep your functions there) ----
    spt_path = './geostats_toolbox/'
    if os.path.isdir(spt_path) and spt_path not in sys.path:
        sys.path.append(spt_path)

    # ---- STEP 1: Load the grid to be kriged upon ----
    grid_mat_path = '../static_data/grid/soil_moisture_grid.mat'
    if not os.path.exists(grid_mat_path):
        raise FileNotFoundError(f"Grid .mat not found: {grid_mat_path}")
    grid_mat = loadmat(grid_mat_path)
    gx_raw, gy_raw = _find_grid_xy_from_mat(grid_mat)
    grid = {
        'x': _to_column_vector(gx_raw).astype(float),
        'y': _to_column_vector(gy_raw).astype(float),
    }

    # ---- STEP 2: Load the residuals to be kriged ----
    # Convert input date to 'yyyymmdd'
    try:
        dt = datetime.strptime(map_date_str, "%Y-%m-%d")
    except ValueError:
        # Accept already-compact strings too
        try:
            dt = datetime.strptime(map_date_str, "%Y%m%d")
        except ValueError:
            raise ValueError("map_date_str must be 'YYYY-MM-DD' or 'YYYYMMDD'")

    map_date_compact = dt.strftime("%Y%m%d")

    resid_data_dir = '../dynamic_data/regression/residual/'
    resid_csv = os.path.join(resid_data_dir, f"resid_{map_date_compact}.csv")
    if not os.path.exists(resid_csv):
        raise FileNotFoundError(f"Residual data file not found: {resid_csv}")
    resid_data = pd.read_csv(resid_csv)

    # ---- STEP 3: Create empirical semivariogram for the chosen depth ----
    d, V, N = empvario(map_date_compact, resid_data, str(depth))

    # ---- STEP 4: Fit theoretical semivariogram model ----
    model, param = semivarfit3(d, V, N, map_date_compact, str(depth))

    # ---- STEP 5: Interpolate volumetric water content using kriging ----
    krigResult = smmkriging(grid, map_date_compact, resid_data, str(depth), model, param)

    return krigResult


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python krige_data.py YYYY-MM-DD depth(cm)")
        sys.exit(1)

    date_arg = sys.argv[1]   # e.g., "2024-04-18"
    depth_arg = sys.argv[2]  # e.g., "25"

    result = krige_data(date_arg, depth_arg)

    print(f"Kriging completed for date={date_arg}, depth={depth_arg} cm.")
    print(f"Predictions: {result.shape[0]} rows written to ../output/kriging_residual/")
    print(f"Semivariogram data saved to ../output/semivariogram/data/")
    print(f"Model & plot saved to ../output/semivariogram/model/ and ../output/semivariogram/plots/")
    print(f"Cross-validation RMSE saved to ../output/kriging_cross_validation/")