"""
Composite Cointegration Testing Procedure Module

Tests for cointegration across multiple model specifications and selects
the best model based on joint significance tests of structural break
parameters, following Trinh (2022), Section 6.
"""

import numpy as np
from .cointegration_test import test_cointegration_breaks


class CompositeCointegrationResult:
    """
    Container for composite cointegration test results.
    
    Attributes
    ----------
    conclusion : str
        Overall conclusion about cointegration
    selected_model : CointegrationTestResult or None
        Best model results, or None if no cointegration detected
    all_results : dict
        Results for all tested models
    model_selection_info : dict
        Information about model selection process
    """
    
    def __init__(self, conclusion, selected_model, all_results, model_selection_info):
        self.conclusion = conclusion
        self.selected_model = selected_model
        self.all_results = all_results
        self.model_selection_info = model_selection_info
    
    def __str__(self):
        result_str = (
            "\nComposite Cointegration Test\n"
            "============================\n"
            f"Models tested: {len(self.all_results)}\n"
            f"Models rejecting null: {self.model_selection_info['n_rejected']}\n"
            f"\nConclusion: {self.conclusion}\n"
        )
        
        if self.selected_model is not None:
            result_str += (
                "\nSelected Model:\n"
                f"  Type: {self.selected_model.model}\n"
                f"  Breaks: {self.selected_model.n_breaks}\n"
            )
            if self.selected_model.break_dates is not None:
                result_str += f"  Break dates: {', '.join(map(str, self.selected_model.break_dates))}\n"
            result_str += (
                f"  Test statistic: {self.selected_model.statistic:.4f}\n"
                f"  Critical value: {self.selected_model.critical_value:.4f}\n"
            )
        
        return result_str
    
    def __repr__(self):
        return f"CompositeCointegrationResult(conclusion='{self.conclusion}')"
    
    def summary(self):
        """
        Print detailed summary of all models tested.
        
        Returns
        -------
        dict
            Summary information for all models.
        """
        print("\nDetailed Summary of All Models")
        print("=" * 70)
        print(f"{'Model':<12} {'Statistic':>12} {'Critical':>12} {'Reject':>10}")
        print("-" * 70)
        
        summary_dict = {}
        for model_name, result in self.all_results.items():
            print(f"{model_name:<12} {result.statistic:>12.4f} "
                  f"{result.critical_value:>12.4f} {str(result.reject_null):>10}")
            summary_dict[model_name] = {
                'statistic': result.statistic,
                'critical_value': result.critical_value,
                'reject_null': result.reject_null
            }
        
        print("-" * 70)
        print(f"\nRejected models: {', '.join(self.model_selection_info['rejected_models'])}")
        if self.selected_model is not None:
            selected_name = f"{self.selected_model.model}_b{self.selected_model.n_breaks}"
            print(f"Selected model: {selected_name}")
        else:
            print("Selected model: None")
        print()
        
        return summary_dict


def composite_cointegration_test(Y, X, max_breaks=2, alpha=0.05, trim=0.15, verbose=False):
    """
    Composite cointegration testing procedure.
    
    Tests for cointegration across multiple model specifications and selects
    the best model based on rejection patterns, following Trinh (2022), Section 6.
    
    Following Trinh (2022), Section 6 (pages 17-19), the procedure:
    
    1. Tests models: O (no breaks), C_b1, CS_b1, C_b2, CS_b2
    2. Applies selection rules (page 18):
       - If null never rejected: No cointegration
       - If null rejected in one model only: Select that model
       - If null rejected in multiple models: Select most general model
    3. Model priority: CS_b2 > CS_b1 > C_b2 > C_b1 > O_b0
    
    Parameters
    ----------
    Y : array-like, shape (T,)
        Dependent variable.
    X : array-like, shape (T,) or (T, m)
        Independent variables.
    max_breaks : int, optional
        Maximum number of breaks to consider (default: 2).
    alpha : float, optional
        Significance level (default: 0.05).
    trim : float, optional
        Trimming parameter for break search (default: 0.15).
    verbose : bool, optional
        If True, print progress messages (default: False).
    
    Returns
    -------
    CompositeCointegrationResult
        Object containing overall test results.
    
    References
    ----------
    Trinh, J. (2022). Testing for cointegration with structural changes in very 
    small sample. THEMA Working Paper n°2022-01, Section 6, pages 17-19.
    
    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(123)
    >>> T = 50
    >>> X = np.random.randn(T, 2)
    >>> Y = 2 + 1.5 * X[:, 0] + 0.8 * X[:, 1] + np.random.randn(T) * 0.5
    >>> 
    >>> # Test using composite procedure
    >>> result = composite_cointegration_test(Y, X, max_breaks=2)
    >>> print(result)
    >>> result.summary()
    """
    # Convert to numpy arrays
    Y = np.asarray(Y).flatten()
    X = np.asarray(X)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    if verbose:
        print("Testing for cointegration using composite procedure...")
    
    # Test all model configurations
    all_results = {}
    
    # Model O (no breaks)
    if verbose:
        print("  Testing model O (no breaks)...")
    all_results['o_b0'] = test_cointegration_breaks(
        Y, X, n_breaks=0, model='o', trim=trim, alpha=alpha
    )
    
    # Models with breaks
    for b in range(1, max_breaks + 1):
        # Model C (breaks in intercept)
        model_name = f'c_b{b}'
        if verbose:
            print(f"  Testing model {model_name}...")
        all_results[model_name] = test_cointegration_breaks(
            Y, X, n_breaks=b, model='c', trim=trim, alpha=alpha
        )
        
        # Model CS (breaks in intercept and slope)
        model_name = f'cs_b{b}'
        if verbose:
            print(f"  Testing model {model_name}...")
        all_results[model_name] = test_cointegration_breaks(
            Y, X, n_breaks=b, model='cs', trim=trim, alpha=alpha
        )
    
    # Count how many models reject null
    rejected_models = [name for name, result in all_results.items() if result.reject_null]
    
    # Selection logic (Section 6, page 18)
    if len(rejected_models) == 0:
        # No cointegration detected
        conclusion = "No cointegration"
        selected_model = None
        
    elif len(rejected_models) == 1:
        # Only one model rejects: select it
        conclusion = "Cointegration detected"
        selected_model = all_results[rejected_models[0]]
        
    else:
        # Multiple models reject: select most general model that rejects
        # Priority: cs_b2 > cs_b1 > c_b2 > c_b1 > o_b0
        
        priority = ['cs_b2', 'cs_b1', 'c_b2', 'c_b1', 'o_b0']
        
        selected_model = None
        for mod_name in priority:
            if mod_name in rejected_models:
                conclusion = "Cointegration detected"
                selected_model = all_results[mod_name]
                break
    
    model_selection_info = {
        'rejected_models': rejected_models,
        'n_rejected': len(rejected_models),
        'alpha': alpha,
        'max_breaks': max_breaks
    }
    
    return CompositeCointegrationResult(
        conclusion=conclusion,
        selected_model=selected_model,
        all_results=all_results,
        model_selection_info=model_selection_info
    )
