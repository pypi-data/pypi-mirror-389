import numpy as np
from epe_maria.metrics import phi
from epe_maria.utils import to_coeffs

def Ω_CZVS(f, g, W=None, domain=(-1, 1), basis='chebyshev', normalize=True):
    coeffs_f = to_coeffs(f, domain, basis)
    coeffs_g = to_coeffs(g, domain, basis)

    if normalize:
        coeffs_f = coeffs_f / np.linalg.norm(coeffs_f)
        coeffs_g = coeffs_g / np.linalg.norm(coeffs_g)

    if W is None:
        W = np.eye(len(coeffs_g))

    ensemble = [W @ coeffs_g for _ in range(10)]
    divergences = [phi(f, lambda x: np.polyval(wg[::-1], x), domain=domain) for wg in ensemble]
    return np.var(divergences)

def 𝓜_CZVS(f, g, W=None, alpha=1.0, beta=1.0, gamma=1.0, domain=(-1, 1), basis='chebyshev'):
    coeffs_g = to_coeffs(g, domain, basis)
    b0 = coeffs_g[0] if len(coeffs_g) > 0 else 0
    var_opt = Ω_CZVS(f, g, W, domain, basis)
    cost_conditions = np.linalg.norm(W - np.eye(W.shape[0])) if W is not None else 0
    return alpha * abs(b0) + beta * abs(var_opt) + gamma * cost_conditions
