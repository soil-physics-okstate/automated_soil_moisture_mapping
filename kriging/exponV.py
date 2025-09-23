import numpy as np

def exponV(b, h):
    """
    EXPONV - Exponential semivariance model with nugget effect.

    Parameters
    ----------
    b : array_like
        Length-3 vector [nugget, sill, range] for the exponential model.
        nugget: semivariance at lag = 0
        sill  : maximum semivariance minus nugget
        range : distance scaling parameter
    h : array_like
        Vector of lag distances.

    Returns
    -------
    G : ndarray
        Estimated semivariance for each lag value in h.

    Notes
    -----
    Mirrors MATLAB's:
        G = nugget + sill * (1 - exp(-3*h/range))
    """
    b = np.asarray(b, dtype=float)
    h = np.asarray(h, dtype=float)

    nugget, sill, rang = b
    G = nugget + sill * (1.0 - np.exp(-3.0 * h / rang))

    return G