from numba import njit
import numpy as np
from plotconfigs import n_perts, num_y, num_x

def calc_LPMM(data, delta=5):
    """Helper function to pass information to the jitted LPMM function. Since numba
    does not allow the axis argument in np.mean(), compute that here and pass out to
    the primary jitted function.

    Parameters
    ----------
    data : np.array
        Ensemble member data at a fixed timed. PxMxN array where P = number of members
    delta : int
        Radius--in grid points--over which to calculate the LPMM. Default=5

    Returns
    -------
    lpmm : np.array
        Localized Probability-Matched Mean (MxN)
    """
    mean = np.mean(data, axis=0)
    return _LPMM(mean, data, delta)

@njit
def _LPMM(mean, data, delta):
    """Compute the Localized Probability-Matched Mean following _[1]

    Parameters
    ----------
    mean : np.array
        Ensemble mean as an MxN array. Numba doesn't handle axis argument in np.mean().
    data : np.array
        Ensemble member data at a fixed time. PxMxN array where P = number of members
    delta : int
        Radius--in grid points--over which to calculate the LPMM

    Returns
    -------
    lpmm : np.array
        Localized Probability-Matched Mean (MxN)
    """

    n_grids = ((delta * 2) + 1)**2
    lpmm = np.zeros((num_y, num_x))
    for j in range(delta, num_y-delta):
        for i in range(delta, num_x-delta):
            mean_rank = np.zeros(n_grids)
            member_rank = np.zeros(n_grids*n_perts)
            grid_knt = 0
            member_knt = 0
            for jj in range(-1*delta,delta+1):
                for ii in range(-1*delta,delta+1):
                    mean_rank[grid_knt] = mean[j+jj,i+ii]
                    for pert in range(n_perts):
                        member_rank[member_knt] = data[pert,j+jj,i+ii]
                        member_knt += 1
                    grid_knt += 1
            mean_rank = sorted(mean_rank)
            member_rank = sorted(member_rank)
            r_mean = mean_rank.index(mean[j,i])
            r_ens = n_perts * r_mean
            lpmm[j,i] = member_rank[r_ens]
    return lpmm
