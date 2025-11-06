import numpy as np
from scipy.special import erf

from iocbio.fcs.lib.const import PIXEL_TIME


# Analytical model (formulas for calculating diffusion and triplet)
def diffusion(distance, time, diffusion_coefficient, width):
    dtw = 4 * diffusion_coefficient * time + width**2
    denominator = np.sqrt(np.pi * dtw)
    numerator = np.exp(-(distance**2) / dtw)
    return numerator / denominator


def triplet(trip, time, tau):
    result = 1 + (trip / (1 - trip)) * np.exp(-time / tau * (1 / PIXEL_TIME))
    return result


# PSF model: integration formulas
def combine(v, erf):
    return (v * erf(v)) + (np.exp(-(v**2)) / np.sqrt(np.pi))


def psf_integral(radius, scaling_factor, voxel_size):
    scaled_radius = radius / scaling_factor
    m = combine(scaled_radius, erf)
    scaled_radius_minus_voxel = (radius - voxel_size) / scaling_factor
    m_prime = combine(scaled_radius_minus_voxel, erf)
    scaled_radius_plus_voxel = (radius + voxel_size) / scaling_factor
    n = combine(scaled_radius_plus_voxel, erf)
    return (2 * m) - m_prime - n


def integration(loc, dl_unique, diffusion, voxel, time):
    L = loc + dl_unique * voxel
    denominator = np.sqrt(4 * diffusion * time)
    integ = psf_integral(L, denominator, voxel)
    return integ, denominator
