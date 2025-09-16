import numpy as np
from spherV import spherV
from exponV import exponV
_MODEL_FUNCS = {
    "spherV": spherV,
    "exponV": exponV,
}

def krig(obs, pred, beta, maxpoints, maxdist, Gmodel, Kmodel=None):
    """
    KRIG — Geospatial interpolation using simple and ordinary kriging.

    Parameters
    ----------
    obs : (m, 3) array_like
        Observed points: [X, Y, Z]
    pred : (p, 2) array_like
        Prediction points: [X, Y]
    beta : array_like
        Semivariogram model parameters [nugget, sill, range]
    maxpoints : int
        Maximum number of observed points to use per prediction
    maxdist : float
        Maximum distance from a prediction point to consider observed points
    Gmodel : str or callable
        Variogram model name ('spherV', 'exponV', etc.) or a callable b,h -> gamma
    Kmodel : str or None
        'simple' or 'ordinary' (default: 'ordinary' if None)

    Returns
    -------
    Zpred : (p, 1) ndarray
        Estimated Z at prediction points
    Vpred : (p, 1) ndarray
        Kriging variance for each prediction
    x : (p,) ndarray
        X coordinates of prediction points (echo of pred[:,0])
    y : (p,) ndarray
        Y coordinates of prediction points (echo of pred[:,1])
    """
    # ---- Memory check (mirrors MATLAB behavior) ----
    try:
        from math import isfinite  # noqa: F401
        # If you have the earlier checkmemory(pred) defined, you could call it here.
        # We'll skip hard failure—MATLAB printed an error but continued.
        # Uncomment if you want a hard stop:
        # if checkmemory(pred) == 0:
        #     print('Error: Not enough memory available. Use function "kirg_in_parts.m" instead')
    except Exception:
        pass

    if Kmodel is None:
        Kmodel = 'ordinary'

    obs = np.asarray(obs, dtype=float)
    pred = np.asarray(pred, dtype=float)
    beta = np.asarray(beta, dtype=float)

    # Remove NaNs in observed Z
    nanidx = np.isnan(obs[:, 2])

    # Observed variables
    Xobs = obs[~nanidx, 0]
    Yobs = obs[~nanidx, 1]
    Zobs = obs[~nanidx, 2]

    # Prediction points
    Xpred = pred[:, 0]
    Ypred = pred[:, 1]

    # Combine coords (pred first, then obs)
    Xall = np.concatenate([Xpred, Xobs])
    Yall = np.concatenate([Ypred, Yobs])
    n = Xall.size

    # --- Compute all pairwise distances using the same Kronecker approach as MATLAB ---
    # df = kron(ones(n,1),[Xall,Yall]) - kron([Xall,Yall],ones(n,1))
    ones_n = np.ones((n, 1))
    XY = np.column_stack((Xall, Yall))
    df = np.kron(ones_n, XY) - np.kron(XY, ones_n)  # shape: (n*n, 2)
    dall = np.sqrt(np.sum(df**2, axis=1)).reshape(n, n)

    # Distances between prediction rows and observed columns
    p = Xpred.size
    rowspred = slice(0, p)              # 0 .. p-1
    colspred = slice(p, n)              # p .. n-1 (observed)
    dpred = dall[rowspred, colspred]    # (p, n_obs)

    # Distances among observed points only
    rowsobs = slice(p, n)
    colsobs = slice(p, n)
    dobs = dall[rowsobs, colsobs]       # (n_obs, n_obs)

    # Pre-allocate outputs
    sill = beta[1]              # per MATLAB: nugget in beta(1), sill in beta(2)
    L = p
    Zpred = np.full((L, 1), np.nan, dtype=float)
    Vpred = np.full((L, 1), np.nan, dtype=float)

    # Resolve the variogram model function
    if callable(Gmodel):
        vmodel = Gmodel
    else:
        name = str(Gmodel)
        # Expect spherV, exponV defined in scope
        def vmodel(b, h):
            return globals()[name](b, h)

    # ---- Interpolation ----
    for i in range(L):
        # Sort distances from prediction i to all observed points
        dpoint = dpred[i, :]
        idxpoint = np.argsort(dpoint)

        # Observed points within maxdist
        within = idxpoint[dpoint[idxpoint] < maxdist]
        npoint = min(within.size, int(maxpoints))
        within = within[:npoint]

        if within.size == 0:
            Zpred[i, 0] = np.nan
            Vpred[i, 0] = np.nan
            continue

        pred_obs = dpred[i, within]                 # distances pred->obs (shape (npt,))
        obs_obs = dobs[np.ix_(within, within)]      # distances obs<->obs (shape (npt,npt))

        # Variogram values
        k = vmodel(beta, pred_obs)                  # shape (npt,)
        K = vmodel(beta, obs_obs)                   # shape (npt,npt)

        if Kmodel.lower() == 'simple':
            # Simple kriging
            # lambda = K \ k'
            try:
                lam = np.linalg.solve(K, k.reshape(-1, 1))  # (npt,1)
            except np.linalg.LinAlgError:
                lam = np.linalg.lstsq(K, k.reshape(-1, 1), rcond=None)[0]
            m = np.nanmean(Zobs)
            res = Zobs[within].reshape(-1, 1) - m
            Zpred[i, 0] = float(lam.T @ res + m)
            Vpred[i, 0] = float(sill - (lam.T @ k.reshape(-1, 1)))

        else:
            # Ordinary kriging
            # Augment system with ones and Lagrange multiplier
            npt = K.shape[0]
            ones_col = np.ones((npt, 1))
            K_aug = np.block([[K,        ones_col],
                              [ones_col.T, np.zeros((1, 1))]])
            k_aug = np.concatenate([k.reshape(-1, 1), np.array([[1.0]])], axis=0)

            # Solve for [lambda; mu]
            try:
                lambdamu = np.linalg.solve(K_aug, k_aug)
            except np.linalg.LinAlgError:
                lambdamu = np.linalg.lstsq(K_aug, k_aug, rcond=None)[0]

            mu = float(lambdamu[-1, 0])
            lam = lambdamu[:-1, 0].reshape(-1, 1)   # (npt,1)

            # Prediction
            Zpred[i, 0] = float((lam.T @ Zobs[within].reshape(-1, 1)))

            # Remove mu from k (MATLAB line: k = k(1,1:length(k)-1))
            # Here k was a vector; we just don't include mu in variance calc
            Vpred[i, 0] = float(k.reshape(1, -1) @ lam + mu)

    x = pred[:, 0]
    y = pred[:, 1]
    return Zpred, Vpred, x, y