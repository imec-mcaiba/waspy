import logging
from typing import List

import numpy as np
from scipy.interpolate import interp1d, UnivariateSpline
from scipy import optimize
from scipy.optimize import Bounds, fmin, fminbound

from waspy.iba.rbs_entities import FitAlgorithmType


def get_angle_for_minimum_yield(smooth_angles, smooth_yields) -> float:
    smooth_angle_for_minimum_yield = round(smooth_angles[np.argmin(smooth_yields)], 2)
    log_line = "[WASPY.IBA.RBS_YIELD_ANGLE_FIT] Minimum yield found at: [angle: yield] = [{angle}: {energy_yield}]" \
        .format(angle=smooth_angle_for_minimum_yield, energy_yield=round(np.amin(smooth_yields), 2))
    logging.info(log_line)
    return smooth_angle_for_minimum_yield


def fit_and_smooth(angles, yields, algorithm_type=FitAlgorithmType.LOWER_FIT):
    """Will fit a curve using x and y. When the fit is found, recalculate the y values with a more finely
    distributed x (smooth) (interpolated)."""

    # Tried to use scipy minimize, fminbound here - but it does not work as expected in all cases
    # Just eval the entire range and get the minimum - will get very slow with large arrays
    if algorithm_type == FitAlgorithmType.MINIMUM_YIELD:
        return None, get_angle_for_minimum_yield(angles, yields)
    elif algorithm_type == FitAlgorithmType.LOWER_FIT:
        return attempt_lower_fit(angles, yields)
    else:
        return attempt_fit(angles, yields)


def attempt_fit(angles, yields):
    p_start = np.amax(yields)
    r_start = angles[np.argmin(yields)]

    arg_bounds = (
        (-np.inf, 0, -np.inf, -np.inf, 0, -np.inf), (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
    [p, q, r, s, t, u], covariance = optimize.least_squares(fit, angles, yields,
                                                        p0=[p_start, 100.0, r_start, 0.3, 50, -1.0],
                                                        bounds=arg_bounds, ftol=0.01)

    def fit_func(x):
        return fit(x, p, q, r, s, t, u)
    smooth_x = [x for x in np.arange(angles[0], angles[-1], 0.01)]
    smooth_y = [fit(x, p, q, r, s, t, u) for x in smooth_x]
    min_x = round(smooth_x[np.argmin(smooth_y)], 2)
    return fit_func, min_x


def fit(x, p, q, r, s, t, u):
    value = p + t * np.exp(-np.power(x - r, 2) / (2 * np.power(4 * s, 2))) - q * np.exp(
        -np.power(x - r, 2) / (2 * np.power(s, 2))) + u * x
    return value


def attempt_lower_fit(angles, yields):
    constant_term_start = np.amax(yields)
    gauss_mean_start = angles[np.argmin(yields)]
    gauss_amplitude_start = abs(np.max(yields) - np.min(yields))

    half_yields_max = (np.max(yields) + np.min(yields)) / 2
    shifted_yields = yields - half_yields_max
    interpolated_yields = UnivariateSpline(angles, shifted_yields)
    intersections = interpolated_yields.roots()

    previous_smaller = False
    sigma_start = 0.3
    for (index, intersection) in enumerate(intersections):
        current_larger = intersection > gauss_mean_start
        if current_larger and previous_smaller:
            # convert full width half maximum to sigma (wikipedia)
            sigma_start = (intersections[index] - intersections[index-1]) / (2 * np.sqrt(2*np.log(2)))
        previous_smaller = intersection < gauss_mean_start

    [constant_term, gauss_amplitude, gauss_mean, sigma, linear_term, quadratic_term], covariance = \
        optimize.curve_fit(lower_order_fit, angles, yields, p0=[constant_term_start, gauss_amplitude_start,
                                                                gauss_mean_start, sigma_start, -1.0, -1.0], ftol=0.01)

    def fit_func(x):
        return lower_order_fit(x, constant_term, gauss_amplitude, gauss_mean, sigma, linear_term, quadratic_term)

    smooth_x = [x for x in np.arange(angles[0], angles[-1], 0.01)]
    smooth_y = [fit(x, constant_term, gauss_amplitude, gauss_mean, sigma, linear_term, quadratic_term) for x in smooth_x]
    min_x = round(smooth_x[np.argmin(smooth_y)], 2)
    return fit_func, min_x


def lower_order_fit(x, p, q, r, s, t, u):
    return p - q * np.exp(-np.power(x - r, 2) / (2 * np.power(s, 2))) + t * np.power(x, 2) + u * x
