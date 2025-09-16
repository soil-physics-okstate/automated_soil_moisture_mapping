import numpy as np
from krig import krig

def krig_in_parts(obs, pred, beta, maxpoints, maxdist, Gmodel, Kmodel=None):
    """
    KRIG_IN_PARTS — Piece-wise geospatial interpolation using simple and ordinary kriging.

    Parameters
    ----------
    obs : (m, 3) array_like
        Observed points: columns [X, Y, Z].
    pred : (p, 2) array_like
        Prediction grid points: columns [X, Y].
    beta : array_like
        Semivariogram parameters [nugget, sill, range].
    maxpoints : int
        Maximum number of observed points to use per prediction.
    maxdist : float
        Maximum distance threshold for observed points considered per prediction.
    Gmodel : str or callable
        Variogram model ('spherV', 'exponV', ...) or a callable (b, h) -> gamma.
    Kmodel : str or None
        'simple' or 'ordinary' (default 'ordinary' if None).

    Returns
    -------
    Zpred : (q,) ndarray
        Predicted Z values at grid coordinates (after de-duplicating overlaps).
    Vpred : (q,) ndarray
        Kriging variances corresponding to Zpred (after de-duplicating overlaps).
    x : (q,) ndarray
        X coordinates of prediction points (after de-duplicating overlaps).
    y : (q,) ndarray
        Y coordinates of prediction points (after de-duplicating overlaps).

    Notes
    -----
    Mirrors the MATLAB logic:
      - Break prediction grid into ~100 contiguous chunks using linspace and rounding.
      - Call `krig` on each chunk and accumulate results.
      - Concatenate [Zpred, Vpred, x, y] and remove duplicate rows caused by chunk boundaries.
    """
    pred = np.asarray(pred, dtype=float)
    gridX = pred[:, 0]
    gridY = pred[:, 1]

    # Make ~100 chunk boundaries, mimicking MATLAB: parts = round(linspace(1, length(pred), 100))
    n = pred.shape[0]
    if n == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])

    # 0-based indices in Python; ensure inclusive end like MATLAB slices
    parts = np.round(np.linspace(0, n - 1, 100)).astype(int)
    # Guarantee first and last are correct
    parts[0] = 0
    parts[-1] = n - 1

    Zpred_all = []
    Vpred_all = []
    xy_all = []

    for i in range(len(parts) - 1):
        start = parts[i]
        end = parts[i + 1]

        # MATLAB uses parts(i):parts(i+1) inclusive; Python slices are exclusive at end -> add +1
        sl = slice(start, end + 1)
        chunk_xy = np.column_stack([gridX[sl], gridY[sl]])

        # Call krig on this chunk (expects krig to be defined/imported)
        tZpred, tVpred, _, _ = krig(obs, chunk_xy, beta, maxpoints, maxdist, Gmodel, Kmodel)

        # Ensure 1-D for concatenation like MATLAB columns
        Zpred_all.append(np.asarray(tZpred, dtype=float).ravel())
        Vpred_all.append(np.asarray(tVpred, dtype=float).ravel())
        xy_all.append(chunk_xy)

    # Concatenate results
    Zpred_all = np.concatenate(Zpred_all, axis=0)
    Vpred_all = np.concatenate(Vpred_all, axis=0)
    xy_all = np.vstack(xy_all)

    # Combine and remove duplicate rows (like MATLAB unique(..., 'rows'))
    krigResult = np.column_stack([Zpred_all, Vpred_all, xy_all])
    krigResult_unique = np.unique(krigResult, axis=0)

    Zpred = krigResult_unique[:, 0]
    Vpred = krigResult_unique[:, 1]
    x = krigResult_unique[:, 2]
    y = krigResult_unique[:, 3]

    return Zpred, Vpred, x, y