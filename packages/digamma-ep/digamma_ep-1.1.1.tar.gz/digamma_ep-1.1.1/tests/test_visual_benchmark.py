import numpy as np
import matplotlib.pyplot as plt
from epe_maria.benchmark import benchmark_epe_vs_ks

# Simulação
reference = np.random.normal(0, 1, 1000)
model_drift = np.random.normal(0.3, 1, 1000)
model_curved = np.array([np.sin(x/10) for x in range(1000)]) + np.random.normal(0, 0.1, 1000)

# Benchmark
result_drift = benchmark_epe_vs_ks(reference, model_drift)
result_curved = benchmark_epe_vs_ks(reference, model_curved)

# Plot
fig, axs = plt.subplots(2, 2, figsize=(12, 6))
axs[0, 0].hist(reference, bins=50, alpha=0.6, label='Reference')
axs[0, 0].hist(model_drift, bins=50, alpha=0.6, label='Drift')
axs[0, 0].set_title("Drift simples")
axs[0, 0].legend()

axs[0, 1].bar(result_drift.keys(), result_drift.values(), color='orange')
axs[0, 1].set_title("Scores Epe vs KS (Drift)")

axs[1, 0].hist(reference, bins=50, alpha=0.6, label='Reference')
axs[1, 0].hist(model_curved, bins=50, alpha=0.6, label='Curvado')
axs[1, 0].set_title("Curvatura alterada")
axs[1, 0].legend()

axs[1, 1].bar(result_curved.keys(), result_curved.values(), color='green')
axs[1, 1].set_title("Scores Epe vs KS (Curvatura)")

plt.tight_layout()
plt.show()
