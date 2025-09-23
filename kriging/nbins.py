import numpy as np

def nbins(X):
    """
    NBINS Determines the optimal number of regularly spaced histogram bins.

    Parameters
    ----------
    X : array_like
        Random variable as a 1-D column vector (any 1-D array is fine).

    Returns
    -------
    D : int
        Optimal number of bins.
    N : ndarray
        Counts per bin (for the optimal D).
    edges : ndarray
        Bin boundaries mapped to the range of X (mirrors MATLAB code behavior).

    Notes
    -----
    Adapted from Birgé and Rozenholc (2006): "How many bins should be put in a regular
    histogram", ESAIM: Probability and Statistics, Vol. 10, pp. 24–45.
    Logic mirrors the provided MATLAB implementation, including:
      - Rescaling X to [0, 1]
      - Trying D = 1..round(n/log n)
      - Computing L = sum_j N_j * log(D * N_j / n)
      - Penalty: D - 1 + (log D)^2.5
      - Merging the last two bins and dropping the last, as in the original script
      - Returning 'edges' after rescaling them to [min(X), max(X)]
    """
    x = np.asarray(X, dtype=float).ravel()
    n = x.size
    if n < 2:
        # Degenerate case: with <2 samples, default to 1 bin
        D = 1
        return D, np.array([n], dtype=int), np.array([np.min(x), np.max(x)], dtype=float)

    # --- Helpers to match MATLAB behavior ---
    def _rescale_to_unit(z):
        # Mimics rescalevar(z, 0, 1) first output
        z = np.asarray(z, dtype=float)
        zmin = np.min(z)
        zmax = np.max(z)
        if zmax == zmin:
            return np.zeros_like(z)  # all same value -> all zeros in [0,1]
        return (z - zmin) / (zmax - zmin)

    def _rescale_from_unit(z_unit, a, b):
        # Linear map from [0,1] to [a,b]
        return a + (b - a) * np.asarray(z_unit, dtype=float)

    # Anonymous functions from the paper / MATLAB
    # LogL(D, N, n) = sum_j N_j * log(D * N_j / n)
    def _logL(D, N, n_):
        N = np.asarray(N, dtype=float)
        # Avoid log(0) by masking zeros (0*log(0) is defined as 0 in this context)
        mask = N > 0
        return float(np.sum(N[mask] * np.log(D * N[mask] / n_)))

    def _pen(D):
        return (D - 1) + (np.log(D) ** 2.5)

    # 1) Rescale X into [0,1]
    Xn = _rescale_to_unit(x)

    # 2) Candidate number of bins
    Dmax = int(np.rint(n / np.log(n))) if n > 1 else 1
    Dmax = max(Dmax, 1)
    Dvec = np.arange(1, Dmax + 1, dtype=int)

    Lpen = np.full(Dmax, np.nan, dtype=float)
    N_list = [None] * Dmax
    edges_list = [None] * Dmax

    for idx, D in enumerate(Dvec):
        # I = floor(D * Xn) + 1  (bin indices, MATLAB-style 1..D+1)
        I = np.floor(D * Xn).astype(int) + 1

        # Unique bin labels present
        C = np.unique(I)

        # Count how many values fall into each present bin
        # (recompute per loop; don't carry counts over iterations)
        counts = np.array([(I == c).sum() for c in C], dtype=int)

        # Merge last two bins: counts[-2] += counts[-1], then drop the last
        if counts.size >= 2:
            counts[-2] += counts[-1]
            counts = counts[:-1]

        N_list[idx] = counts
        edges_list[idx] = C  # store the present bin labels before rescaling

        # Log-likelihood and penalization
        L = _logL(D, counts, n)
        penalty = _pen(D)
        Lpen[idx] = L - penalty

    # 3) Pick D that maximizes penalized likelihood
    Iopt = int(np.nanargmax(Lpen))
    Dopt = int(Dvec[Iopt])

    # 4) Prepare outputs
    counts_opt = np.asarray(N_list[Iopt], dtype=int)
    C_opt = np.asarray(edges_list[Iopt], dtype=float)

    # Rescale "edges" to [min(X), max(X)] as in MATLAB via rescalevar(edges, min(X), max(X))
    # First map C_opt into [0,1] using its own min/max (to mimic rescalevar behavior),
    # then to [xmin, xmax].
    if C_opt.size == 1:
        # Degenerate: single edge -> replicate to form boundaries
        edges_scaled = np.array([np.min(x), np.max(x)], dtype=float)
    else:
        C_unit = _rescale_to_unit(C_opt)
        edges_scaled = _rescale_from_unit(C_unit, np.min(x), np.max(x))

    return Dopt, counts_opt, edges_scaled