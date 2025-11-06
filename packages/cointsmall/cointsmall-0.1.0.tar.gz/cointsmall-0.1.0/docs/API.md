# API Documentation

## cointsmall Package

Python implementation of cointegration tests with endogenous structural breaks for very small sample sizes (T < 50) following Trinh (2022).

---

## Main Functions

### test_cointegration_breaks()

Test for cointegration with a specific number of structural breaks.

**Signature:**
```python
test_cointegration_breaks(Y, X, n_breaks, model='cs', trim=0.15, alpha=0.05)
```

**Parameters:**
- `Y` (array-like): Dependent variable, shape (T,)
- `X` (array-like): Independent variables, shape (T,) or (T, m)
- `n_breaks` (int): Number of structural breaks (0, 1, or 2)
- `model` (str, optional): Type of structural change:
  - `'o'`: no breaks (standard cointegration test)
  - `'c'`: breaks in intercept only
  - `'cs'`: breaks in intercept and slope (default)
- `trim` (float, optional): Trimming parameter (default: 0.15). Restricts break dates to [trim*T, (1-trim)*T]
- `alpha` (float, optional): Significance level (default: 0.05)

**Returns:**
- `CointegrationTestResult`: Object containing:
  - `statistic`: ADF test statistic
  - `critical_value`: Size-corrected critical value
  - `reject_null`: True if null hypothesis is rejected
  - `break_dates`: List of estimated break points
  - `model`: Model type used
  - `n_breaks`: Number of breaks
  - `residuals`: Regression residuals
  - `coefficients`: Estimated coefficients
  - `adf_result`: Detailed ADF test results

**Example:**
```python
import numpy as np
from cointsmall import test_cointegration_breaks

# Generate data
np.random.seed(42)
T = 50
X = np.random.randn(T, 1)
Y = 2 + 1.5 * X[:, 0] + np.random.randn(T) * 0.3

# Test without breaks
result = test_cointegration_breaks(Y, X, n_breaks=0, model='o')
print(result)

# Test with one break
result = test_cointegration_breaks(Y, X, n_breaks=1, model='cs')
print(result)
```

---

### composite_cointegration_test()

Automatic model selection across multiple specifications.

**Signature:**
```python
composite_cointegration_test(Y, X, max_breaks=2, alpha=0.05, trim=0.15, verbose=False)
```

**Parameters:**
- `Y` (array-like): Dependent variable, shape (T,)
- `X` (array-like): Independent variables, shape (T,) or (T, m)
- `max_breaks` (int, optional): Maximum number of breaks to consider (default: 2)
- `alpha` (float, optional): Significance level (default: 0.05)
- `trim` (float, optional): Trimming parameter (default: 0.15)
- `verbose` (bool, optional): Print progress messages (default: False)

**Returns:**
- `CompositeCointegrationResult`: Object containing:
  - `conclusion`: Overall conclusion about cointegration
  - `selected_model`: Best model (CointegrationTestResult) or None
  - `all_results`: Dictionary of all tested models
  - `model_selection_info`: Information about selection process

**Model Selection Logic:**
1. If null never rejected → No cointegration
2. If null rejected in one model only → Select that model
3. If null rejected in multiple models → Select most general model
4. Model priority: CS_b2 > CS_b1 > C_b2 > C_b1 > O_b0

**Example:**
```python
import numpy as np
from cointsmall import composite_cointegration_test

np.random.seed(123)
T = 60
X = np.random.randn(T, 2)
Y = 2 + 1.5 * X[:, 0] + 0.8 * X[:, 1] + np.random.randn(T) * 0.5

result = composite_cointegration_test(Y, X, max_breaks=2, verbose=True)
print(result)
result.summary()  # Detailed summary of all models
```

---

### get_critical_value()

Get size-corrected critical values.

**Signature:**
```python
get_critical_value(T, m, b=1, model='cs', alpha=0.05)
```

**Parameters:**
- `T` (int): Sample size (≥ 12)
- `m` (int): Number of regressors (1, 2, or 3)
- `b` (int, optional): Number of breaks (0, 1, or 2). Default: 1
- `model` (str, optional): Model type ('o', 'c', or 'cs'). Default: 'cs'
- `alpha` (float, optional): Significance level. Only 0.05 is implemented. Default: 0.05

**Returns:**
- `float`: Critical value, or np.nan if configuration not available

**Example:**
```python
from cointsmall import get_critical_value

# Critical value for T=30, m=1, one break in intercept and slope
cv = get_critical_value(T=30, m=1, b=1, model='cs')
print(f"Critical value: {cv:.4f}")

# Critical value for T=50, m=2, no breaks
cv = get_critical_value(T=50, m=2, b=0, model='o')
print(f"Critical value: {cv:.4f}")
```

---

### verify_critical_values()

Verify implementation against Table 1 from Trinh (2022).

**Signature:**
```python
verify_critical_values(tolerance=0.1, verbose=True)
```

**Parameters:**
- `tolerance` (float, optional): Maximum acceptable difference (default: 0.1)
- `verbose` (bool, optional): Print detailed comparison (default: True)

**Returns:**
- `bool` (if verbose=True): True if all values match within tolerance
- `dict` (if verbose=False): Dictionary with keys:
  - `'all_match'`: bool
  - `'max_diff'`: float
  - `'tolerance'`: float
  - `'details'`: dict with detailed results

**Example:**
```python
from cointsmall import verify_critical_values

# Verify with output
is_valid = verify_critical_values()

# Verify without output, custom tolerance
result = verify_critical_values(tolerance=0.05, verbose=False)
print(f"All match: {result['all_match']}")
print(f"Max difference: {result['max_diff']:.4f}")
```

---

### adf_test_residuals()

Perform ADF test on residuals with automatic lag selection.

**Signature:**
```python
adf_test_residuals(residuals, max_lags=None)
```

**Parameters:**
- `residuals` (array-like): Regression residuals
- `max_lags` (int, optional): Maximum lags to consider. If None, uses min(12*(T/100)^0.25, (T-1)/3)

**Returns:**
- `ADFTestResult`: Object containing:
  - `statistic`: ADF test statistic
  - `lag`: Selected number of lags
  - `model`: Fitted OLS model

**Example:**
```python
import numpy as np
from cointsmall import adf_test_residuals

np.random.seed(42)
residuals = np.cumsum(np.random.randn(50) * 0.1)

result = adf_test_residuals(residuals)
print(f"ADF statistic: {result.statistic:.4f}")
print(f"Selected lags: {result.lag}")
```

---

## Result Classes

### CointegrationTestResult

Container for cointegration test results.

**Attributes:**
- `statistic` (float): Minimum ADF test statistic
- `critical_value` (float): Size-corrected critical value
- `p_value` (None): Not available (not in original paper)
- `reject_null` (bool): True if null hypothesis rejected
- `break_dates` (list or None): Estimated break dates
- `model` (str): Model type
- `n_breaks` (int): Number of breaks
- `residuals` (array): Regression residuals
- `coefficients` (array): Estimated coefficients
- `adf_result` (ADFTestResult): ADF test details

**Methods:**
- `__str__()`: Print formatted results
- `__repr__()`: Short representation

### CompositeCointegrationResult

Container for composite test results.

**Attributes:**
- `conclusion` (str): Overall conclusion
- `selected_model` (CointegrationTestResult or None): Best model
- `all_results` (dict): All tested models
- `model_selection_info` (dict): Selection information

**Methods:**
- `__str__()`: Print formatted results
- `summary()`: Print detailed summary table

### ADFTestResult

Container for ADF test results.

**Attributes:**
- `statistic` (float): ADF test statistic
- `lag` (int): Selected number of lags
- `model` (OLS result): Fitted regression model

**Methods:**
- `__str__()`: Print formatted results

---

## Model Specifications

### Model O (No Breaks)
Standard cointegration test without structural breaks.
- Regression: Y = μ + β'X + ε

### Model C (Breaks in Intercept)
Allows for breaks in the intercept only.
- Regression: Y = μ + β'X + Σ μ_i*D_i + ε
- Where D_i are break dummy variables

### Model CS (Breaks in Intercept and Slope)
Allows for breaks in both intercept and slope coefficients.
- Regression: Y = μ + β'X + Σ [μ_i*D_i + β_i'(X*D_i)] + ε

---

## Limitations

1. **Significance Level**: Only 5% significance level is implemented
2. **Maximum Regressors**: Maximum 3 regressors (m ≤ 3)
3. **Maximum Breaks**: Maximum 2 breaks (b ≤ 2)
4. **P-values**: P-values are not computed (not provided in original paper)
5. **Sample Size**: Designed for T ≥ 15, but works best with T ≥ 20

---

## Citation

When using this package, please cite:

```
Trinh, J. (2022). Testing for cointegration with structural changes in very 
small sample. THEMA Working Paper n°2022-01, CY Cergy Paris Université.
```

And the R package:

```
Roudane, M. (2025). cointsmall: R package for cointegration testing with 
structural breaks in very small samples. R package version 0.1.1.
```

---

## Credits

- **Methodology**: Jérôme Trinh (THEMA, CY Cergy Paris Université)
- **R Package**: Dr. Merwan Roudane - Independent Researcher (merwanroudane920@gmail.com)  
- **Python Port**: Based on R package version 0.1.1 by Dr. Merwan Roudane

---

## References

1. Trinh, J. (2022). Testing for cointegration with structural changes in very small sample. THEMA Working Paper n°2022-01, CY Cergy Paris Université.

2. Gregory, A. W., & Hansen, B. E. (1996). Residual-based tests for cointegration in models with regime shifts. Journal of Econometrics, 70(1), 99-126.

3. MacKinnon, J. G. (1991). Critical values for cointegration tests. In Long-Run Economic Relationships: Readings in Cointegration, Chapter 13.
