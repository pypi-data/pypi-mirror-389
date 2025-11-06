import numpy as np
from .mollify import mollify_coefficients

def phi(f, g, domain=None, mollify=False):
    """
    Structural divergence between two functions f and g.
    Measures average absolute difference over a domain.
    Optionally applies mollification to the signal.
    """
    if domain is None:
        domain = range(-10, 11)

    f_vals = np.array([f(x) for x in domain])
    g_vals = np.array([g(x) for x in domain])

    if mollify:
        f_vals = mollify_coefficients(f_vals)
        g_vals = mollify_coefficients(g_vals)

    differences = np.abs(f_vals - g_vals)
    return np.mean(differences)


def delta_phi(f, g, domain=None, mollify=False):
    """
    Rate divergence between two functions f and g.
    Measures average absolute difference in derivatives.
    Optionally applies mollification to the derivative signal.
    """
    if domain is None:
        domain = range(-10, 11)

    def derivative(func, x, h=1e-5):
        return (func(x + h) - func(x - h)) / (2 * h)

    f_derivs = np.array([derivative(f, x) for x in domain])
    g_derivs = np.array([derivative(g, x) for x in domain])

    if mollify:
        f_derivs = mollify_coefficients(f_derivs)
        g_derivs = mollify_coefficients(g_derivs)

    rate_diffs = np.abs(f_derivs - g_derivs)
    return np.mean(rate_diffs)


def phi_star(f, g, alpha=0.5, beta=0.5, domain=None, mollify=False):
    """
    Fusion metric combining structural and rate divergence.
    Weighted sum of phi and delta_phi.
    Optionally applies mollification to both components.
    """
    if domain is None:
        domain = range(-10, 11)

    phi_val = phi(f, g, domain, mollify=mollify)
    delta_val = delta_phi(f, g, domain, mollify=mollify)

    return alpha * phi_val + beta * delta_val


def mollify_series(signal, kernel='gaussian', bandwidth=0.5):
    """
    Legacy smoothing function (not used in phi/δϝ).
    Retained for compatibility.
    """
    from scipy.ndimage import gaussian_filter1d

    if kernel == 'gaussian':
        return gaussian_filter1d(signal, sigma=bandwidth)
    elif kernel == 'laplacian':
        smoothed = np.copy(signal)
        for i in range(1, len(signal)-1):
            smoothed[i] = (signal[i-1] + signal[i] + signal[i+1]) / 3
        return smoothed
    else:
        raise ValueError(f"Unsupported kernel: {kernel}")
