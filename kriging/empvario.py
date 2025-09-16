import os
import csv
import numpy as np
from semivarlags import semivarlags
from vario import vario

# Assumes you already defined/imported:
# - semivarlags(X, Y)  -> returns (lagbins, mergedN, edges, N)
# - vario(c, Z, cl, method, options=None) -> returns (d, V, o)

def empvario(map_date_str, resid_data, depth):
    """
    EMPVARIO
    --------
    Compute the empirical semivariogram for Oklahoma state-wide soil moisture maps
    using Mesonet station data, then save the results to CSV.

    Parameters
    ----------
    map_date_str : str
        Date string formatted as 'yyyymmdd'.
    resid_data : pandas.DataFrame or dict-like
        Must provide columns/keys:
          - 'x', 'y': coordinates of Mesonet stations
          - f'resid_{depth}': residuals after regression for the target depth
    depth : int or str
        Soil moisture measurement depth in cm (used in resid_ column name and output filename).

    Returns
    -------
    d : (nc,) ndarray
        Mean distance of each lag distance class.
    V : (nc,) ndarray
        Semivariances corresponding to lag distances (for single variable).
    N_out : (k,) ndarray
        Bin counts used in output (mirrors MATLAB: this is the *mergedN* from semivarlags,
        i.e., counts for bins with > 50 elements).
    """
    # --- Load residuals for the designated depth ---
    depth_str = str(depth)
    key_resid = f"resid_{depth_str}"

    def _col(obj, name):
        # Pull a column from pandas.DataFrame or dict-like
        if hasattr(obj, "__getitem__") and name in obj:
            col = obj[name]
        elif hasattr(obj, name):
            col = getattr(obj, name)
        else:
            raise KeyError(f"Column '{name}' not found in resid_data")
        # Convert to numpy array
        try:
            return np.asarray(col, dtype=float)
        except Exception:
            # Some pandas Series with dtype 'object' might need astype
            return np.asarray(col, dtype=float)

    resids = _col(resid_data, key_resid)
    X = _col(resid_data, "x")
    Y = _col(resid_data, "y")

    # --- Exclude stations with missing residuals ---
    mask = ~np.isnan(resids)
    resids = resids[mask]
    X = X[mask]
    Y = Y[mask]

    # --- Generate lag-distance bins ---
    # semivarlags returns: lagbins, mergedN, edges, N
    lagbins, mergedN, _, _ = semivarlags(X, Y)

    # --- Calculate the empirical variogram ---
    # vario returns: d (mean distance per class), V (variogram(s)), o (pairs per class)
    d, V, _ = vario(np.column_stack((X, Y)), resids, lagbins, "kron")

    # For single variable, our vario() returns V as a 1-D array already (MATLAB-like)

    # --- Save variogram data ---
    dir_out = "../output/semivariogram/data/"
    os.makedirs(dir_out, exist_ok=True)
    file_name = os.path.join(dir_out, f"semivariogram_{depth_str}cm_{map_date_str}.csv")

    # Write header, then rows [h, gamma, n]
    with open(file_name, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["h", "gamma", "n"])
        # mergedN can be shorter than d/V if some bins were filtered;
        # In MATLAB, mergedN corresponds to lagbins constructed from bins with N>50.
        # d and V were computed on 'lagbins', so lengths should match.
        for h, g, n in zip(np.asarray(d).ravel(),
                           np.asarray(V).ravel(),
                           np.asarray(mergedN).ravel()):
            writer.writerow([f"{h:g}", f"{g:g}", f"{int(n)}"])

    return np.asarray(d), np.asarray(V), np.asarray(mergedN)