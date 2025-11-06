"""
Cointegration Test with Structural Breaks Module

Implements the Gregory-Hansen (1996) test extended to allow up to two
endogenous structural breaks, as developed in Trinh (2022).

Based on Trinh (2022), Section 2.
"""

import numpy as np
from statsmodels.regression.linear_model import OLS
from .adf_test import adf_test_residuals
from .critical_values import get_critical_value


class CointegrationTestResult:
    """
    Container for cointegration test results.
    
    Attributes
    ----------
    statistic : float
        Minimum ADF test statistic (ADF*)
    critical_value : float
        Size-corrected critical value
    p_value : float or None
        Approximate p-value (currently None as not provided in paper)
    reject_null : bool
        True if null of no cointegration is rejected
    break_dates : array-like or None
        Estimated break dates (indices)
    model : str
        Model type used
    n_breaks : int
        Number of breaks
    residuals : array-like
        Residuals from best-fit regression
    coefficients : array-like
        Estimated coefficients
    adf_result : ADFTestResult
        ADF test results
    """
    
    def __init__(self, statistic, critical_value, reject_null, break_dates,
                 model, n_breaks, residuals, coefficients, adf_result):
        self.statistic = statistic
        self.critical_value = critical_value
        self.p_value = None  # Not provided in paper
        self.reject_null = reject_null
        self.break_dates = break_dates
        self.model = model
        self.n_breaks = n_breaks
        self.residuals = residuals
        self.coefficients = coefficients
        self.adf_result = adf_result
    
    def __str__(self):
        result_str = (
            "\nCointegration Test with Structural Breaks\n"
            "==========================================\n"
            f"Model: {self.model}\n"
            f"Number of breaks: {self.n_breaks}\n"
        )
        
        if self.break_dates is not None:
            result_str += f"Break dates: {', '.join(map(str, self.break_dates))}\n"
        
        result_str += (
            f"\nTest Statistic (ADF*): {self.statistic:.4f}\n"
            f"Critical Value (5%): {self.critical_value:.4f}\n"
            f"Decision: {'Reject null (cointegration detected)' if self.reject_null else 'Fail to reject null (no cointegration)'}\n"
        )
        
        return result_str
    
    def __repr__(self):
        return f"CointegrationTestResult(statistic={self.statistic:.4f}, reject_null={self.reject_null})"


def test_cointegration_breaks(Y, X, n_breaks, model='cs', trim=0.15, alpha=0.05):
    """
    Test for cointegration with structural breaks.
    
    Implements the Gregory-Hansen (1996) test extended to allow up to two
    endogenous structural breaks, as developed in Trinh (2022).
    
    Following Trinh (2022), the test minimizes the ADF statistic over all
    possible break dates: ADF* = inf_{t_i} ADF(ε_hat)
    
    The regression model (Equation 1, page 3) is:
    Y = [1 X][μ β]' + Σ B_i[1 X][μ_i β_i]' + ε
    
    where B_i are break dummy matrices.
    
    Parameters
    ----------
    Y : array-like, shape (T,)
        Dependent variable.
    X : array-like, shape (T,) or (T, m)
        Independent variables. Can be 1D or 2D.
    n_breaks : int
        Number of structural breaks (0, 1, or 2).
    model : str, optional
        Type of structural change:
        - 'o': no breaks
        - 'c': breaks in intercept only
        - 'cs': breaks in intercept and slope (default)
    trim : float, optional
        Trimming parameter for break date search (default: 0.15).
        Restricts break dates to [trim*T, (1-trim)*T].
    alpha : float, optional
        Significance level for critical value (default: 0.05).
    
    Returns
    -------
    CointegrationTestResult
        Object containing test results.
    
    References
    ----------
    Trinh, J. (2022). Testing for cointegration with structural changes in very 
    small sample. THEMA Working Paper n°2022-01, Section 2, pages 3-5.
    
    Gregory, A. W., & Hansen, B. E. (1996). Residual-based tests for cointegration 
    in models with regime shifts. Journal of Econometrics, 70(1), 99-126.
    
    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(123)
    >>> T = 50
    >>> X = np.random.randn(T, 1)
    >>> Y = 2 + 1.5 * X[:, 0] + np.random.randn(T) * 0.3
    >>> 
    >>> # Test for cointegration without breaks
    >>> result = test_cointegration_breaks(Y, X, n_breaks=0, model='o')
    >>> print(result)
    >>> 
    >>> # Test with one break in intercept and slope
    >>> result2 = test_cointegration_breaks(Y, X, n_breaks=1, model='cs')
    >>> print(result2)
    """
    # Convert to numpy arrays and ensure proper shape
    Y = np.asarray(Y).flatten()
    X = np.asarray(X)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T = len(Y)
    m = X.shape[1]
    
    # Input validation
    if T != X.shape[0]:
        raise ValueError("Y and X must have the same number of observations")
    
    if trim <= 0 or trim >= 0.5:
        raise ValueError("trim must be between 0 and 0.5")
    
    if n_breaks < 0 or n_breaks > 2:
        raise ValueError("n_breaks must be 0, 1, or 2")
    
    if model not in ['o', 'c', 'cs']:
        raise ValueError("model must be 'o', 'c', or 'cs'")
    
    # Get critical value
    cv = get_critical_value(T=T, m=m, b=n_breaks, model=model, alpha=alpha)
    
    if np.isnan(cv):
        import warnings
        warnings.warn("Could not compute critical value for this configuration")
    
    # Case: No breaks
    if n_breaks == 0 or model == 'o':
        # Simple OLS regression: Y = α + X*β + ε
        X_with_const = np.column_stack([np.ones(T), X])
        ols_model = OLS(Y, X_with_const).fit()
        residuals = ols_model.resid
        adf_result = adf_test_residuals(residuals)
        
        return CointegrationTestResult(
            statistic=adf_result.statistic,
            critical_value=cv,
            reject_null=adf_result.statistic < cv,
            break_dates=None,
            model=model,
            n_breaks=0,
            residuals=residuals,
            coefficients=ols_model.params,
            adf_result=adf_result
        )
    
    # Case: With breaks - grid search
    trim_start = int(np.ceil(T * trim))
    trim_end = int(np.floor(T * (1 - trim)))
    possible_dates = range(trim_start, trim_end + 1)
    
    min_stat = np.inf
    best_breaks = None
    best_residuals = None
    best_coefs = None
    best_adf = None
    
    if n_breaks == 1:
        # Search over single break dates
        for t1 in possible_dates:
            # Create break dummies
            D1 = np.zeros((T, m + 1))
            D1[t1:, :] = np.column_stack([np.ones(T - t1), X[t1:, :]])
            
            # Construct design matrix
            if model == 'c':
                # Break in intercept only
                Z = np.column_stack([np.ones(T), X, D1[:, 0]])
            else:  # model == 'cs'
                # Break in intercept and slope
                Z = np.column_stack([np.ones(T), X, D1])
            
            # Estimate regression
            try:
                ols_model = OLS(Y, Z).fit()
                resid = ols_model.resid
                
                # ADF test on residuals
                adf_result = adf_test_residuals(resid)
                
                if adf_result.statistic < min_stat:
                    min_stat = adf_result.statistic
                    best_breaks = [t1]
                    best_residuals = resid
                    best_coefs = ols_model.params
                    best_adf = adf_result
            except Exception:
                continue
    
    elif n_breaks == 2:
        # Search over two break dates
        for t1 in possible_dates:
            for t2 in possible_dates:
                if t2 <= t1 + int(np.ceil(T * trim)):
                    continue  # Ensure minimum distance between breaks
                
                # Create break dummies
                D1 = np.zeros((T, m + 1))
                D1[t1:, :] = np.column_stack([np.ones(T - t1), X[t1:, :]])
                
                D2 = np.zeros((T, m + 1))
                D2[t2:, :] = np.column_stack([np.ones(T - t2), X[t2:, :]])
                
                # Construct design matrix
                if model == 'c':
                    # Breaks in intercept only
                    Z = np.column_stack([np.ones(T), X, D1[:, 0], D2[:, 0]])
                else:  # model == 'cs'
                    # Breaks in intercept and slope
                    Z = np.column_stack([np.ones(T), X, D1, D2])
                
                # Estimate regression
                try:
                    ols_model = OLS(Y, Z).fit()
                    resid = ols_model.resid
                    
                    # ADF test on residuals
                    adf_result = adf_test_residuals(resid)
                    
                    if adf_result.statistic < min_stat:
                        min_stat = adf_result.statistic
                        best_breaks = [t1, t2]
                        best_residuals = resid
                        best_coefs = ols_model.params
                        best_adf = adf_result
                except Exception:
                    continue
    
    # Return results
    return CointegrationTestResult(
        statistic=min_stat,
        critical_value=cv,
        reject_null=min_stat < cv,
        break_dates=best_breaks,
        model=model,
        n_breaks=n_breaks,
        residuals=best_residuals,
        coefficients=best_coefs,
        adf_result=best_adf
    )
