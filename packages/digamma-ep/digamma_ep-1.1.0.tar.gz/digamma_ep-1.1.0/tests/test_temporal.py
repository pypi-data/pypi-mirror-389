import numpy as np

def second_order_divergence(series1, series2):
    """
    Calcula a divergência de segunda ordem entre duas séries temporais.
    Mede a diferença na aceleração (curvatura).
    """
    d2_series1 = np.diff(series1, n=2)
    d2_series2 = np.diff(series2, n=2)

    min_len = min(len(d2_series1), len(d2_series2))
    d2_series1 = d2_series1[:min_len]
    d2_series2 = d2_series2[:min_len]

    divergence = np.linalg.norm(d2_series1 - d2_series2)
    return divergence

# Teste direto
series1 = np.array([1, 2, 4, 7, 11])  # aceleração crescente
series2 = np.array([1, 2, 3, 4, 5])   # aceleração constante

delta2_phi = second_order_divergence(series1, series2)
print("Second-order divergence (δ²ϝ) =", delta2_phi)
