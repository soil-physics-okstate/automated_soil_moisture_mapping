import numpy as np

def spherV(b, h):
    """
    SPHERV - Spherical semivariance model with nugget effect.

    Parameters
    ----------
    b : array_like
        Length-3 vector [nugget, sill, range] for the spherical model.
        nugget: semivariance at lag = 0
        sill  : plateau value (max semivariance minus nugget)
        range : distance beyond which semivariance reaches sill
    h : array_like
        Vector of lag distances.

    Returns
    -------
    G : ndarray
        Estimated semivariance for each lag value in h.

    Notes
    -----
    Mirrors the MATLAB implementation:
      G = nugget + sill * (1.5*(h/range) - 0.5*(h/range)^3) for h <= range
      G = nugget + sill for h > range
    """
    b = np.asarray(b, dtype=float)
    h = np.asarray(h, dtype=float)

    nugget, sill, rang = b

    # Base spherical model
    G = nugget + sill * (1.5 * (h / rang) - 0.5 * (h / rang) ** 3)

    # For lags beyond range, semivariance is nugget + sill
    mask = h > rang
    G[mask] = nugget + sill

    return G