from sympy import symbols
from symbolic_metrics import (
    phi_symbolic,
    delta_phi_symbolic,
    phi_star_symbolic,
    symbolic_group_audit
)
from symbolic_visuals import plot_group_divergence

x = symbols('x')

# Individual functions
f = x**3 + 2*x + 1
g = x**3 - x + 1

print("ϝ =", phi_symbolic(f, g))
print("δϝ =", delta_phi_symbolic(f, g))
print("ϝ* =", phi_star_symbolic(f, g, alpha=0.6, beta=0.4))

# Group audit
group_a = [x**2 + x, x**2 - 1]
group_b = [x**2 + 2*x + 1, x**2 - x]
groups = {'Group A': group_a, 'Group B': group_b}

phi_val = symbolic_group_audit(groups, metric='phi')
delta_val = symbolic_group_audit(groups, metric='delta')

print("Group φ audit:", phi_val)
print("Group δφ audit:", delta_val)

# Visualization
group_names = ['Group A', 'Group B']
plot_group_divergence(group_names, [phi_val, delta_val], metric_name='φ and δφ')
