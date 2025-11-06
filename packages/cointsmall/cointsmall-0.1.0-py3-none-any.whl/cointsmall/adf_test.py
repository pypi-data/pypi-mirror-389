"""
Augmented Dickey-Fuller Test Module

Performs ADF test on regression residuals with automatic lag selection
based on serial correlation testing using the Breusch-Godfrey test.

Based on Trinh (2022), Section 2, page 4.
"""

import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.diagnostic import acorr_breusch_godfrey
import warnings


class ADFTestResult:
    """
    Container for ADF test results.
    
    Attributes
    ----------
    statistic : float
        ADF test statistic (t-statistic for gamma)
    lag : int
        Selected number of lags
    model : statsmodels OLS result
        Fitted ADF regression model
    """
    
    def __init__(self, statistic, lag, model):
        self.statistic = statistic
        self.lag = lag
        self.model = model
    
    def __str__(self):
        return (
            "\nAugmented Dickey-Fuller Test\n"
            "============================\n"
            f"Test Statistic: {self.statistic:.4f}\n"
            f"Lags: {self.lag}\n"
        )
    
    def __repr__(self):
        return f"ADFTestResult(statistic={self.statistic:.4f}, lag={self.lag})"


def adf_test_residuals(residuals, max_lags=None):
    """
    Perform ADF test on residuals with automatic lag selection.
    
    Following Trinh (2022, page 4): "We only consider the Augmented Dickey-Fuller 
    (ADF) version of the test for its relative efficiency in very small sample, 
    in which we select the minimal number of lags for which the residuals of the 
    ADF model are not serially correlated."
    
    The ADF regression is: Δε_t = γ*ε_{t-1} + Σ φ_i*Δε_{t-i} + error
    The test statistic is: t = γ_hat / SE(γ_hat)
    
    Parameters
    ----------
    residuals : array-like
        Regression residuals to test for unit root.
    max_lags : int, optional
        Maximum number of lags to consider. If None, uses
        min(12*(T/100)^0.25, (T-1)/3).
    
    Returns
    -------
    ADFTestResult
        Object containing test statistic, selected lag, and fitted model.
    
    References
    ----------
    Trinh, J. (2022). Testing for cointegration with structural changes in very 
    small sample. THEMA Working Paper n°2022-01, Section 2, page 4.
    
    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(123)
    >>> residuals = np.cumsum(np.random.randn(50) * 0.1)
    >>> result = adf_test_residuals(residuals)
    >>> print(result.statistic)
    >>> print(result.lag)
    """
    residuals = np.asarray(residuals).flatten()
    n = len(residuals)
    
    if n < 10:
        raise ValueError("At least 10 observations required for ADF test")
    
    if max_lags is None:
        # Standard rule: min(12*(T/100)^0.25, (T-1)/3)
        max_lags = int(min(np.floor(12 * (n/100)**0.25), np.floor((n-1)/3)))
    
    if max_lags >= n - 3:
        max_lags = max(0, n - 10)
    
    # Try lags from 0 upwards until no serial correlation
    for lag in range(max_lags + 1):
        # First difference of residuals
        d_resid = np.diff(residuals)
        n_diff = len(d_resid)
        
        if lag == 0:
            # ADF without lags: Δε_t = γ*ε_{t-1} + error
            y_lag = residuals[:-1]
            X = y_lag.reshape(-1, 1)
            y = d_resid
            
        else:
            # ADF with lags: Δε_t = γ*ε_{t-1} + Σ φ_i*Δε_{t-i} + error
            # Build lag matrix
            lag_matrix = np.zeros((n_diff, lag))
            for i in range(1, lag + 1):
                if i < n_diff:
                    lag_matrix[i:, i-1] = d_resid[:-i]
            
            # Combine with lagged level
            y_lag = residuals[:-1]
            X = np.column_stack([y_lag, lag_matrix])
            y = d_resid
            
            # Remove rows with NaN (from lagged differences)
            valid_idx = lag  # First 'lag' rows have NaN
            X = X[valid_idx:]
            y = y[valid_idx:]
            
            if len(y) < lag + 3:
                continue  # Not enough observations
        
        # Fit model
        try:
            model = OLS(y, X).fit()
        except Exception as e:
            warnings.warn(f"OLS failed for lag {lag}: {e}")
            continue
        
        # Test for serial correlation using Breusch-Godfrey test
        if lag > 0 and len(model.resid) > lag + 2:
            try:
                bg_result = acorr_breusch_godfrey(model, nlags=1)
                # bg_result is (lm_statistic, lm_pvalue, f_statistic, f_pvalue)
                
                # If no serial correlation detected (p > 0.05), use this lag
                if bg_result[1] > 0.05:  # lm_pvalue
                    # Compute t-statistic for first coefficient (γ)
                    test_stat = model.params[0] / model.bse[0]
                    return ADFTestResult(
                        statistic=test_stat,
                        lag=lag,
                        model=model
                    )
            except Exception as e:
                warnings.warn(f"Breusch-Godfrey test failed for lag {lag}: {e}")
                continue
    
    # If no lag eliminates serial correlation, use maximum lag
    d_resid = np.diff(residuals)
    
    if max_lags == 0:
        y_lag = residuals[:-1]
        X = y_lag.reshape(-1, 1)
        y = d_resid
        lag_used = 0
    else:
        lag_matrix = np.zeros((len(d_resid), max_lags))
        for i in range(1, max_lags + 1):
            if i < len(d_resid):
                lag_matrix[i:, i-1] = d_resid[:-i]
        
        y_lag = residuals[:-1]
        X = np.column_stack([y_lag, lag_matrix])
        y = d_resid
        
        # Remove rows with NaN
        valid_idx = max_lags
        X = X[valid_idx:]
        y = y[valid_idx:]
        lag_used = max_lags
    
    try:
        final_model = OLS(y, X).fit()
        # Compute final test statistic
        final_stat = final_model.params[0] / final_model.bse[0]
        
        return ADFTestResult(
            statistic=final_stat,
            lag=lag_used,
            model=final_model
        )
    except Exception as e:
        raise RuntimeError(f"Failed to compute ADF test: {e}")
