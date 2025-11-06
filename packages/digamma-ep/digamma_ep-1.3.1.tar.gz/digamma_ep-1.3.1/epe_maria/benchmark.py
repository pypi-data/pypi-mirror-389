from epe_maria.metrics import phi
from scipy.stats import ks_2samp

def benchmark_epe_vs_ks(reference, current):
    """
    Compara a métrica Epe (ϝ) com o KS-test.
    Retorna os scores e interpretações.
    """
    epe_score = phi(reference, current)
    ks_stat, ks_p = ks_2samp(reference, current)

    result = {
        "ϝ (Epe)": round(epe_score, 6),
        "KS-stat": round(ks_stat, 6),
        "KS-p": round(ks_p, 6),
        "KS drift detected": ks_p < 0.05
    }
    return result


def assign_compliance_badge(report, thresholds=None):
    """
    Assigns a symbolic badge based on audit alert status.
    """
    if thresholds is None:
        thresholds = {'ϝ': 0.2, 'δϝ': 0.2, 'ϝ*': 0.25, 'curvature': 10.0}

    alerts = report.get('alert', {})
    if all(not v for v in alerts.values()):
        return '✅ Stable'
    elif alerts.get('ϝ*'):
        return '⚠️ Divergent'
    elif alerts.get('δϝ') or alerts.get('curvature_f') or alerts.get('curvature_g'):
        return '🌀 Unstable'
    else:
        return '🔍 Review'


def attach_badge_to_report(report, thresholds=None):
    """
    Adds a badge field to the report dictionary based on symbolic audit status.
    """
    badge = assign_compliance_badge(report, thresholds)
    report['badge'] = badge
    return report
