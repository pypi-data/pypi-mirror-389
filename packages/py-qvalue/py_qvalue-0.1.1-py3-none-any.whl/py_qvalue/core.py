import numpy as np
from scipy import special
from scipy.stats import gaussian_kde
from scipy.interpolate import UnivariateSpline
from typing import Optional, Tuple, Union, List, Dict, Any

def qvalue(p: np.ndarray, fdr_level: Optional[float] = None, pfdr: bool = False,
           lfdr_out: bool = True, pi0: Optional[float] = None,
           **kwargs) -> Dict[str, Any]:
    """
    Calculate q-values for a given set of p-values using Storey's method.

    Parameters:
    -----------
    p : np.ndarray
        Array of p-values
    fdr_level : float, optional
        False discovery rate level for determining significant results
    pfdr : bool, default=False
        Whether to calculate the positive false discovery rate
    lfdr_out : bool, default=True
        Whether to calculate local false discovery rates
    pi0 : float, optional
        Optional estimate of the proportion of true null hypotheses
    **kwargs : additional arguments passed to pi0est and lfdr functions

    Returns:
    --------
    dict : Dictionary containing q-values and related statistics
    """

    # Argument checks
    p_in = p.copy()
    qvals_out = np.full_like(p, np.nan)
    lfdr_out_arr = np.full_like(p, np.nan)

    rm_na = ~np.isnan(p)
    p = p[rm_na]

    if np.min(p) < 0 or np.max(p) > 1:
        raise ValueError("p-values not in valid range [0, 1].")
    if fdr_level is not None and (fdr_level <= 0 or fdr_level > 1):
        raise ValueError("'fdr_level' must be in (0, 1].")

    # Calculate pi0 estimate
    if pi0 is None:
        pi0s = pi0est(p, **kwargs)
    else:
        if pi0 > 0 and pi0 <= 1:
            pi0s = {'pi0': pi0}
        else:
            raise ValueError("pi0 must be in (0,1]")

    # Calculate q-value estimates
    m = len(p)
    i = np.arange(m, 0, -1)
    o = np.argsort(p)[::-1]  # indices sorted in descending order
    ro = np.argsort(o)       # reverse order indices
    if pfdr:
        qvals = pi0s['pi0'] * np.minimum(1, np.minimum.accumulate(
            p[o] * m / (i * (1 - (1 - p[o]) ** m))))
    else:
        qvals = pi0s['pi0'] * np.minimum(1, np.minimum.accumulate(p[o] * m / i))

    qvals = qvals[ro]
    qvals_out[rm_na] = qvals

    # Calculate local FDR estimates
    if lfdr_out:
        lfdr_vals = lfdr(p=p, pi0=pi0s['pi0'], **kwargs)
        lfdr_out_arr[rm_na] = lfdr_vals
    else:
        lfdr_out_arr = None

    # Prepare return dictionary
    result = {
        'pi0': pi0s.get('pi0'),
        'qvalues': qvals_out,
        'pvalues': p_in,
        'lfdr': lfdr_out_arr,
    }

    # Add additional pi0 estimation details if available
    for key in ['pi0_lambda', 'lambda', 'pi0_smooth']:
        if key in pi0s:
            result[key] = pi0s[key]

    if fdr_level is not None:
        result['fdr_level'] = fdr_level
        result['significant'] = (qvals_out <= fdr_level)

    return result


def pi0est(p: np.ndarray, lambda_: Optional[np.ndarray] = None,
           pi0_method: str = "smoother", smooth_df: int = 3,
           smooth_log_pi0: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Estimate the proportion of true null hypotheses (pi0).

    Parameters:
    -----------
    p : np.ndarray
        Array of p-values
    lambda_ : np.ndarray, optional
        Lambda values for pi0 estimation
    pi0_method : str, default="smoother"
        Method for estimating pi0 ("smoother" or "bootstrap")
    smooth_df : int, default=3
        Degrees of freedom for smoother
    smooth_log_pi0 : bool, default=False
        Whether to smooth on log scale

    Returns:
    --------
    dict : Dictionary containing pi0 estimate and related values
    """
    if lambda_ is None:
        lambda_ = np.arange(0.05, 0.96, 0.05)

    m = len(p)
    pi0 = np.zeros_like(lambda_, dtype=float)

    for i, l in enumerate(lambda_):
        pi0[i] = np.mean(p >= l) / (1 - l)

    pi0_lambda = np.minimum(pi0.copy(), 1.0)
    pi0_smooth: Optional[np.ndarray] = None

    if pi0_method == "smoother":
        if smooth_log_pi0:
            pi0 = np.log(pi0)

        spline = UnivariateSpline(lambda_, pi0, k=smooth_df)
        pi0_smooth = spline(lambda_)

        if smooth_log_pi0:
            pi0_smooth = np.exp(pi0_smooth)

        pi0_value = float(np.minimum(1, pi0_smooth[-1]))
    elif pi0_method == "bootstrap":
        min_pi0 = np.min(pi0)
        W = np.array([np.sum(p >= l) for l in lambda_])
        mse = (W / (m**2 * (1 - lambda_)**2)) * (1 - W/m) + (pi0 - min_pi0)**2
        pi0_value = float(min(1, pi0[np.argmin(mse)]))
    else:
        raise ValueError("pi0_method must be 'smoother' or 'bootstrap'")

    return {
        'pi0': pi0_value,
        'pi0_lambda': pi0_lambda,
        'lambda': lambda_,
        'pi0_smooth': pi0_smooth
    }


def lfdr(p: np.ndarray, pi0: float, trunc: bool = True, monotone: bool = True,
         transf: str = "probit", adj: float = 1.5, eps: float = 1e-8,
         **kwargs) -> np.ndarray:
    """
    Estimate local false discovery rates (lfdr).

    Parameters:
    -----------
    p : np.ndarray
        Array of p-values
    pi0 : float
        Proportion of true null hypotheses
    trunc : bool, default=True
        Whether to truncate lfdr values at pi0
    monotone : bool, default=True
        Whether to enforce monotonicity
    transf : str, default="probit"
        Transformation for p-values ("probit" or "log")
    adj : float, default=1.5
        Adjustment factor for bandwidth
    eps : float, default=1e-8
        Small value to avoid numerical issues

    Returns:
    --------
    np.ndarray : Array of local false discovery rates
    """
    p = np.clip(p, eps, 1 - eps)  # Avoid extreme values

    if transf == "probit":
        x = -np.sqrt(2) * special.erfinv(2 * p - 1)
    elif transf == "log":
        x = -np.log(p)
    else:
        raise ValueError("transf must be 'probit' or 'log'")

    # Kernel density estimation
    kde = gaussian_kde(x, bw_method='scott')
    dens = kde.evaluate(x)
    # Theoretical null density
    if transf == "probit":
        null_dens = np.exp(-x**2 / 2) / np.sqrt(2 * np.pi)
    else:  # log
        null_dens = np.exp(-x)

    lfdr = pi0 * null_dens / dens

    if trunc:
        lfdr = np.minimum(lfdr, 1)

    if monotone:
        o = np.argsort(p)
        lfdr[o] = np.minimum.accumulate(lfdr[o])

    return lfdr
