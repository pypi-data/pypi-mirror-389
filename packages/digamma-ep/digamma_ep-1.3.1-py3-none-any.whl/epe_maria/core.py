import numpy as np
from epe_maria.utils import to_coeffs
from epe_maria.metrics import phi, delta_phi, phi_star
from epe_maria.mollify import mollify_coefficients

class MetricConfig:
    def __init__(self, domain=(-1, 1), basis='chebyshev', 
                 normalize=True, alpha=0.5, beta=0.5, mollify=False):
        self.domain = domain
        self.basis = basis
        self.normalize = normalize
        self.alpha = alpha
        self.beta = beta
        self.mollify = mollify

def normalize_coeffs(coeffs, method='l2'):
    coeffs = np.array(coeffs, dtype=np.float64)
    if method == 'l2':
        norm = np.linalg.norm(coeffs)
        return coeffs / norm if norm > 0 else coeffs
    elif method == 'max':
        max_val = np.max(np.abs(coeffs))
        return coeffs / max_val if max_val > 0 else coeffs
    elif method == 'none':
        return coeffs
    else:
        raise ValueError(f"Unsupported normalization method: {method}")

class KernelAudit:
    def __init__(self, kernel='laplacian', threshold=0.05):
        self.kernel = kernel
        self.threshold = threshold

    def compare(self, structure_A, structure_B):
        divergence = np.abs(np.array(structure_A) - np.array(structure_B))
        return divergence

def compute_metrics(f, g, config: MetricConfig):
    metrics = {
        'ϝ': phi(f, g, domain=config.domain, mollify=config.mollify),
        'δϝ': delta_phi(f, g, domain=config.domain, mollify=config.mollify),
        'ϝ*': phi_star(f, g, alpha=config.alpha, beta=config.beta,
                       domain=config.domain, mollify=config.mollify)
    }
    return metrics
