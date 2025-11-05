from copy import deepcopy

from numpy import  nan, zeros, zeros_like, nanmedian, sum, isnan
from scipy.interpolate import interp1d

from pycarmat.inverse_model.model import InverseProblem
from pycarmat.inverse_model.objective_functions.multi_params import cost_function
from pycarmat.inverse_model.tools import linear_regression


class EnhancedInverseProblem(InverseProblem):
    def __init__(self, config_file, score_fn, unknown_layer: int, air_gap_layer: int = 1):
        super().__init__(config_file, cost_function, score_fn, unknown_layer)
        self.air_gap_layer = air_gap_layer

    def compute_weights(self, frequency_step: int = 1):
        _frequencies_ghz = self.frequencies_ghz[::frequency_step]
        weights = zeros_like(_frequencies_ghz)

        for i, angle_deg in enumerate(self.theta_y_deg_array):
            raw_signal = self.raw_data[i].s[::frequency_step, 1, 0]
            noise_estimate = abs(raw_signal - self.data[i].s[::frequency_step, 1, 0])
            _weights = 1 / (noise_estimate + 1e-8)
            _weights = _weights
            weights += _weights
        weights /= len(self.theta_y_deg_array)
        weights /= sum(weights)

        return weights

    def sweep_fit(self, model, initial_guess_values, frequency_step: int = 1, pbar=None):
        _frequencies_ghz = self.frequencies_ghz[::frequency_step]
        _e = zeros((_frequencies_ghz.shape[0], 2))
        if len(initial_guess_values) >= 3:
            _h = zeros((_frequencies_ghz.shape[0], 2 if len(initial_guess_values) == 4 else 1))
        else:
            _h = None

        if pbar is not None:
            pbar.reset(_frequencies_ghz.shape[0])

        _i = 0
        for k in range(len(_frequencies_ghz)):
            res = self.fit(x=initial_guess_values, freq_idx=_i, model=model, args={
                'unknown_layer': self.unknown_layer,
                'air_gap_layer': self.air_gap_layer,
            })
            if not res['success']:
                raise RuntimeError("Unable to fit model")
            if len(initial_guess_values) >= 3:
                tck = res['thickness_mm']
                _h[k, :] = (tck[0], tck[1]) if len(tck) > 1 else (tck[0],)
            _e[k, :] = res['epsilon_r']
            initial_guess_values = res['guess']
            if pbar is not None:
                pbar.update(1)
            _i += frequency_step
        if pbar is not None:
            pbar.close()

        epsr_est_raw = interp1d(_frequencies_ghz, _e[:, 0] + 1j * _e[:, 1], kind='quadratic')
        wh = self.compute_weights(frequency_step=frequency_step)
        epsr_est = linear_regression(_frequencies_ghz, _e[:, 0], _e[:, 1], slope_mode='less', weights=wh)
        if len(initial_guess_values) >= 3:
            h_est_mm = .5 * (nanmedian(_h, axis=0) + sum(_h * wh.reshape((-1, 1)), axis=0))
        else:
            h_est_mm = nan

        if self.config_est is None:
            self.config_est = deepcopy(self.config)

        if len(self.config_est['mut']) > 1:
            # multi-layer case
            if len(initial_guess_values) >= 2:
                self.config_est['mut'][self.unknown_layer]['epsilon_r'] = epsr_est
            if len(initial_guess_values) >= 3:
                self.config_est['mut'][self.unknown_layer]['thickness'] = h_est_mm[0] * .001
            if len(initial_guess_values) == 4:
                self.config_est['mut'][self.air_gap_layer]['thickness'] = h_est_mm[1] * .001
        else:
            # single-layer case
            self.unknown_layer = 0
            self.config_est['mut'][0]['epsilon_r'] = epsr_est
            if not isnan(h_est_mm):
                self.config_est['mut'][0]['thickness'] = h_est_mm * .001

        if len(initial_guess_values) >= 3:
            return epsr_est, epsr_est_raw, h_est_mm
        else:
            return epsr_est, epsr_est_raw