from symbolic_temporal import simulate_temporal_drift, plot_temporal_phi
from sympy import symbols

x = symbols('x')
base = x**2 + 1

drifted = simulate_temporal_drift(base, steps=6, drift_type='linear')
plot_temporal_phi(drifted)
