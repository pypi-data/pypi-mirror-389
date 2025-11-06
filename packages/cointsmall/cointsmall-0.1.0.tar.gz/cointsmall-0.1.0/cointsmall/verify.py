"""
Verification Module

Compares computed critical values with Table 1 from Trinh (2022), page 8.
This helps verify that the implementation matches the paper.
"""

import numpy as np
from .critical_values import get_critical_value


def verify_critical_values(tolerance=0.1, verbose=True):
    """
    Verify critical values against Table 1 from Trinh (2022).
    
    Compares computed critical values with Table 1 (page 8) of the paper.
    The default tolerance of 0.1 is used because values in the paper are 
    reported to 2 decimal places.
    
    Parameters
    ----------
    tolerance : float, optional
        Maximum acceptable difference (default: 0.1).
    verbose : bool, optional
        If True, print detailed comparison (default: True).
    
    Returns
    -------
    bool or dict
        If verbose=True, returns True if all values match within tolerance,
        False otherwise. If verbose=False, returns a dict with keys:
        'all_match', 'max_diff', 'tolerance', and 'details'.
    
    References
    ----------
    Trinh, J. (2022). Testing for cointegration with structural changes in very 
    small sample. THEMA Working Paper n°2022-01, Table 1, page 8.
    
    Examples
    --------
    >>> # Verify critical values match the paper (with output)
    >>> verify_critical_values()
    
    >>> # Verify with custom tolerance, suppress output and get detailed results
    >>> result = verify_critical_values(tolerance=0.05, verbose=False)
    >>> print(result['all_match'])
    >>> print(result['max_diff'])
    """
    # Values from Table 1 of the paper (page 8)
    table1 = {
        'm1_b1_c': {
            'T': [15, 20, 30, 50, 100, 500],
            'CV': [-5.85, -5.73, -5.37, -5.08, -4.83, -4.62]
        },
        'm1_b1_cs': {
            'T': [15, 20, 30, 50, 100, 500],
            'CV': [-6.25, -6.08, -5.72, -5.40, -5.11, -4.96]
        },
        'm1_b2_c': {
            'T': [15, 20, 30, 50, 100, 500],
            'CV': [-8.16, -7.11, -6.90, -6.04, -5.47, -5.21]
        },
        'm1_b2_cs': {
            'T': [15, 20, 30, 50, 100, 500],
            'CV': [-8.87, -7.81, -7.47, -6.67, -6.24, -5.94]
        }
    }
    
    configs = [
        {'m': 1, 'b': 1, 'model': 'c', 'name': 'm1_b1_c'},
        {'m': 1, 'b': 1, 'model': 'cs', 'name': 'm1_b1_cs'},
        {'m': 1, 'b': 2, 'model': 'c', 'name': 'm1_b2_c'},
        {'m': 1, 'b': 2, 'model': 'cs', 'name': 'm1_b2_cs'}
    ]
    
    all_correct = True
    all_diffs = []
    detailed_results = {}
    
    if verbose:
        print("\n" + "=" * 80)
        print("VERIFICATION: Critical Values vs Table 1 (page 8)")
        print("=" * 80)
    
    for cfg in configs:
        if verbose:
            print(f"\n{cfg['name']} (m={cfg['m']}, b={cfg['b']}, model={cfg['model']})")
            print("-" * 70)
            print(f"{'T':>8} {'Paper':>15} {'Computed':>15} {'Diff':>12}")
            print("-" * 70)
        
        paper_data = table1[cfg['name']]
        config_results = {
            'T': paper_data['T'],
            'Paper': paper_data['CV'],
            'Computed': [],
            'Diff': [],
            'Match': []
        }
        
        for i, T_val in enumerate(paper_data['T']):
            paper_cv = paper_data['CV'][i]
            computed_cv = get_critical_value(T_val, cfg['m'], cfg['b'], cfg['model'])
            diff = abs(paper_cv - computed_cv)
            all_diffs.append(diff)
            
            config_results['Computed'].append(computed_cv)
            config_results['Diff'].append(diff)
            config_results['Match'].append(diff <= tolerance)
            
            if verbose:
                status = " [MISMATCH]" if diff > tolerance else " [OK]"
                print(f"{T_val:>8} {paper_cv:>15.2f} {computed_cv:>15.2f} {diff:>12.4f}{status}")
            
            if diff > tolerance:
                all_correct = False
        
        detailed_results[cfg['name']] = config_results
    
    max_diff = max(all_diffs) if all_diffs else 0.0
    
    if verbose:
        print("\n" + "=" * 80)
        if all_correct:
            print(f"SUCCESS: All critical values verified (max diff: {max_diff:.4f})")
        else:
            print("WARNING: Some critical values do not match within tolerance")
            print(f"Max difference: {max_diff:.4f}")
        print("=" * 80 + "\n")
        return all_correct
    else:
        return {
            'all_match': all_correct,
            'max_diff': max_diff,
            'tolerance': tolerance,
            'details': detailed_results
        }


def compare_critical_values_across_sample_sizes(m=1, b=1, model='cs', T_range=None):
    """
    Compare critical values across different sample sizes.
    
    Useful for visualizing how critical values change with sample size.
    
    Parameters
    ----------
    m : int, optional
        Number of regressors (default: 1).
    b : int, optional
        Number of breaks (default: 1).
    model : str, optional
        Model type (default: 'cs').
    T_range : list or array-like, optional
        Sample sizes to test. If None, uses [15, 20, 30, 50, 100, 200, 500].
    
    Returns
    -------
    dict
        Dictionary with 'T' and 'CV' keys containing sample sizes and
        corresponding critical values.
    
    Examples
    --------
    >>> results = compare_critical_values_across_sample_sizes(m=1, b=1, model='cs')
    >>> print(results)
    """
    if T_range is None:
        T_range = [15, 20, 30, 50, 100, 200, 500]
    
    critical_values = []
    for T in T_range:
        cv = get_critical_value(T, m, b, model)
        critical_values.append(cv)
    
    results = {
        'T': T_range,
        'CV': critical_values,
        'm': m,
        'b': b,
        'model': model
    }
    
    # Print results
    print(f"\nCritical Values for m={m}, b={b}, model={model}")
    print("-" * 40)
    print(f"{'T':>8} {'Critical Value':>20}")
    print("-" * 40)
    for T, cv in zip(T_range, critical_values):
        print(f"{T:>8} {cv:>20.4f}")
    print("-" * 40 + "\n")
    
    return results
