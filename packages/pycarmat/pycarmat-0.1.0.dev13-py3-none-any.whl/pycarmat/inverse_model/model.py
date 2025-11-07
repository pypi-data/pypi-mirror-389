from copy import deepcopy

from numpy import asarray, nan, linspace, isscalar, zeros, zeros_like, isnan, nanmedian
from qosm import load_config_from_toml
from scipy.interpolate import interp1d
from scipy.optimize import minimize
import skrf as rf

from pycarmat.inverse_model.analyse.analyze_angle_independence import analyze_angle_independence
from pycarmat.inverse_model.tools import linear_regression_from_interp, poly_fit_cplx, load_s2p_file, linear_regression


class CostFunction:
    def __init__(self, fn, score_fn):
        self.fn = fn
        self.score_fn = score_fn

    def eval(self, x, freq_ghz, kwargs):
        return self.fn(x, freq_ghz, self.score_fn, kwargs)

class InverseProblem:
    def __init__(self, config_file, cost_fn, score_fn, unknown_layer: int = 0):
        self.cost_function = CostFunction(cost_fn, score_fn)

        self.theta_y_deg_array = (0, )
        self.theta_weight_array = (1, )
        self.frequencies_ghz = []
        self.unknown_layer = unknown_layer

        # Data containers
        self.raw_data = []
        self.filtered_data = []
        self.data_list = []
        self.data = []
        self.angles_pairs = {}
        self.model = None

        # initial config
        if isinstance(config_file, dict):
            self.config = config_file
        else:
            self.config = load_config_from_toml(config_file, load_csv=True)
        self.frequencies_ghz = linspace(
            float(self.config['sweep']['range'][0]),
            float(self.config['sweep']['range'][1]),
            int(self.config['sweep']['num_points']),
            True
        )
        for layer in self.config['mut']:
            if not isscalar(layer['epsilon_r']):
                layer['epsilon_r'] = linear_regression_from_interp(self.frequencies_ghz, layer['epsilon_r'])

        # estimated config
        self.config_est = None

        # Options
        self.options = {
            'maxiter': 10000,
            'xatol': 1e-3,
            'fatol': 1e-10,
            'adaptive': True
        }

    def set_tol(self, x_tol, f_tol, adaptive: bool = True):
        self.options['xatol'] = x_tol
        self.options['fatol'] = f_tol
        self.options['adaptive'] = adaptive

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
            res = self.fit(x=initial_guess_values, freq_idx=_i, model=model)
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

        n_points = len(_frequencies_ghz)
        if n_points >= 3:
            interp_kind = 'quadratic'
        elif n_points == 2:
            interp_kind = 'linear'
        else:  # n_points == 1
            interp_kind = 'nearest'

        epsr_est_raw = interp1d(_frequencies_ghz, _e[:, 0] + 1j * _e[:, 1], kind=interp_kind, fill_value="extrapolate")
        epsr_est = linear_regression(_frequencies_ghz, _e[:, 0], _e[:, 1], slope_mode='less')
        if len(initial_guess_values) >= 3:
            h_est_mm = nanmedian(_h, axis=0)
        else:
            h_est_mm = nan

        if self.config_est is None:
            self.config_est = deepcopy(self.config)

        if len(self.config_est['mut']) > 1:
            # multi-layer case
            if len(initial_guess_values) >= 2:
                self.config_est['mut'][self.unknown_layer]['epsilon_r'] = epsr_est
            elif len(initial_guess_values) >= 3:
                self.config_est['mut'][self.unknown_layer]['thickness'] = h_est_mm[0] * .001
            else:
                raise AssertionError(f'Unexpected number of variables (read: {len(initial_guess_values)})')
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

    def fit(self, x, freq_idx, model, args=None):
        if args is None:
            args = {}
        freq_ghz = self.frequencies_ghz[freq_idx]
        if len(x) == 2:
            # only permittivity (real, imag)
            bounds = ([1, 20], [-10., -0.00001])
        elif len(x) == 3:
            # thickness, permittivity (real, imag)
            bounds = ([0.0001, 50], [1, 10.], [-10., -1e-6])
        else:
            # thickness1, thickness2, permittivity (real, imag)
            bounds = ([0.0001, 50], [0.0001, 50], [1, 10.], [-10., -1e-6])

        _args = {
            's21_meas': self.data[:, freq_idx, 1, 0],
            's11_meas': None,
            'use_abs': True,
            'config': self.config,
            'unknown_layer': self.unknown_layer,
            'model': model
        }
        for key, val in args.items():
            _args[key] = val

        res = minimize(
            self.cost_function.eval,
            x0=asarray(x),
            args=(freq_ghz, _args),
            bounds=bounds,
            options=self.options,
            method='Nelder-Mead'
        )
        guess = res.x

        if len(x) == 2:
            return {
                'epsilon_r': (guess[0], guess[1]),
                'thickness_mm': (nan,),
                'guess': guess,
                'success': res.success,
            }
        elif len(x) == 3:
            return {
                'epsilon_r': (guess[1], guess[2]),
                'thickness_mm': (guess[0],),
                'guess': guess,
                'success': res.success,
            }
        else:
            return {
                'epsilon_r': (guess[2], guess[3]),
                'thickness_mm': (guess[0], guess[1]),
                'guess': guess,
                'success': res.success,
            }

    def load_experimental_data(self,
                               s2p_path: str,
                               poly_fit_degree: int = 0,
                               filter_window_length: int = 51,
                               filter_poly_order: int = 5,
                               n_angles_to_use: int = 1):
        """
        Load experimental S21 measurements from S2P files.

        Parameters
        ----------
        poly_fit_degree : int
            Degree of polynomial fit to smooth S21 vs angle. If 0, no smoothing.
        filter_window_length: int
            Window size to smooth S21 vs frequency. Defaults to 101
        filter_poly_order: int
            Degree of polynomial fit to smooth S21 vs frequency. Defaults to 5
        """

        # Load raw data with auto-selection of angles
        if s2p_path.endswith('.s2p'):
            # In this case, suppose that only normal incidence is used
            self.raw_data = rf.Network(s2p_path)
            self.filtered_data = (load_s2p_file(s2p_path, filter_window_length, filter_poly_order), )
            self.theta_y_deg_array = asarray((0, ), dtype=float)
            self.theta_weight_array = asarray((1, ), dtype=float)
            sizes = self.filtered_data[0].s.shape
            self.data = zeros((1, sizes[0], sizes[1], sizes[2]), dtype=complex)
            self.data[0, :, :, :] = self.filtered_data[0].s
            self.frequencies_ghz = self.raw_data.f * 1e-9
        else:
            _angles_deg, self.raw_data, self.filtered_data, _angle_weights, opts = analyze_angle_independence(
                s2p_path,
                n_angles_to_select=n_angles_to_use, use_pairs=True,
                smoothing_window=filter_window_length,
                smoothing_poly=filter_poly_order)
            _, _, _, _, self.angles_pairs = opts

            self.theta_y_deg_array = asarray(_angles_deg, dtype=float)
            self.theta_weight_array = asarray(_angle_weights, dtype=float)

            # Perform polyfit if requested
            if poly_fit_degree > 0:
                s21_wrt_angle = zeros((self.theta_y_deg_array.shape[0], self.frequencies_ghz.shape[0]), dtype=complex)
                s21_wrt_angle_poly = zeros((self.theta_y_deg_array.shape[0], self.frequencies_ghz.shape[0]),
                                              dtype=complex)
                for i, mut in enumerate(self.filtered_data):
                    s21_wrt_angle[i, :] = deepcopy(mut.s[:, 1, 0])

                for j, freq_GHz in enumerate(self.frequencies_ghz):
                    s21_wrt_angle_poly[:, j] = poly_fit_cplx(self.theta_y_deg_array, s21_wrt_angle[:, j],
                                                             deg=poly_fit_degree)

                for i, mut in enumerate(self.filtered_data):
                    s = zeros_like(mut.s)
                    s[:, 1, 0] = s21_wrt_angle_poly[i, :]
                    s[:, 0, 1] = s21_wrt_angle_poly[i, :]
                    self.data_list.append(rf.Network(s=s, f=mut.f))
            else:
                self.data_list = self.filtered_data

            # Prepare measurement array
            _data = zeros((len(self.theta_y_deg_array), len(self.frequencies_ghz), 2, 2), dtype=complex)
            for i, angle_deg in enumerate(self.theta_y_deg_array):
                for j, _ in enumerate(self.frequencies_ghz):
                    _data[i, j, 0, 0] = self.data_list[i].s[j, 0, 0]
                    _data[i, j, 0, 1] = self.data_list[i].s[j, 0, 1]
                    _data[i, j, 1, 0] = self.data_list[i].s[j, 1, 0]
                    _data[i, j, 1, 1] = self.data_list[i].s[j, 1, 1]
            self.data = _data

            # frequency array (GHz)
            self.frequencies_ghz = self.raw_data[0].f * 1e-9
