from time import sleep

import matplotlib.pyplot as plt
import RsInstrument
import skrf as rf
import numpy as np
from scipy.interpolate import interp1d

def wrap(unwrapped_phase_rad: float | np.ndarray) -> float | np.ndarray:
    """
    Wraps the phase between -π and π.

    Args:
        unwrapped_phase_rad (float | np.ndarray): The unwrapped phase in radians.

    Returns:
        float | np.ndarray: The wrapped phase in radians, within the range [-π, π].

    Notes:
        - If `unwrapped_phase_rad` is a numpy array, the operation is applied element-wise.
        - This function is useful for handling phase discontinuities in signal processing.
    """
    return (unwrapped_phase_rad + np.pi) % (2 * np.pi) - np.pi


class VNA:
    """
    A class to interface with a Vector Network Analyzer (VNA).

    This class provides methods for configuring, controlling, and retrieving S-parameter
    measurements from a VNA using the RsInstrument API. It supports real instrument
    communication as well as a simulation mode.
    """

    def __init__(self, ip_address: str, simulate: bool = False, load: str = None, reset_instr: bool = False):
        """
        Initializes the VNA connection and configures simulation mode if required.

        Args:
            ip_address (str): The IP address of the VNA for TCP/IP communication.
            simulate (bool, optional): If True, enables simulation mode. Default is False.
            load (str, optional): Path to an S2P file for simulation mode. Default is None.
            reset_instr (bool, optional): If True, resets the VNA to default settings. Default is False.

        """
        self.ip = f'TCPIP::{ip_address}::instr'
        self.vna = None
        self.frequency_sweep = (0, 0, 0)
        self._simulate = simulate
        self._reset_instr = reset_instr
        self._sim_file = load

    def __enter__(self):
        """
        Establishes a connection to the VNA when entering a context.

        Returns:
            VNA: The VNA instance with an active connection.

        Raises:
            ConnectionError: If the instrument cannot be accessed.
        """
        try:
            self.vna = RsInstrument.RsInstrument(self.ip, reset=self._reset_instr, id_query=True,
                                                 options=f'Simulate={self._simulate}')
        except RsInstrument.Internal.InstrumentErrors.ResourceError as e:
            raise ConnectionError(str(e))
        return self

    def __exit__(self, *exc):
        """
        Closes the VNA connection when exiting a context.

        Args:
            *exc (tuple): Exception type, value, and traceback (if any), passed automatically by the context manager.
        """
        if self.vna is not None:
            self.reset()
            self.vna.close()
            self.vna = None

    @property
    def frequencies_GHz(self) -> np.ndarray:
        """
        Computes the frequency sweep in GHz as a numpy array.
        The frequencies are generated using `numpy.linspace` and the sweep settings defined in `frequency_sweep`.

        Returns:
            np.ndarray: A numpy array of frequencies in GHz, equally spaced between `freq_start` and `freq_end`.
        """
        freq_start, freq_end, num_points = self.frequency_sweep
        return np.linspace(freq_start, freq_end, int(num_points), endpoint=True)

    def _com_prep(self, timeout: float = 50000) -> None:
        """
        Prepares the communication settings for the VNA.

        Args:
            timeout (float, optional): The timeout value in milliseconds. Default is 50000 ms.
        """
        self.vna.visa_timeout = timeout
        self.vna.opc_timeout = timeout
        self.vna.instrument_status_checking = True
        self.vna.clear_status()

    def _load_s2p_data(self, s_param: str, return_format: str):
        """
        Loads S-parameter data from an S2P file or generates pseudo-random data for simulation.

        Args:
            s_param (str): The S-parameter to retrieve (e.g., 'S11', 'S12', 'S21', 'S22').
            return_format (str): The desired format for the data ('RI' or 'DB').

        Returns:
            tuple[list[float], list[float]]: The real/imaginary or magnitude/phase data.

        Raises:
            RuntimeError: If the frequency range of the S2P file does not match the required sweep.
        """
        if self._sim_file is None:
            if return_format.upper() == 'RI':
                data_1 = np.random.uniform(low=0.05, high=0.1, size=(self.frequency_sweep[2],))
            else:
                data_1 = np.random.uniform(low=-20, high=-1.5, size=(self.frequency_sweep[2],))
            data_2 = wrap(
                np.random.uniform(low=0.1, high=0.9, size=(1,)) * self.frequencies_GHz
                + np.random.uniform(low=-2, high=2, size=(1,)))
        else:
            s2p_data = rf.Network(self._sim_file)
            if np.min(s2p_data.f * 1e-9) != self.frequency_sweep[0] or \
                    np.max(s2p_data.f * 1e-9) != self.frequency_sweep[1]:
                raise RuntimeError('S2P file not in same frequency range')

            idxs = {'S11': (0, 0), 'S12': (0, 1), 'S21': (1, 0), 'S22': (1, 1)}
            i1, i2 = idxs[s_param]
            if return_format.upper() == 'RI':
                data_1 = np.real(s2p_data.s[:, i1, i2])
                data_2 = np.imag(s2p_data.s[:, i1, i2])
            else:
                data_1 = s2p_data.s_db[:, i1, i2]
                data_2 = np.angle(s2p_data.s[:, i1, i2], deg=True)

            _sim_freq_GHz = s2p_data.f * 1e-9
            interp_func1 = interp1d(_sim_freq_GHz, data_1, kind='cubic')
            interp_func2 = interp1d(_sim_freq_GHz, data_2, kind='cubic')
            data_1 = interp_func1(self.frequencies_GHz)
            data_2 = interp_func2(self.frequencies_GHz)

        return data_1.tolist(), data_2.tolist()

    def set_sweep(self, freq_start_GHz: float, freq_end_GHz: float, num_pts: int, bandwidth: str) -> None:
        """
        Configures the frequency sweep settings for the VNA.

        Args:
            freq_start_GHz (float): The starting frequency of the sweep in GHz.
            freq_end_GHz (float): The ending frequency of the sweep in GHz.
            num_pts (int): The number of points in the frequency sweep.
            bandwidth (float): Measure bandwidth in Hz
        """
        self.vna.write_str(f':SENSe1:FREQuency:STARt {freq_start_GHz} GHZ')
        self.vna.write_str(f':SENSe1:FREQuency:STOP {freq_end_GHz} GHZ')
        self.vna.write_str(f':SENSe1:SWEep:POINts {num_pts}')
        self.vna.write_str(f':SENSe1:BWIDth:RESolution {bandwidth.upper()}')
        self.vna.write_str(':SENSe1:BWIDth:RESolution:DREDuction OFF')
        self.frequency_sweep = (freq_start_GHz, freq_end_GHz, num_pts)

    def sweep(self, return_format: str = 'RI') -> np.ndarray | tuple:
        """
        Performs a single frequency sweep measurement for all S-parameters.

        Args:
            return_format (str, optional): The format of the returned data ('RI' or 'DB'). Default is 'RI'.

        Returns:
            np.ndarray | dict: The measured data in the specified format.

        Raises:
            RuntimeError: If an invalid `return_format` is provided.
        """
        if return_format.upper() == 'RI':
            _cmp_ctrl = 0
            _trace1_format = 'REAL'
            _trace2_format = 'IMAG'
        elif return_format.upper() == 'DB':
            _cmp_ctrl = -999
            _trace1_format = 'MLOG'
            _trace2_format = 'PHAS'
        else:
            raise RuntimeError('Invalid format: %s' % return_format)

        # erase previous data
        self.vna.write_str('CALCulate:PARameter:DELete:ALL')

        # enable SINGLE SWEEP
        self.vna.write_str('INIT1:CONT OFF')

        # create trace for the S-
        _s_params = ('S11', 'S12', 'S21', 'S22')
        id_trace = 1

        for s_param in _s_params:
            self.vna.write_str(f'CALC1:PAR:SDEF "Trc{id_trace}","{s_param}"')
            self.vna.write_str(f'CALC1:PAR:MEAS "Trc{id_trace}","{s_param}"')
            self.vna.write_str(f'CALC1:PAR:SEL "Trc{id_trace}"')
            self.vna.write_str(f'CALC1:FORM {_trace1_format}')
            id_trace += 1

            self.vna.write_str(f'CALC1:PAR:SDEF "Trc{id_trace}","{s_param}"')
            self.vna.write_str(f'CALC1:PAR:MEAS "Trc{id_trace}","{s_param}"')
            self.vna.write_str(f'CALC1:PAR:SEL "Trc{id_trace}"')
            self.vna.write_str(f'CALC1:FORM {_trace2_format}')
            id_trace += 1

        # Launch the sweep
        self.vna.write_str('INIT1')

        _cmp_ctrl = (0 if return_format.upper() == 'RI' else -999)
        data_s11_1 = [_cmp_ctrl, ]
        data_s11_2 = None
        data_s12_1 = [_cmp_ctrl, ]
        data_s12_2 = None
        data_s21_1 = [_cmp_ctrl, ]
        data_s21_2 = None
        data_s22_1 = [_cmp_ctrl, ]
        data_s22_2 = None
        data_float_read = [0, ]
        while (np.min(data_s11_1) == _cmp_ctrl or np.min(data_s12_1) == _cmp_ctrl or np.min(data_s21_1) == _cmp_ctrl or
               np.min(data_s22_1) == _cmp_ctrl or np.sum(np.isnan(data_float_read)) > 0):
            data_str = self.vna.query_str('CALC:DATA:DALL? FDATA')
            if data_str == 'Simulating':
                data_s11_1, data_s11_2 = self._load_s2p_data('S11', return_format)
                data_s12_1, data_s12_2 = self._load_s2p_data('S12', return_format)
                data_s21_1, data_s21_2 = self._load_s2p_data('S21', return_format)
                data_s22_1, data_s22_2 = self._load_s2p_data('S22', return_format)
            elif data_str:
                data_float_read = [float(d) for d in data_str.split(',')]
                if len(data_float_read) != (8 * self.frequency_sweep[2]):
                    continue

                data_float = np.array(data_float_read).reshape((-1, self.frequency_sweep[2]))

                data_s11_1 = data_float[0, :]
                data_s11_2 = data_float[1, :]

                data_s12_1 = data_float[2, :]
                data_s12_2 = data_float[3, :]

                data_s21_1 = data_float[4, :]
                data_s21_2 = data_float[5, :]

                data_s22_1 = data_float[6, :]
                data_s22_2 = data_float[7, :]

        # re-enable continuous sweep
        self.vna.write_str('INIT1:CONT ON')

        # Display sweep (visible only after the end of remote control
        self.vna.write_str('DISPLAY:WINDOW1:STATE ON')
        self.vna.write_str('DISP:WIND1:TRAC1:FEED "Trc1"')
        self.vna.write_str('DISP:WIND1:TRAC2:FEED "Trc2"')
        self.vna.write_str('DISP:WIND1:TRAC3:FEED "Trc3"')
        self.vna.write_str('DISP:WIND1:TRAC4:FEED "Trc4"')
        self.vna.write_str('DISP:WIND1:TRAC5:FEED "Trc5"')
        self.vna.write_str('DISP:WIND1:TRAC6:FEED "Trc6"')
        self.vna.write_str('DISP:WIND1:TRAC7:FEED "Trc7"')
        self.vna.write_str('DISP:WIND1:TRAC8:FEED "Trc8"')

        if return_format.upper() == 'RI':
            return (
                data_s11_1 + 1j * data_s11_2,
                data_s12_1 + 1j * data_s12_2,
                data_s21_1 + 1j * data_s21_2,
                data_s22_1 + 1j * data_s22_2
            )

        elif return_format.upper() == 'DB':
            return {
                's11': {'mag': data_s11_1, 'phase': data_s11_2},
                's12': {'mag': data_s12_1, 'phase': data_s12_2},
                's21': {'mag': data_s21_1, 'phase': data_s21_2},
                's22': {'mag': data_s22_1, 'phase': data_s22_2},
            }
        else:
            return None

    def single_sweep(self, s_param: str, return_format: str = 'RI') -> np.ndarray | tuple:
        """
        Performs a single frequency sweep measurement for a specified S-parameter.

        Args:
            s_param (str): The S-parameter to measure (e.g., 'S11', 'S12', 'S21', 'S22').
            return_format (str, optional): The format of the returned data ('RI' or 'DB'). Default is 'RI'.

        Returns:
            np.ndarray | dict: The measured data in the specified format.

        Raises:
            RuntimeError: If an invalid `return_format` is provided.
        """
        if return_format.upper() == 'RI':
            _cmp_ctrl = 0
            _trace1_format = 'REAL'
            _trace2_format = 'IMAG'
        elif return_format.upper() == 'DB':
            _cmp_ctrl = -999
            _trace1_format = 'MLOG'
            _trace2_format = 'PHAS'
        else:
            raise RuntimeError('Invalid format: %s' % return_format)

        # erase previous data
        self.vna.write_str('CALCulate:PARameter:DELete:ALL')

        # enable SINGLE SWEEP
        self.vna.write_str('INIT1:CONT OFF')

        # create trace for the S-Parameter
        self.vna.write_str(f'CALC1:PAR:SDEF "Trc1","{s_param}"')
        self.vna.write_str(f'CALC1:PAR:MEAS "Trc1","{s_param}"')
        self.vna.write_str('CALC1:PAR:SEL "Trc1"')
        self.vna.write_str(f'CALC1:FORM {_trace1_format}')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc2","{s_param}"')
        self.vna.write_str(f'CALC1:PAR:MEAS "Trc2","{s_param}"')
        self.vna.write_str('CALC1:PAR:SEL "Trc2"')
        self.vna.write_str(f'CALC1:FORM {_trace2_format}')

        # Launch the sweep
        self.vna.write_str('INIT1')

        # Display sweep (visible only after the end of remote control
        self.vna.write_str('DISPLAY:WINDOW1:STATE ON')
        self.vna.write_str('DISP:WIND1:TRAC1:FEED "Trc1"')
        self.vna.write_str('DISP:WIND1:TRAC2:FEED "Trc2"')

        _cmp_ctrl = (0 if return_format.upper() == 'RI' else -999)
        data_1 = np.ones((self.frequency_sweep[2],)) * _cmp_ctrl
        data_2 = np.zeros((self.frequency_sweep[2],))
        while np.min(data_1) == _cmp_ctrl:
            data_str = self.vna.query_str('CALC:DATA:DALL? FDATA')
            if data_str == 'Simulating':
                data_1, data_2 = self._load_s2p_data(s_param, return_format)
            elif data_str:
                data_float = [float(d) for d in data_str.split(',')]
                data_1 = data_float[0:self.frequency_sweep[2]]
                data_2 = data_float[self.frequency_sweep[2]:]

        # re-enable continuous sweep
        self.vna.write_str('INIT1:CONT ON')

        if return_format.upper() == 'RI':
            return np.array(data_1) + 1j * np.array(data_2)
        elif return_format.upper() == 'DB':
            return {'mag': data_1, 'phase': data_2}
        else:
            return None

    def measure(self, num_iterations: int = 1, return_format: str = 's2p', file_path: str = None, progress_bar=None) \
            -> np.ndarray | rf.Network:
        """
        Performs multiple VNA sweeps and returns the measured S-parameters.

        Args:
            num_iterations (int, optional): The number of frequency sweep iterations. Default is 1.
            return_format (str, optional): The output format ('s2p' or 'matrix'). Default is 's2p'.
            file_path (str, optional): Path to save the measured data as an S2P file.
            progress_bar (Any, optional): Progress Bar object. Must have those methods: setMaximum() and setValue().

        Returns:
            rf.Network | np.ndarray: The measured S-parameters in the specified format.

        Raises:
            ValueError: If an invalid `return_format` is specified.
        """
        results = np.zeros((self.frequency_sweep[2], 2, 2), dtype=complex)

        if progress_bar is not None:
            progress_bar.setMaximum(num_iterations)

        for i in range(num_iterations):
            results[:, 0, 0], results[:, 0, 1], results[:, 1, 0], results[:, 1, 1] = \
                self.sweep(return_format='RI')
            if progress_bar is not None:
                progress_bar.setValue(i)

        results /= float(num_iterations)

        s2p = rf.Network(s=results, f=self.frequencies_GHz * 1e9, f_unit='Hz')
        if file_path is not None:
            s2p.write_touchstone(file_path)
            print(f"S2P file created successfully: {file_path}")

        if return_format.lower() == 's2p':
            return s2p
        elif return_format.lower() == 'matrix':
            return results
        else:
            raise ValueError('Invalid return format: %s (valid: s2p, matrix)' % return_format)

    def reset(self):
        # create trace for the S-Parameters
        self.vna.write_str('CALCulate:PARameter:DELete:ALL')
        self.vna.write_str(f'CALC1:PAR:SDEF "Trc1","S11"')
        self.vna.write_str(f'CALC1:FORM MLOG')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc2","S22"')
        self.vna.write_str(f'CALC1:FORM MLOG')

        self.vna.write_str('DISPLAY:WINDOW1:STATE ON')
        self.vna.write_str('DISP:WIND1:TRAC1:FEED "Trc1"')
        self.vna.write_str('DISP:WIND1:TRAC2:FEED "Trc2"')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc3","S11"')
        self.vna.write_str(f'CALC1:FORM PHAS')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc4","S22"')
        self.vna.write_str(f'CALC1:FORM PHAS')

        self.vna.write_str('DISPLAY:WINDOW2:STATE ON')
        self.vna.write_str('DISP:WIND2:TRAC1:FEED "Trc3"')
        self.vna.write_str('DISP:WIND2:TRAC2:FEED "Trc4"')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc5","S12"')
        self.vna.write_str(f'CALC1:FORM MLOG')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc6","S21"')
        self.vna.write_str(f'CALC1:FORM MLOG')

        self.vna.write_str('DISPLAY:WINDOW3:STATE ON')
        self.vna.write_str('DISP:WIND3:TRAC1:FEED "Trc5"')
        self.vna.write_str('DISP:WIND3:TRAC2:FEED "Trc6"')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc7","S12"')
        self.vna.write_str(f'CALC1:FORM PHAS')

        self.vna.write_str(f'CALC1:PAR:SDEF "Trc8","S21"')
        self.vna.write_str(f'CALC1:FORM PHAS')

        self.vna.write_str('DISPLAY:WINDOW4:STATE ON')
        self.vna.write_str('DISP:WIND4:TRAC1:FEED "Trc7"')
        self.vna.write_str('DISP:WIND4:TRAC2:FEED "Trc8"')

    def enable_trl_calibration(self, cal_kit: str):
        try:
            self.reset()
            # Select GOLA connector and the requested calibration kit
            self.vna.write_str(":SENSe1:CORRection:COLLect:METHod TRL")
            self.vna.write_str(f"SENSe1:CORRection:CKIT:SELect 'GOLA', '{cal_kit}'")

            return True
        except Exception as e:
            print(f"❌ Error during TRL cal: {e}")
            return False

    def save_trl_calibration(self):
        try:
            self.vna.write_str(":SENSe1:CORRection:COLLect:SAVE:SELected")

            # Turn on calibration
            self.turn_on_calibration()
            return True, None
        except Exception as e:
            print(f"❌ Error during saving TRL cal: {e}")
            return False, e

    def perform_thru_measurement(self):
        try:
            # Select GOLA connector and the requested calibration kit
            self.vna.write_str(":SENSe1:CORRection:COLLect:ACQuire:SELected THRough, 1, 2")
            return True, None
        except Exception as e:
            print(f"❌ Error during TRL THRU: {e}")
            return False, e

    def perform_line_measurement(self):
        try:
            # Select GOLA connector and the requested calibration kit
            self.vna.write_str(":SENSe1:CORRection:COLLect:ACQuire:SELected LINE, 1, 2")
            return True, None
        except Exception as e:
            print(f"❌ Error during TRL LINE: {e}")
            return False, e

    def perform_reflect_measurement(self):
        try:
            # Select GOLA connector and the requested calibration kit
            self.vna.write_str(":SENSe1:CORRection:COLLect:ACQuire:SELected REFL, 1")
            self.vna.write_str(":SENSe1:CORRection:COLLect:ACQuire:SELected REFL, 2")
            return True, None
        except Exception as e:
            print(f"❌ Error during TRL REFLECT: {e}")
            return False, e

    def turn_off_calibration(self) :
        """
        Turns off the current calibration.
        """
        self.vna.write_str(':SENSe1:CORRection:STAT OFF')
        self.calibration_active = False

    def turn_on_calibration(self) -> bool:
        """
        Turns on calibration (if one is loaded).
        """
        self.vna.write_str(':SENSe1:CORRection:STAT ON')
        cal_state = self.vna.query_str(':SENSe1:CORRection:STAT?')
        self.calibration_active = (cal_state.strip() == '1')

        return self.calibration_active
