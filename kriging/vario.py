import numpy as np
import math

# Optional: only used when plotting is requested (options[0] == 1)
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def vario(c, Z, cl, method, options=None):
    """
    Multivariate variogram / cross-variogram estimation.

    Parameters
    ----------
    c : (n, d) array_like
        Coordinates of n locations in d-dimensional space.
    Z : (n, nv) array_like
        Values for nv variables at the same n locations.
    cl : (nc+1,) array_like
        Class limits for the distance bins (open on left, closed on right).
        Must be sorted; cl[0] >= 0.
    method : {"kron", "loop"}
        - "kron": use Kronecker products (fast for small n, memory heavy).
        - "loop":  pairwise loops (slower, low memory).
    options : None or array_like
        If None -> treated as [0] (no plotting).
        If length 1: options[0] == 1 turns plotting on.
        If length 3: options = [plot_flag, min_angle_deg, max_angle_deg] (only for 2D coords).
            Angles use same convention as the original MATLAB (range [-90, 90] degrees).

    Returns
    -------
    d : (nc,) ndarray
        Mean distance of pairs in each distance class (NaN where empty).
    V : list[list[ndarray]] or (nc,) ndarray
        Variograms/cross-variograms per class:
          - If nv > 1: V is an nv x nv nested list, each element an (nc,) ndarray.
          - If nv == 1: V is a single (nc,) ndarray.
    o : (nc,) ndarray
        Number of pairs in each distance class.

    Notes
    -----
    This mirrors the behavior of the provided MATLAB function, including:
    - Angle filtering only when 2D coordinates and options length is 3.
    - In "kron" mode, distances/products are computed for all (i,j) pairs,
      then divided by 2 to correct the double counting.
    - In "loop" mode, only i<j pairs are considered; normalization follows MATLAB.
    - Plotting (if options[0] == 1) produces an nv x nv grid of subplots.
    """

    if not isinstance(method, str):
        raise ValueError("method should be a char string")

    c = np.asarray(c, dtype=float)
    Z = np.asarray(Z, dtype=float)
    cl = np.sort(np.asarray(cl, dtype=float))

    if cl[0] < 0:
        raise ValueError("Minimum class distance must be >= 0")

    n, d = c.shape
    nv = Z.shape[1] if Z.ndim > 1 else 1
    if Z.ndim == 1:
        Z = Z.reshape(-1, 1)

    nc = cl.size - 1
    minim = cl[0]
    maxim = cl[-1]

    # options handling
    if options is None:
        options = [0]
    options = np.asarray(options).ravel()
    noptions = options.size

    use_angles = (noptions == 3)
    if use_angles:
        if d != 2:
            raise ValueError("Angle limits are specified only for planar (2D) coordinates")
        a = float(options[1]) * 2 * math.pi / 360.0
        b = float(options[2]) * 2 * math.pi / 360.0
        if (a == b) or (min(a, b) < -math.pi / 2) or (max(a, b) > math.pi / 2):
            raise ValueError("Angle limits must be different and between or equal to -90 and 90 degrees")

    # initialize V container
    V = [[np.zeros(nc, dtype=float) for _ in range(nv)] for _ in range(nv)]

    if method == "kron":
        # --- Kronecker product approach (may be memory heavy) ---

        unit = np.ones((n, 1))
        # Differences for all pairs: shape (n*n, d)
        dc = np.kron(unit, c) - np.kron(c, unit)

        # Distances (n*n,)
        if dc.shape[1] == 1:
            dist = np.abs(dc[:, 0])
        else:
            dist = np.sqrt(np.sum(dc**2, axis=1))

        # Angles (only if requested)
        if use_angles:
            ang = np.zeros(dist.shape, dtype=float)
            dc1 = dc[:, 0]
            dc2 = dc[:, 1]
            zero_mask = (dc1 == 0)
            ang[zero_mask] = (math.pi / 2.0) * np.sign(dc2[zero_mask])
            nz = ~zero_mask
            ang[nz] = np.arctan(dc2[nz] / dc1[nz])

        # Select couples within distance/angle constraints
        cond = (dist > max(0.0, minim)) & (dist <= maxim)
        if use_angles:
            conda = (ang > a)
            condb = (ang <= b)
            if a < b:
                cond = cond & (conda & condb)
            else:
                cond = cond & (conda | condb)

        dist_f = dist[cond]
        m = dist_f.size
        if m == 0:
            raise ValueError("No couples of values within the specified classes")

        # Build class membership
        isclass = [None] * nc
        d_out = np.full(nc, np.nan, dtype=float)
        o = np.zeros(nc, dtype=int)

        for k in range(nc):
            cls_mask = (dist_f > cl[k]) & (dist_f <= cl[k + 1])
            idxs = np.flatnonzero(cls_mask)
            isclass[k] = idxs
            # In the Kronecker approach, pairs are double counted -> divide by 2
            o[k] = idxs.size // 2
            if o[k] != 0:
                d_out[k] = np.sum(dist_f[idxs]) / (2.0 * o[k])

        # Variograms / cross-variograms
        for i in range(nv):
            zi = Z[:, i]
            dzi = np.kron(unit, zi.reshape(-1, 1)) - np.kron(zi.reshape(-1, 1), unit)
            dzi = dzi.ravel()

            for j in range(i, nv):
                zj = Z[:, j]
                dzj = np.kron(unit, zj.reshape(-1, 1)) - np.kron(zj.reshape(-1, 1), unit)
                dzj = dzj.ravel()

                product = (dzi * dzj)[cond]
                v = np.full(nc, np.nan, dtype=float)
                for k in range(nc):
                    if o[k] != 0:
                        v[k] = np.sum(product[isclass[k]]) / (4.0 * o[k])  # 4 = 2 (double count) * 2 (semivariogram)
                V[i][j] = v
                if i != j:
                    V[j][i] = v

    else:
        # --- Loop approach (i<j pairs only) ---

        d_out = np.zeros(nc, dtype=float)
        o = np.zeros(nc, dtype=int)
        # Initialize V to zeros (already done above)

        for i1 in range(n):
            for j1 in range(i1 + 1, n):
                dc_vec = c[i1, :] - c[j1, :]
                dist = float(np.sqrt(np.sum(dc_vec**2)))
                cond = (dist > max(0.0, minim)) & (dist <= maxim)

                if use_angles:
                    # Only for first two components (planar)
                    if dc_vec[0] == 0:
                        ang = (math.pi / 2.0) * np.sign(dc_vec[1])
                    else:
                        ang = math.atan(dc_vec[1] / dc_vec[0])
                    conda = (ang > a)
                    condb = (ang <= b)
                    if a < b:
                        cond = cond & (conda & condb)
                    else:
                        cond = cond & (conda | condb)

                if cond:
                    # MATLAB: index = sum(dist > cl); if 1 <= index <= nc, it belongs to that class
                    index = int(np.sum(dist > cl))
                    if 1 <= index <= nc:
                        k = index - 1  # zero-based
                        d_out[k] += dist
                        o[k] += 1
                        for k1 in range(nv):
                            for l1 in range(k1, nv):
                                V[k1][l1][k] += (Z[i1, k1] - Z[j1, k1]) * (Z[i1, l1] - Z[j1, l1])

        # Normalize
        for i_k in range(nc):
            if o[i_k] == 0:
                d_out[i_k] = np.nan
                for j in range(nv):
                    for k in range(j, nv):
                        V[j][k][i_k] = np.nan
                        V[k][j][i_k] = np.nan
            else:
                d_out[i_k] = d_out[i_k] / o[i_k]
                for j in range(nv):
                    for k in range(j, nv):
                        V[j][k][i_k] = V[j][k][i_k] / (2.0 * o[i_k])
                        V[k][j][i_k] = V[j][k][i_k]

    # Plot if requested
    plot_flag = (options.size >= 1 and int(options[0]) == 1)
    if plot_flag:
        if plt is None:
            print("Plotting requested but matplotlib is unavailable.")
        else:
            # Create nv x nv grid of subplots
            fig, axes = plt.subplots(nv, nv, squeeze=False, figsize=(3 * nv, 3 * nv))
            max_d = np.nanmax(d_out) if np.any(~np.isnan(d_out)) else 1.0
            for i in range(nv):
                for j in range(nv):
                    ax = axes[i][j]
                    vij = V[i][j]
                    # Determine y-limits similar to MATLAB logic
                    minV = np.nanmin(vij) if np.any(~np.isnan(vij)) else 0.0
                    maxV = np.nanmax(vij) if np.any(~np.isnan(vij)) else 0.0
                    ymin = min(0.0, -1.1 * np.sign(minV) * minV)  # gives -1.1*|minV|
                    ymax = max(0.0,  1.1 * np.sign(maxV) * maxV)  # gives  1.1*|maxV|
                    ax.plot(d_out, vij, ".", markersize=4)
                    ax.axhline(0.0, linestyle=":", linewidth=1)
                    ax.set_xlim(0.0, max_d if np.isfinite(max_d) else 1.0)
                    if np.isfinite(ymin) and np.isfinite(ymax) and ymin != ymax:
                        ax.set_ylim(ymin, ymax)
                    ax.set_xlabel("Distance", fontsize=8)
                    ax.set_ylabel("Variogram", fontsize=8)
                    ax.set_title(f"Couple {i+1}-{j+1}", fontsize=8)
                    ax.tick_params(axis='both', labelsize=6)
            fig.tight_layout()

    # If only one variable, return vector for V (like MATLAB)
    if nv == 1:
        V_out = V[0][0]
    else:
        V_out = V

    # Warning if any empty classes
    if np.any(np.isnan(d_out)):
        print("Warning: some distance classes do not contain pairs of points")

    return d_out, V_out, o