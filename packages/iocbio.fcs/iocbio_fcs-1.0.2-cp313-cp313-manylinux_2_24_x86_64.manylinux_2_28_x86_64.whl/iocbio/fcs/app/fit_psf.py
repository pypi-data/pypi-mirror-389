import argparse
import h5py
import numpy as np
from scipy.optimize import least_squares


def calc_psf_value(x, y, z, w_x, w_y, w_z, x0, y0, z0, amplitude):
    W_x = np.exp(-2 * ((x - x0) ** 2) / (w_x**2))
    W_y = np.exp(-2 * ((y - y0) ** 2) / (w_y**2))
    W_z = np.exp(-2 * ((z - z0) ** 2) / (w_z**2))
    W_r = amplitude * W_x * W_y * W_z
    return W_r


def error_func(parameters, delta_x, delta_y, delta_z, psf_value):
    y = calc_psf_value(delta_x, delta_y, delta_z, *parameters)
    residual = psf_value - y
    return residual


def fit_psf(args):
    psf = h5py.File(args.psf_name, "r")
    dataset = "psf" if "psf" in psf else "image"
    psf_data = psf[dataset]
    psf_value = np.array(psf_data)
    element_size = psf_data.attrs["element_size_um"]
    voxel_z, voxel_x, voxel_y = element_size
    volume = voxel_x * voxel_y * voxel_z

    # Normalization
    psf_value /= psf_value.sum() * volume

    # PSF shape
    shape = psf_value.shape
    x_shape = shape[2]
    y_shape = shape[1]
    z_shape = shape[0]

    # PSF size
    x_size = x_shape * voxel_x  # micro meter
    y_size = y_shape * voxel_y  # micro meter
    z_size = z_shape * voxel_z  # micro meter

    x_axis = np.linspace(-x_size / 2, x_size / 2, x_shape)
    y_axis = np.linspace(y_size / 2, -y_size / 2, y_shape)
    z_axis = np.linspace(z_size / 2, -z_size / 2, z_shape)

    matrix_y, matrix_z, matrix_x = np.meshgrid(y_axis, z_axis, x_axis)

    # Flatten
    psf_values_flat = psf_value.flatten()
    matrix_y_flat = matrix_y.flatten()
    matrix_z_flat = matrix_z.flatten()
    matrix_x_flat = matrix_x.flatten()

    # Fitting
    parameters = ["w_x", "w_y", "w_z", "x_0", "y_0", "z_0", "amplitude"]
    p0 = [
        0.29,
        0.29,
        0.29 * 4,
        matrix_x_flat[matrix_x_flat.size // 2],
        matrix_y_flat[matrix_y_flat.size // 2],
        matrix_z_flat[matrix_z_flat.size // 2],
        1,
    ]

    residual = least_squares(
        error_func,
        p0,
        args=(matrix_x_flat, matrix_y_flat, matrix_z_flat, psf_values_flat),
    )

    error = error_func(residual.x, matrix_x_flat, matrix_y_flat, matrix_z_flat, psf_values_flat)
    error
    for i, k in enumerate(parameters):
        print("%s:" % k, residual.x[i])

    print("==============================================================")
    print(f"PSF shape: x-> {shape[1]}  y-> {shape[2]}  z-> {shape[0]}")
    print(f"PSF size:  {x_size:.2f} * {y_size:.2f} * {z_size:.2f} = {x_size * y_size * z_size:.2f}")
    print("voxel_x:  ", voxel_x)
    print("voxel_y:  ", voxel_y)
    print("voxel_z:  ", voxel_z)


def main():
    parser = argparse.ArgumentParser(
        description="Fit PSF file (HDF5) using least squares method",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("psf_name", help="PSF file name")
    args = parser.parse_args()
    fit_psf(args)


if __name__ == "__main__":
    main()
