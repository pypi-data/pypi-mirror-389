"""
cointsmall: Cointegration Testing with Structural Breaks in Very Small Samples

Python implementation of cointegration tests with endogenous structural breaks
for very small sample sizes (T < 50) following Trinh (2022).

Main Functions:
--------------
- test_cointegration_breaks: Test for cointegration with specified number of breaks
- composite_cointegration_test: Automatic model selection across specifications
- get_critical_value: Get size-corrected critical values
- verify_critical_values: Verify implementation against paper
"""

__version__ = "0.1.0"
__author__ = "Jérôme Trinh (methodology), Dr. Merwan Roudane (R package - Independent Researcher), Python port"

from .cointegration_test import test_cointegration_breaks, CointegrationTestResult
from .composite_test import composite_cointegration_test, CompositeCointegrationResult
from .critical_values import get_critical_value
from .verify import verify_critical_values
from .adf_test import adf_test_residuals, ADFTestResult

__all__ = [
    'test_cointegration_breaks',
    'composite_cointegration_test',
    'get_critical_value',
    'verify_critical_values',
    'adf_test_residuals',
    'CointegrationTestResult',
    'CompositeCointegrationResult',
    'ADFTestResult',
]
