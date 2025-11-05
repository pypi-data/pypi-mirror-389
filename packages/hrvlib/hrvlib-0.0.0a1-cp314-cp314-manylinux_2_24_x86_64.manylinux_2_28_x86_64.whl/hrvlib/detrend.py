import numpy as np
import scipy
from hrvlib._core import detrend as detrend

def detrend_og(rr: np.ndarray, lambada: int = 10) -> np.ndarray:
    """Apply detrending to RR intervals."""
    T = len(rr)
    I = np.identity(T)
    D2 = scipy.sparse.spdiags(
        np.array([np.ones(T), np.repeat(-2, T), np.ones(T)]),
        np.array([0, 1, 2]),
        T - 2,
        T
    ).toarray()

    z_stat1 = I + lambada ** 2 * D2.T @ D2
    z_stat2 = I - np.linalg.inv(z_stat1)

    return z_stat2 @ rr

def detrend_sparse(rr: np.ndarray, lambada: int = 10) -> np.ndarray:
    """
    Apply detrending to RR intervals using sparse matrices for memory efficiency.

    Memory optimization: Uses sparse matrices throughout instead of dense T×T matrices.
    For a 2-hour session (7200 intervals), this saves ~1GB of memory.
    """
    T = len(rr)
    # Use sparse identity matrix instead of dense (saves T×T×8 bytes)
    I = scipy.sparse.identity(T, format='csr')

    # Keep D2 as sparse matrix (don't convert to dense array)
    D2 = scipy.sparse.spdiags(
        np.array([np.ones(T), np.repeat(-2, T), np.ones(T)]),
        np.array([0, 1, 2]),
        T - 2,
        T,
        format='csr'
    )

    # Perform operations in sparse format
    D2TD2 = D2.T @ D2
    z_stat1 = I + lambada ** 2 * D2TD2

    # Solve sparse linear system instead of computing inverse
    # This is both faster and more memory efficient
    z_stat2_rr = scipy.sparse.linalg.spsolve(z_stat1, rr)

    return rr - z_stat2_rr
