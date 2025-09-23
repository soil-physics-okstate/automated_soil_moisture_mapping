import numpy as np
from krig import krig
# Assumes you already have `krig` defined/imported and your variogram models
# (e.g., spherV/exponV) available to `krig`.

def crossvalidation(obs, beta, maxpoints, maxdist, Gmodel=None, Kmodel=None):
    """
    CROSSVALIDATION — Leave-one-out cross validation using kriging.

    Parameters
    ----------
    obs : (n, 3) array_like
        Columns: x, y, z (observations).
    beta : array_like
        Semivariogram parameters [nugget, sill, range].
    maxpoints : int
        Max observed points used per prediction.
    maxdist : float
        Max neighbor distance for kriging.
    Gmodel : str or callable, optional
        Variogram model name ('spherV', 'exponV', ...) or callable (b, h) -> gamma.
        Defaults to 'spherV' if not provided (to mirror MATLAB behavior when 4 args).
    Kmodel : str, optional
        'ordinary' (default) or 'simple'.

    Returns
    -------
    RMSE : float
        Root mean squared error (raw values).
    RMSEn : float
        Normalized RMSE = RMSE / range(z).
    RMSEz : float
        RMSE on z-scores (standardized values).
    """
    obs = np.asarray(obs, dtype=float)
    if Gmodel is None:
        Gmodel = 'spherV'
    if Kmodel is None:
        Kmodel = 'ordinary'

    # --- Helpers to mimic MATLAB zscore/std behavior (uses ddof=1) ---
    def _nanmean(a):
        return np.nanmean(a)

    def _nanstd(a, ddof=1):
        return np.nanstd(a, ddof=ddof)

    def _zscore(a):
        m = _nanmean(a)
        s = _nanstd(a, ddof=1)
        # Avoid divide-by-zero
        if not np.isfinite(s) or s == 0.0:
            return np.zeros_like(a)
        return (a - m) / s

    # =========================
    # LOOCV on raw observations
    # =========================
    pred = obs[:, :2]           # prediction points at station locations
    Zpred_list = []

    for i in range(pred.shape[0]):
        predTemp = pred[i, :].reshape(1, 2)
        obsTemp = np.delete(obs, i, axis=0)  # remove the ith observation
        ZpredTemp, _VpredTemp, _x, _y = krig(obsTemp, predTemp, beta, maxpoints, maxdist, Gmodel, Kmodel)
        Zpred_list.append(np.asarray(ZpredTemp, dtype=float).ravel()[0])

    Zpred_arr = np.asarray(Zpred_list, dtype=float)
    z_obs = obs[:, 2]

    # RMSE
    RMSE = np.sqrt(np.nanmean((Zpred_arr - z_obs) ** 2))

    # Normalized RMSE: divide by range of observed z
    z_range = np.nanmax(z_obs) - np.nanmin(z_obs)
    RMSEn = RMSE / z_range if np.isfinite(z_range) and z_range != 0 else np.nan

    # ==============================
    # LOOCV on standardized z-scores
    # ==============================
    obs_z = obs.copy()
    obs_z[:, 2] = _zscore(obs[:, 2])

    pred = obs_z[:, :2]
    Zpred_list_z = []

    for i in range(pred.shape[0]):
        predTemp = pred[i, :].reshape(1, 2)
        obsTemp = np.delete(obs_z, i, axis=0)
        ZpredTemp, _VpredTemp, _x, _y = krig(obsTemp, predTemp, beta, maxpoints, maxdist, Gmodel, Kmodel)
        Zpred_list_z.append(np.asarray(ZpredTemp, dtype=float).ravel()[0])

    Zpred_arr_z = np.asarray(Zpred_list_z, dtype=float)
    # Note: MATLAB re-applies zscore to the (already standardized) obs(:,3) here.
    # We mirror that behavior exactly:
    RMSEz = np.sqrt(np.nanmean((Zpred_arr_z - _zscore(obs_z[:, 2])) ** 2))

    return RMSE, RMSEn, RMSEz