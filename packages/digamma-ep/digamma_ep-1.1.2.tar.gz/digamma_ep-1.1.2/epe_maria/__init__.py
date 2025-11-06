"""
epe_maria: Symbolic audit framework for model divergence and integrity.

Core Metrics:
- phi(f, g, domain=None): Structural divergence
- delta_phi(f, g, domain=None): Rate divergence
- phi_star(f, g, alpha=0.5, beta=0.5, domain=None): Fusion metric
- drift(f, g, domain=None): Directional drift
- curvature(f, domain=None): Average curvature

Symbolic Grammar:
- ϝ: Structural variation
- δϝ: Rate variation
- ϝ*: Fusion metric
- δ²ϝ: Curvature divergence

Modules:
- benchmark: Audit traces and symbolic benchmarks
- monitor: Compliance logic and alert zones
- core: Kernel logic and symbolic scaffolding
- metrics: Core symbolic operators
- temporal: Drift and time-based variation
- visuals: Plotting utilities for divergence and curvature
- utils: Padding, vector ops, and helpers
"""

import numpy as np
from epe_maria.utils import to_coeffs, robust_derivative
from epe_maria.core import normalize_coeffs, MetricConfig
from .monitor import drift, curvature
from . import benchmark, monitor, core, metrics, temporal, visuals, utils

# Structural divergence
def phi(f, g, domain=(-1, 1), basis='chebyshev', normalize=True, config=None):
    try:
        if config:
            domain = config.domain
            basis = config.basis
            normalize = config.normalize

        coeffs_f = to_coeffs(f, domain, basis)
        coeffs_g = to_coeffs(g, domain, basis)

        if normalize:
            coeffs_f = normalize_coeffs(coeffs_f)
            coeffs_g = normalize_coeffs(coeffs_g)

        max_len = max(len(coeffs_f), len(coeffs_g))
        coeffs_f = np.pad(coeffs_f, (0, max_len - len(coeffs_f)))
        coeffs_g = np.pad(coeffs_g, (0, max_len - len(coeffs_g)))

        return np.linalg.norm(coeffs_f - coeffs_g, ord=2)

    except Exception as e:
        raise RuntimeError(f"phi() failed: {e}")

# Rate divergence
def delta_phi(f, g, domain=(-1, 1), basis='chebyshev', normalize=True, config=None):
    try:
        if config:
            domain = config.domain
            basis = config.basis
            normalize = config.normalize

        df = robust_derivative(f, domain)
        dg = robust_derivative(g, domain)

        return phi(df, dg, domain=domain, basis=basis, normalize=normalize)

    except Exception as e:
        raise RuntimeError(f"delta_phi() failed: {e}")

# Fusion metric
def phi_star(f, g, alpha=0.5, beta=0.5, domain=(-1, 1), basis='chebyshev', normalize=True, config=None):
    if config:
        domain = config.domain
        basis = config.basis
        normalize = config.normalize
        alpha = config.alpha
        beta = config.beta

    s = phi(f, g, domain=domain, basis=basis, normalize=normalize)
    r = delta_phi(f, g, domain=domain, basis=basis, normalize=normalize)
    return alpha * s + beta * r

# Symbolic aliases
ϝ = phi
δϝ = delta_phi
ϝ_star = phi_star

# CZVS logic
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

__all__ = [
    "phi", "delta_phi", "phi_star", "drift", "curvature",
    "ϝ", "δϝ", "ϝ_star",
    "Ω_CZVS", "𝓜_CZVS",
    "benchmark", "monitor", "core", "metrics", "temporal", "visuals", "utils"
]

def Ω_CZVS_drift(f, g, W=None, domain=(-1, 1), basis='chebyshev', normalize=True):
    coeffs_g = to_coeffs(g, domain, basis)
    if normalize:
        coeffs_g = coeffs_g / np.linalg.norm(coeffs_g)

    dim = len(coeffs_g)
    if W is None:
        W = np.eye(dim)
    elif W.shape != (dim, dim):
        raise ValueError(f"W must be ({dim}, {dim})")

    ensemble = [W @ coeffs_g for _ in range(10)]
    drifts = [drift(f, lambda x: np.polyval(wg[::-1], x), domain=domain) for wg in ensemble]
    return np.var(drifts)
