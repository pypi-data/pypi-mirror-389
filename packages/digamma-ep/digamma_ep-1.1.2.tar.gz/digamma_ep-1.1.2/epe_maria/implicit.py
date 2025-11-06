import numpy as np

def implicit_gradient(omega_f, omega_g, J_f, J_g):
    """
    Compute structural gradient propagation for F(Ω(f), Ω(g)) = 0
    using Jacobians in coefficient space.

    Parameters:
    - omega_f: np.ndarray, coefficient vector of f
    - omega_g: np.ndarray, coefficient vector of g
    - J_f: np.ndarray, Jacobian matrix ∂F/∂Ω(f)
    - J_g: np.ndarray, Jacobian matrix ∂F/∂Ω(g)

    Returns:
    - omega_g_prime: np.ndarray, propagated gradient of g
    """
    J_g_inv = np.linalg.pinv(J_g)
    return -np.dot(J_g_inv, np.dot(J_f, omega_f))


#Usage example
from epe_maria.implicit import implicit_gradient

# Example coefficient vectors
omega_f = np.array([1, 2, 3])
omega_g = np.array([0.5, -1, 4])

# Example Jacobians (3×3)
J_f = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
J_g = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]])

# Compute propagated gradient
omega_g_prime = implicit_gradient(omega_f, omega_g, J_f, J_g)
print("Propagated gradient:", omega_g_prime)

