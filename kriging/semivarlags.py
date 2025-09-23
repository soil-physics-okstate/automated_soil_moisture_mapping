import numpy as np
from nbins import nbins

def semivarlags(X, Y):
    """
    SEMIVARLAGS estimates the number of bins and bin boundaries to create empirical semivariograms.

    Parameters
    ----------
    X : array_like
        Column vector with spatial coordinates in the X direction.
    Y : array_like
        Column vector with spatial coordinates in the Y direction.

    Returns
    -------
    lagbins : ndarray
        Edges of bins with more than 50 elements (in terms of pairwise distances).
    mergedN : ndarray
        Number of elements in each merged bin (where original bin count > 50).
    edges : ndarray
        Bin 'edges' from nbins (including those with < 50 elements), mapped to the range of distances.
    N : ndarray
        Number of elements in each bin (including those with < 50 elements).

    Notes
    -----
    - Mirrors the MATLAB implementation:
        * Removes NaNs in X or Y.
        * Forms the pairwise Euclidean distance matrix and uses the lower triangle.
        * Calls nbins(hcloud) to select the optimal regular binning.
        * Merges bins by threshold N > 50 to define lagbins and mergedN.
    - Assumes a Python implementation of `nbins` is available in scope.
    """
    X = np.asarray(X, dtype=float).ravel()
    Y = np.asarray(Y, dtype=float).ravel()

    # Eliminate NaNs in either X or Y
    mask = ~np.isnan(X) & ~np.isnan(Y)
    X = X[mask]
    Y = Y[mask]
    n = X.size

    if n == 0:
        # Degenerate: no data
        return (np.array([], dtype=float),
                np.array([], dtype=int),
                np.array([], dtype=float),
                np.array([], dtype=int))

    # --- Compute Euclidean distances between all pairs (lower triangle only) ---
    # Equivalent to MATLAB:
    # df = kron(ones(n,1),[X,Y]) - kron([X,Y],ones(n,1));
    # d = sqrt(sum(df.^2,2));
    # d = reshape(d,n,n);
    # loweridx = logical(tril(ones(size(d)),-1));
    # hcloud = d(loweridx);
    dx = X[:, None] - X[None, :]
    dy = Y[:, None] - Y[None, :]
    d = np.sqrt(dx * dx + dy * dy)

    # Take strict lower triangle (exclude diagonal)
    lower_idx = np.tril_indices(n, k=-1)
    hcloud = d[lower_idx]

    if hcloud.size == 0:
        # Only one point -> no pairwise distances
        return (np.array([], dtype=float),
                np.array([], dtype=int),
                np.array([], dtype=float),
                np.array([], dtype=int))

    # --- Find optimal number of bins using nbins ---
    # Expecting nbins to return: D, N, edges
    _, N, edges = nbins(hcloud)  # nbins must be defined/imported elsewhere

    # Sort distances and compute cumulative counts to locate bin edges
    sortedh = np.sort(hcloud)
    N = np.asarray(N, dtype=int)

    # Select bins with > 50 elements
    idx = N > 50
    csN = np.cumsum(N)
    csNidx = csN[idx]

    # In MATLAB: lagbins = sortedh([1 csNidx]);
    # Convert to 0-based: indices [0] + (csNidx - 1)
    if csNidx.size > 0:
        lag_indices = np.concatenate(([0], csNidx - 1))
    else:
        # If none exceed threshold, still follow MATLAB pattern: use first element
        lag_indices = np.array([0], dtype=int)
    lagbins = sortedh[lag_indices]

    # mergedN = (csNidx - [0 csNidx(1:end-1)])'
    if csNidx.size > 0:
        prev = np.concatenate(([0], csNidx[:-1]))
        mergedN = (csNidx - prev).astype(int)
    else:
        mergedN = np.array([], dtype=int)

    return lagbins, mergedN, edges, N