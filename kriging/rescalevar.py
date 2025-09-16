import numpy as np

def rescalevar(x, *args):
    """
    RESCALEVAR re-scales a given vector/matrix to a new desired range, or recovers original values.

    Syntax
    ------
    xscaled, xpar = rescalevar(x, newmin, newmax)
        Re-scale each column to range [newmin, newmax].

    xscaled, xpar = rescalevar(x, newminmax)
        First row represents the new minimum values for each column in x,
        second row must contain the new maximum values for each column in x.

    N = rescalevar(xscaled, xpar)
        Recover original values.

    Parameters
    ----------
    x : ndarray
        Input array.
    newmin : float or ndarray, optional
        New minimum value (scalar) or per-column min array.
    newmax : float or ndarray, optional
        New maximum value (scalar) or per-column max array.
    newminmax : ndarray, optional
        2 x n array: first row = newmin per column, second row = newmax per column.

    Returns
    -------
    xscaled : ndarray
        Rescaled array.
    xpar : ndarray
        Array with original column min and max in first and second row.
    """
    x = np.array(x, dtype=float)

    if len(args) == 0 or len(args) > 2:
        raise ValueError(f"Input arguments must be two or three. You had {1 + len(args)} input arguments")

    # Case 1: One argument - 2 x n array [newmin; newmax]
    if len(args) == 1 and np.ndim(args[0]) == 2 and args[0].shape[0] == 2 and args[0].shape[1] == x.shape[1]:
        newmin = np.tile(args[0][0, :], (x.shape[0], 1))
        newmax = np.tile(args[0][1, :], (x.shape[0], 1))

    # Case 2: Two arguments - scalar newmin, scalar newmax
    elif len(args) == 2 and np.size(args[0]) == 1 and np.size(args[1]) == 1:
        newmin = np.ones_like(x) * args[0]
        newmax = np.ones_like(x) * args[1]
    else:
        raise ValueError("Invalid argument combination.")

    # Original max and min
    xmax = np.max(x, axis=0)
    xmin = np.min(x, axis=0)
    xpar = np.vstack([xmin, xmax])

    # Expand to match shape
    xmax = np.tile(xmax, (x.shape[0], 1))
    xmin = np.tile(xmin, (x.shape[0], 1))

    # Scaling formula
    xscaled = (newmax - newmin) / (xmax - xmin) * (x - xmax) + newmax

    return xscaled, xpar