from epe_maria.benchmark import attach_badge_to_report

def test_badge_assignment_stable():
    report = {
        'metrics': {'ϝ': 0.1, 'δϝ': 0.1, 'ϝ*': 0.1},
        'alert': {'ϝ': False, 'δϝ': False, 'ϝ*': False,
                  'curvature_f': False, 'curvature_g': False}
    }
    result = attach_badge_to_report(report)
    assert result['badge'] == '✅ Stable'

def test_badge_assignment_divergent():
    report = {
        'metrics': {'ϝ': 0.1, 'δϝ': 0.1, 'ϝ*': 0.3},
        'alert': {'ϝ': False, 'δϝ': False, 'ϝ*': True,
                  'curvature_f': False, 'curvature_g': False}
    }
    result = attach_badge_to_report(report)
    assert result['badge'] == '⚠️ Divergent'
