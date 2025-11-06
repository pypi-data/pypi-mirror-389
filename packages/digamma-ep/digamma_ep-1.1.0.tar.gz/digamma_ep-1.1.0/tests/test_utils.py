import numpy as np
from epe_maria.utils import to_coeffs, robust_derivative

def test_to_coeffs_callable():
    f = lambda x: x**2
    coeffs = to_coeffs(f)
    assert isinstance(coeffs, np.ndarray)
    assert len(coeffs) > 0

def test_robust_derivative_callable():
    f = lambda x: np.sin(x)
    df = robust_derivative(f)
    assert callable(df)
    assert abs(df(0)) < 1.0
