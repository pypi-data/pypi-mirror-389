import numpy as np

def mollify_coefficients(coeffs, kernel=None):
    """
    Apply Gaussian mollification to a coefficient vector.
    
    Parameters:
    - coeffs: list or np.ndarray of polynomial coefficients
    - kernel: optional smoothing kernel (default: Gaussian [0.106, 0.788, 0.106])
    
    Returns:
    - mollified: np.ndarray of smoothed coefficients
    """
    if kernel is None:
        kernel = np.array([0.106, 0.788, 0.106])  # Gaussian approximation
    padded = np.pad(coeffs, (1, 1), mode='constant')
    mollified = np.convolve(padded, kernel, mode='valid')
    return mollified
