from epe_maria import Ω_CZVS, 𝓜_CZVS
import numpy as np

def f(x): return x**2
def g(x): return x**2 + 0.01
W = np.eye(3)

def test_czvs_variance_nonnegative():
    var = Ω_CZVS(f, g, W)
    print("Ω_CZVS:", var)
    assert var >= 0, "Variance must be non-negative"

def test_czvs_metric_positive():
    score = 𝓜_CZVS(f, g, W)
    print("𝓜_CZVS:", score)
    assert score > 0, "Metric should be positive unless CZVS is achieved"

if __name__ == "__main__":
    test_czvs_variance_nonnegative()
    test_czvs_metric_positive()
