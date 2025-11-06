from epe_maria.core import compute_metrics, MetricConfig
from epe_maria.benchmark import attach_badge_to_report

def drift(f, g, domain=None):
    if domain is None:
        domain = range(-10, 11)
    return sum(f(x) - g(x) for x in domain) / len(domain)

def curvature(f, domain=None):
    if domain is None:
        domain = range(-10, 11)
    def second_derivative(func, x, h=1e-5):
        return (func(x + h) - 2 * func(x) + func(x - h)) / (h ** 2)
    return sum(abs(second_derivative(f, x)) for x in domain) / len(domain)

def monitor_model_drift(f, g, config=None):
    if config is None:
        config = MetricConfig()
    metrics = compute_metrics(f, g, config)
    alert = {
        'ϝ': metrics['ϝ'] > 0.2,
        'δϝ': metrics['δϝ'] > 0.2,
        'ϝ*': metrics['ϝ*'] > 0.25,
        'curvature_f': curvature(f, config.domain) > 10.0,
        'curvature_g': curvature(g, config.domain) > 10.0
    }
    report = {
        'metrics': metrics,
        'alert': alert
    }
    return attach_badge_to_report(report)
