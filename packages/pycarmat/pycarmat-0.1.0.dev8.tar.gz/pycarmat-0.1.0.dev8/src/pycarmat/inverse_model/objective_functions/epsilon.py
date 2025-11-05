from copy import deepcopy

from numpy import ones_like, abs, asarray
from qosm.propagation import PW


def cost_function(self, x, freq_ghz, metric_fn, kwargs):
    config = kwargs['config']
    s21_meas = kwargs['s21_meas']
    phys_constraint = kwargs.get('phys_constraint', True)
    coefficient_3d = self.params.get('coefficient_3d', 10)

    self.params['mut'][self.s_idx]['epsilon_r'] = x[0] + 1j * x[1]
    _, _, s21_model, _ = PW.simulate(config, freq_ghz)

    # Error calculation
    err1 = 1 - s21_meas / s21_model
    err2 = 1 - s21_model / s21_meas

    penalty = (1e10 if x[1] > 0 else 0) if phys_constraint else 0

    return abs(metric_fn((1 / coefficient_3d) * abs(err1 * err2)) + penalty)
