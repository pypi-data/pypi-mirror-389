import numpy as np
from epe_maria.metrics import phi, delta_phi, phi_star

def test_phi_basic():
    f = lambda x: x**2
    g = lambda x: x**2 + 1
    score = phi(f, g)
    assert score > 0

def test_phi_mollified():
    f = lambda x: x**2
    g = lambda x: x**2 + 1
    score_raw = phi(f, g, mollify=False)
    score_mollified = phi(f, g, mollify=True)
    assert score_mollified <= score_raw

def test_delta_phi_behavior():
    f = lambda x: np.sin(x)
    g = lambda x: np.cos(x)
    score = delta_phi(f, g)
    assert score > 0

def test_phi_star_fusion():
    f = lambda x: x
    g = lambda x: x + 2
    fusion = phi_star(f, g, alpha=0.3, beta=0.7)
    assert fusion > 0
