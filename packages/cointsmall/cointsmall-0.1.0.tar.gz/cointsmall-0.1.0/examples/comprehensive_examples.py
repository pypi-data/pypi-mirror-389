"""
Example Usage of cointsmall Package

This script demonstrates various use cases of the cointegration testing package.

NOTE: This script requires the package to be installed. Install with:
    pip install -e .
Or run from the package directory with PYTHONPATH set.
"""

import numpy as np
import sys
import os

# Try to import from installed package, otherwise use local
try:
    from cointsmall import (
        test_cointegration_breaks,
        composite_cointegration_test,
        get_critical_value,
        verify_critical_values
    )
except ModuleNotFoundError:
    # If not installed, add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cointsmall import (
        test_cointegration_breaks,
        composite_cointegration_test,
        get_critical_value,
        verify_critical_values
    )


def example_1_basic_test():
    """Example 1: Basic cointegration test without breaks"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Cointegration Test (No Breaks)")
    print("=" * 80)
    
    # Generate cointegrated data
    np.random.seed(42)
    T = 50
    X = np.random.randn(T, 1)
    Y = 2 + 1.5 * X[:, 0] + np.random.randn(T) * 0.3
    
    print("\nGenerated cointegrated data:")
    print(f"  Sample size: T = {T}")
    print(f"  True relationship: Y = 2.0 + 1.5*X + ε")
    
    # Test for cointegration without breaks
    result = test_cointegration_breaks(Y, X, n_breaks=0, model='o')
    print(result)


def example_2_one_break():
    """Example 2: Test with one structural break"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Cointegration Test with One Break")
    print("=" * 80)
    
    # Generate data with a structural break at t=25
    np.random.seed(123)
    T = 50
    break_point = 25
    
    X = np.random.randn(T, 1)
    Y = np.zeros(T)
    
    # Before break: Y = 2 + 1.5*X
    Y[:break_point] = 2 + 1.5 * X[:break_point, 0] + np.random.randn(break_point) * 0.3
    
    # After break: Y = 4 + 2.0*X (intercept and slope change)
    Y[break_point:] = 4 + 2.0 * X[break_point:, 0] + np.random.randn(T - break_point) * 0.3
    
    print("\nGenerated data with structural break:")
    print(f"  Sample size: T = {T}")
    print(f"  True break point: t = {break_point}")
    print(f"  Before break: Y = 2.0 + 1.5*X + ε")
    print(f"  After break: Y = 4.0 + 2.0*X + ε")
    
    # Test with one break in intercept and slope
    result = test_cointegration_breaks(Y, X, n_breaks=1, model='cs')
    print(result)
    
    if result.break_dates:
        print(f"Estimated break date: {result.break_dates[0]}")
        print(f"True break date: {break_point}")


def example_3_two_breaks():
    """Example 3: Test with two structural breaks"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Cointegration Test with Two Breaks")
    print("=" * 80)
    
    # Generate data with two structural breaks
    np.random.seed(456)
    T = 80
    break1, break2 = 25, 55
    
    X = np.random.randn(T, 2)
    Y = np.zeros(T)
    
    # Regime 1: Y = 1 + 1.0*X1 + 0.5*X2
    Y[:break1] = 1 + 1.0 * X[:break1, 0] + 0.5 * X[:break1, 1] + np.random.randn(break1) * 0.3
    
    # Regime 2: Y = 2 + 1.5*X1 + 0.8*X2
    Y[break1:break2] = 2 + 1.5 * X[break1:break2, 0] + 0.8 * X[break1:break2, 1] + \
                       np.random.randn(break2 - break1) * 0.3
    
    # Regime 3: Y = 3 + 2.0*X1 + 1.0*X2
    Y[break2:] = 3 + 2.0 * X[break2:, 0] + 1.0 * X[break2:, 1] + \
                 np.random.randn(T - break2) * 0.3
    
    print("\nGenerated data with two structural breaks:")
    print(f"  Sample size: T = {T}")
    print(f"  True break points: t1 = {break1}, t2 = {break2}")
    
    # Test with two breaks in intercept only
    result_c = test_cointegration_breaks(Y, X, n_breaks=2, model='c')
    print("\nModel C (breaks in intercept only):")
    print(result_c)
    
    # Test with two breaks in intercept and slope
    result_cs = test_cointegration_breaks(Y, X, n_breaks=2, model='cs')
    print("\nModel CS (breaks in intercept and slope):")
    print(result_cs)


def example_4_composite_test():
    """Example 4: Composite testing procedure"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Composite Cointegration Testing")
    print("=" * 80)
    
    # Generate cointegrated data with one structural break
    np.random.seed(789)
    T = 60
    break_point = 30
    
    X = np.random.randn(T, 2)
    Y = np.zeros(T)
    
    Y[:break_point] = 2 + 1.5 * X[:break_point, 0] + 0.8 * X[:break_point, 1] + \
                      np.random.randn(break_point) * 0.5
    Y[break_point:] = 3 + 1.8 * X[break_point:, 0] + 1.0 * X[break_point:, 1] + \
                      np.random.randn(T - break_point) * 0.5
    
    print("\nGenerated data with one structural break:")
    print(f"  Sample size: T = {T}")
    print(f"  True break point: t = {break_point}")
    
    # Run composite test
    result = composite_cointegration_test(Y, X, max_breaks=2, verbose=True)
    print(result)
    
    # Print detailed summary
    result.summary()


def example_5_critical_values():
    """Example 5: Working with critical values"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Critical Values")
    print("=" * 80)
    
    # Get critical values for different configurations
    print("\nCritical values for different configurations:")
    print("-" * 60)
    
    configs = [
        (30, 1, 0, 'o', "T=30, m=1, no breaks"),
        (30, 1, 1, 'c', "T=30, m=1, 1 break in intercept"),
        (30, 1, 1, 'cs', "T=30, m=1, 1 break in intercept & slope"),
        (50, 2, 1, 'cs', "T=50, m=2, 1 break in intercept & slope"),
        (100, 1, 2, 'cs', "T=100, m=1, 2 breaks in intercept & slope"),
    ]
    
    for T, m, b, model, description in configs:
        cv = get_critical_value(T=T, m=m, b=b, model=model)
        print(f"{description:<50} {cv:>8.4f}")


def example_6_verify_implementation():
    """Example 6: Verify implementation against paper"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Verify Implementation")
    print("=" * 80)
    
    # Verify critical values match the paper
    is_valid = verify_critical_values(tolerance=0.1, verbose=True)
    
    if is_valid:
        print("✓ Implementation successfully verified against Trinh (2022)")
    else:
        print("✗ Some discrepancies found - review detailed output above")


def example_7_small_sample():
    """Example 7: Very small sample (T=20)"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Very Small Sample Analysis (T=20)")
    print("=" * 80)
    
    # Generate data for very small sample
    np.random.seed(999)
    T = 20
    X = np.random.randn(T, 1)
    Y = 1 + 0.8 * X[:, 0] + np.random.randn(T) * 0.4
    
    print(f"\nGenerated data with T = {T} (very small sample)")
    
    # Test with composite procedure
    result = composite_cointegration_test(Y, X, max_breaks=1, verbose=False)
    print(result)
    result.summary()


def run_all_examples():
    """Run all examples"""
    examples = [
        example_1_basic_test,
        example_2_one_break,
        example_3_two_breaks,
        example_4_composite_test,
        example_5_critical_values,
        example_6_verify_implementation,
        example_7_small_sample,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COINTSMALL PACKAGE - COMPREHENSIVE EXAMPLES")
    print("Cointegration Testing with Structural Breaks in Small Samples")
    print("=" * 80)
    
    run_all_examples()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")
