import argparse
import h5py
import matplotlib.pyplot as plt
import numpy as np

from iocbio.fcs.lib.const import PIXEL_TIME


def calc_psf_value(x, y, z):
    w_x, w_y, w_z = 0.29, 0.29, 1.1
    x_0, y_0, z_0 = 0, 0, 0
    amplitude = 1
    W_x = np.exp(-2 * ((x - x_0) ** 2) / (w_x**2))
    W_y = np.exp(-2 * ((y - y_0) ** 2) / (w_y**2))
    W_z = np.exp(-2 * ((z - z_0) ** 2) / (w_z**2))
    W_r = amplitude * W_x * W_y * W_z
    return W_r


def app(args):
    # PSF shape
    shape_n = [args.z, args.xy, args.xy]
    x_shape = shape_n[2]
    y_shape = shape_n[1]
    z_shape = shape_n[0]

    # PSF size
    x_size = args.xy_size  # micro meter
    y_size = args.xy_size  # micro meter
    z_size = args.z_size

    # Meshgrid
    x_axis = np.linspace(-x_size / 2, x_size / 2, x_shape)
    y_axis = np.linspace(y_size / 2, -y_size / 2, y_shape)
    z_axis = np.linspace(z_size / 2, -z_size / 2, z_shape)

    matrix_y, matrix_z, matrix_x = np.meshgrid(y_axis, z_axis, x_axis)

    PSF = calc_psf_value(matrix_x, matrix_y, matrix_z)
    print("PSF shape:\n", PSF.shape)

    x, y, z = matrix_x, matrix_y, matrix_z

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(x, y, z)
    pnt3d = ax.scatter(x, y, z, s=PSF / 0.005, c="r", alpha=PSF / np.max(PSF))
    cbar = plt.colorbar(pnt3d)
    cbar.set_label("Values (units)")
    plt.show()

    psf = h5py.File("%s.h5" % args.psf_name, "w")
    dataset = psf.create_dataset("psf", data=PSF)
    dataset.attrs["element_size_um"] = np.array([z_size / z_shape, y_size / y_shape, x_size / x_shape])
    dataset.attrs["voxel size x [meter]"] = (x_size / x_shape) * PIXEL_TIME
    dataset.attrs["voxel size y [meter]"] = (y_size / y_shape) * PIXEL_TIME
    dataset.attrs["voxel size z [meter]"] = (z_size / z_shape) * PIXEL_TIME


def main():
    parser = argparse.ArgumentParser(
        description="Create a 3D-Gaussian PSF as a HDF5 file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--psf-name", default="psf", help="Name of HDF file")
    parser.add_argument(
        "--xy",
        type=int,
        default=29,
        help="Specifies the number of voxels along X and Y axes in the 3D-PSF shape (Z, X, Y)",
    )
    parser.add_argument(
        "--xy-size",
        type=float,
        default=1.46,
        help="PSF size along X-Y-axes [micrometer]",
    )
    parser.add_argument(
        "--z",
        type=int,
        default=43,
        help="Specifies the number of voxels along Z-axis in the 3D-PSF shape (Z, X, Y)",
    )
    parser.add_argument(
        "--z-size",
        type=float,
        default=4.30,
        help="PSF size along Z-axis [micrometer]",
    )
    args = parser.parse_args()
    app(args)


if __name__ == "__main__":
    main()
