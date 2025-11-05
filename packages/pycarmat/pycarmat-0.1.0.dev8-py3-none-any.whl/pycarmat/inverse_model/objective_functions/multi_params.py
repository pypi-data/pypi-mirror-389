from copy import deepcopy

from numpy import ones_like, abs, asarray


def cost_function(x, freq_ghz, metric_fn, kwargs):
    s21_meas = kwargs['s21_meas']
    s11_meas = kwargs.get('s11_meas', None)
    use_abs = kwargs.get('use_abs', True)

    model = kwargs.get('model')
    config = kwargs.get('config')
    unknown_layer = kwargs.get('unknown_layer')
    air_gap_layer = kwargs.get('air_gap_layer', None)
    theta_weight_array = kwargs.get('theta_weight_array')
    theta_y_deg_array = kwargs.get('theta_weight_array', asarray((0, )))

    _config = deepcopy(config)
    if len(x) == 2:
        _config['mut'][unknown_layer]['epsilon_r'] = x[0] + x[1] * 1j
    else:
        if len(x) == 4:
            # thickness_sample, thickness_air, eps_re, eps_im
            _config['mut'][unknown_layer]['thickness'] = x[0] * 1e-3
            _config['mut'][air_gap_layer]['thickness'] = x[1] * 1e-3
            _config['mut'][unknown_layer]['epsilon_r'] = x[2] + x[3] * 1j
        else:
            # thickness_air/sample, eps_re, eps_im
            _config['mut'][unknown_layer]['epsilon_r'] = x[1] + x[2] * 1j

            index = air_gap_layer if air_gap_layer is not None else unknown_layer
            _config['mut'][index]['thickness'] = x[0] * 1e-3

    # _w =  self.theta_weight_array
    _w = ones_like(theta_weight_array)
    _arr_sim = []
    _arr_meas = [abs(s11_meas[0]), ] if s11_meas is not None else []
    for ii, theta_deg in enumerate(theta_y_deg_array):
        _config['sample_attitude_deg'] = (0, theta_deg, 0)
        _s11, _, _s21, _ = model.simulate(_config, freq_ghz)
        if ii == 0 and s11_meas is not None:
            _arr_sim.append(abs(_s11) * _w[ii])
        _arr_sim.append(_s21.real * _w[ii])
        _arr_sim.append(_s21.imag * _w[ii])
        _arr_meas.append(s21_meas[ii].real * _w[ii])
        _arr_meas.append(s21_meas[ii].imag * _w[ii])
        if use_abs:
            _arr_sim.append(abs(_s21) * _w[ii])
            _arr_meas.append(abs(s21_meas[ii]) * _w[ii])

    return metric_fn(asarray(_arr_meas), asarray(_arr_sim))
