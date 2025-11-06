# cointsmall: Cointegration Testing with Structural Breaks in Very Small Samples

Python implementation of cointegration tests with endogenous structural breaks for very small sample sizes (T < 50) following Trinh (2022).

## Overview

This package implements the methodology from:

> Trinh, J. (2022). Testing for cointegration with structural changes in very small sample. THEMA Working Paper n°2022-01, CY Cergy Paris Université.

The package extends the Gregory-Hansen (1996) test to allow up to two structural breaks with size-corrected critical values computed via surface response methodology. It is designed for macroeconometric studies of emerging economies where data history is limited.

## Features

- **Size-corrected critical values** for sample sizes as small as T=15
- **Multiple model specifications**: No breaks, breaks in intercept only, breaks in intercept and slope
- **Up to 2 structural breaks** with endogenous break date selection
- **Composite testing procedure** for automatic model selection
- **Verified against paper**: All critical values match Table 1 from Trinh (2022)

## Installation

```bash
pip install cointsmall
```

Or install from source:

```bash
git clone https://github.com/yourusername/cointsmall-python.git
cd cointsmall-python
pip install -e .
```

## Quick Start

```python
import numpy as np
from cointsmall import composite_cointegration_test, test_cointegration_breaks

# Generate cointegrated data
np.random.seed(123)
T = 50
X = np.random.randn(T, 2)
Y = 2 + 1.5 * X[:, 0] + 0.8 * X[:, 1] + np.random.randn(T) * 0.5

# Test for cointegration using composite procedure
result = composite_cointegration_test(Y, X, max_breaks=2)
print(result)
print(result.summary())
```

## Main Functions

### `test_cointegration_breaks()`
Test for cointegration with a specific number of breaks:

```python
# No breaks
result = test_cointegration_breaks(Y, X, n_breaks=0, model='o')

# One break in intercept and slope
result = test_cointegration_breaks(Y, X, n_breaks=1, model='cs')

# Two breaks in intercept only
result = test_cointegration_breaks(Y, X, n_breaks=2, model='c')

print(result)
```

### `composite_cointegration_test()`
Automatic model selection across multiple specifications:

```python
result = composite_cointegration_test(Y, X, max_breaks=2)
print(result.summary())
```

### `get_critical_value()`
Get size-corrected critical values:

```python
from cointsmall import get_critical_value

# T=30, m=1 regressor, 1 break in intercept and slope
cv = get_critical_value(T=30, m=1, b=1, model='cs')
print(f"Critical value: {cv}")
```

### `verify_critical_values()`
Verify implementation against paper:

```python
from cointsmall import verify_critical_values

# Should return True
is_valid = verify_critical_values()
print(f"Implementation valid: {is_valid}")
```

## Model Specifications

- **Model O**: No structural breaks (standard cointegration test)
- **Model C**: Breaks in intercept only
- **Model CS**: Breaks in intercept and slope coefficients

## Limitations

- Only 5% significance level is implemented (as in the paper)
- Maximum 3 regressors (m ≤ 3)
- Maximum 2 breaks (b ≤ 2)
- P-values are not computed (not provided in original paper)

## Citation

When using this package, please cite:

```
Trinh, J. (2022). Testing for cointegration with structural changes in very 
small sample. THEMA Working Paper n°2022-01, CY Cergy Paris Université.
```

And optionally cite the R package:

```
Roudane, M. (2025). cointsmall: R package for cointegration testing with 
structural breaks in very small samples. R package version 0.1.1.
```

## Author

- **Methodology**: Jérôme Trinh (jerome.trinh@ensae.fr)
- **R Package**: Dr. Merwan Roudane (merwanroudane920@gmail.com) - Independent Researcher
- **Python Port**: Based on R package version 0.1.1 by Dr. Merwan Roudane

## References

- Gregory, A. W., & Hansen, B. E. (1996). Residual-based tests for cointegration in models with regime shifts. *Journal of Econometrics*, 70(1), 99-126.
- MacKinnon, J. G. (1991). Critical values for cointegration tests. In *Long-Run Economic Relationships: Readings in Cointegration*, Chapter 13.
- Trinh, J. (2022). Testing for cointegration with structural changes in very small sample. THEMA Working Paper n°2022-01, CY Cergy Paris Université.

## License

GPL-3
