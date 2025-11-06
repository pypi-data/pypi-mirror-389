"""
Quick Start Guide for cointsmall Package

This guide demonstrates the most common use cases.

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

print("\n" + "=" * 80)
print("COINTSMALL - QUICK START GUIDE")
print("Cointegration Testing with Structural Breaks in Small Samples")
print("=" * 80)

# ============================================================================
# 1. BASIC IMPORT
# ============================================================================
print("\n1. IMPORTING THE PACKAGE")
print("-" * 80)

print("✓ Successfully imported cointsmall functions")

# ============================================================================
# 2. GENERATE EXAMPLE DATA
# ============================================================================
print("\n2. GENERATING SAMPLE DATA")
print("-" * 80)

np.random.seed(42)
T = 50  # Sample size
X = np.random.randn(T, 1)  # Single regressor
Y = 2 + 1.5 * X[:, 0] + np.random.randn(T) * 0.3  # Cointegrated relationship

print(f"Generated data: T={T}, Y = 2.0 + 1.5*X + ε")

# ============================================================================
# 3. TEST WITHOUT BREAKS
# ============================================================================
print("\n3. TEST FOR COINTEGRATION (NO BREAKS)")
print("-" * 80)

result = test_cointegration_breaks(Y, X, n_breaks=0, model='o')
print(f"Test Statistic: {result.statistic:.4f}")
print(f"Critical Value (5%): {result.critical_value:.4f}")
print(f"Decision: {'Cointegration detected ✓' if result.reject_null else 'No cointegration ✗'}")

# ============================================================================
# 4. TEST WITH ONE BREAK
# ============================================================================
print("\n4. TEST WITH ONE STRUCTURAL BREAK")
print("-" * 80)

# Generate data with a break
np.random.seed(123)
T = 50
break_point = 25
X = np.random.randn(T, 1)
Y = np.zeros(T)
Y[:break_point] = 2 + 1.5 * X[:break_point, 0] + np.random.randn(break_point) * 0.3
Y[break_point:] = 4 + 2.0 * X[break_point:, 0] + np.random.randn(T - break_point) * 0.3

print(f"Data with break at t={break_point}")
print("Before: Y = 2.0 + 1.5*X, After: Y = 4.0 + 2.0*X")

result = test_cointegration_breaks(Y, X, n_breaks=1, model='cs')
print(f"\nTest Statistic: {result.statistic:.4f}")
print(f"Critical Value (5%): {result.critical_value:.4f}")
print(f"Estimated break: t={result.break_dates[0]}")
print(f"True break: t={break_point}")
print(f"Decision: {'Cointegration detected ✓' if result.reject_null else 'No cointegration ✗'}")

# ============================================================================
# 5. COMPOSITE TEST (AUTOMATIC MODEL SELECTION)
# ============================================================================
print("\n5. COMPOSITE TEST (AUTOMATIC MODEL SELECTION)")
print("-" * 80)

np.random.seed(789)
T = 60
X = np.random.randn(T, 2)
Y = 2 + 1.5 * X[:, 0] + 0.8 * X[:, 1] + np.random.randn(T) * 0.5

result = composite_cointegration_test(Y, X, max_breaks=2)
print(f"Conclusion: {result.conclusion}")
if result.selected_model:
    print(f"Selected model: {result.selected_model.model}, breaks={result.selected_model.n_breaks}")
    print(f"Test statistic: {result.selected_model.statistic:.4f}")

# ============================================================================
# 6. CRITICAL VALUES
# ============================================================================
print("\n6. WORKING WITH CRITICAL VALUES")
print("-" * 80)

# Get critical values for different configurations
configs = [
    (30, 1, 1, 'cs'),
    (50, 2, 1, 'cs'),
    (100, 1, 2, 'cs'),
]

for T, m, b, model in configs:
    cv = get_critical_value(T=T, m=m, b=b, model=model)
    print(f"T={T:>3}, m={m}, b={b}, model={model}: CV = {cv:>7.4f}")

# ============================================================================
# 7. VERIFY IMPLEMENTATION
# ============================================================================
print("\n7. VERIFY IMPLEMENTATION AGAINST PAPER")
print("-" * 80)

is_valid = verify_critical_values(tolerance=0.05, verbose=False)
if is_valid:
    print("✓ Implementation verified against Trinh (2022)")
else:
    print("! Some minor discrepancies (see detailed verification for info)")

# ============================================================================
# 8. SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The cointsmall package provides:

1. test_cointegration_breaks() - Test with specific number of breaks
   - n_breaks: 0, 1, or 2
   - model: 'o' (none), 'c' (intercept), 'cs' (intercept & slope)

2. composite_cointegration_test() - Automatic model selection
   - Tests all configurations and selects best model

3. get_critical_value() - Size-corrected critical values
   - Valid for T as small as 15

4. verify_critical_values() - Verify against paper

Key features:
- Designed for small samples (T < 50)
- Handles up to 2 structural breaks
- Size-corrected critical values
- Endogenous break date selection
""")

print("\nFor more examples, see examples/comprehensive_examples.py")
print("=" * 80 + "\n")
