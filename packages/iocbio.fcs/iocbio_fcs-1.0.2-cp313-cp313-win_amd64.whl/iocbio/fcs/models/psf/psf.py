import h5py
import numpy as np
from scipy import ndimage

from .engines.psfmult import psfmult


class PSF:
    def __init__(self, psf_name, downscaleXY, downscaleZ):
        psf = h5py.File(psf_name, "r+")
        dataset_name = psf.keys()
        if "image" in dataset_name:
            dataset_name = "image"
        elif "psf" in dataset_name:
            dataset_name = "psf"
        else:
            raise Exception("\nUnknown dataset name")
        psf_data = psf[dataset_name]
        psf_value = np.array(psf_data)
        element_size = psf_data.attrs["element_size_um"]
        voxel_z, voxel_x, voxel_y = element_size
        print("Shape of original PSF:", psf_value.shape, "Elements:", psf_value.size)

        # convolution
        if downscaleXY > 1 or downscaleZ > 1:
            ones_box = np.ones((downscaleXY, downscaleXY, downscaleZ))
            convolved_psf = ndimage.convolve(psf_value, ones_box)
            psf_value = convolved_psf[
                downscaleZ // 2 : -1 : downscaleZ,
                downscaleXY // 2 : -1 : downscaleXY,
                downscaleXY // 2 : -1 : downscaleXY,
            ]
            print("Shape of PSF after downscaling:", psf_value.shape, "Elements:", psf_value.size)
        else:
            print("Using original PSF in calculations")

        # PSF size
        self._voxel_x = voxel_x * downscaleXY  # micro meter
        self._voxel_y = voxel_y * downscaleXY  # micro meter
        self._voxel_z = voxel_z * downscaleZ  # micro meter
        self._psf_scale = 1.0

        # Mesh
        x_shape = psf_value.shape[2]
        y_shape = psf_value.shape[1]
        z_shape = psf_value.shape[0]
        x_axis = range(x_shape)
        y_axis = range(y_shape)
        z_axis = range(z_shape)

        y, z, x = np.meshgrid(y_axis, z_axis, x_axis)

        # Flatten
        psf_value = psf_value.flatten()
        y = y.flatten()
        z = z.flatten()
        x = x.flatten()

        # Filtering (PSF value < 0.01 Max)
        max_value = np.max(psf_value)
        cutoff = 0.01 * max_value
        filter_index = psf_value > cutoff
        y = y[filter_index]
        z = z[filter_index]
        x = x[filter_index]
        psf_value = psf_value[filter_index]
        print("Number of PSF elements after filtering:", psf_value.size)

        # Normalization
        psf_value /= psf_value.sum() * self.voxel_volume

        # Get all unique combinations
        combination_key = f"psfpsf/{downscaleXY}-{downscaleZ}"
        if combination_key in psf:  # check HDF5 if older combinations were cached
            group = psf[combination_key]
            self.psf_mult = group["psfpsf"][:]
            deltax = group["x"][:]
            deltay = group["y"][:]
            deltaz = group["z"][:]
        else:
            self.psf_mult, deltax, deltay, deltaz = psfmult(psf_value, x, y, z)
            if psf_value.size > 5000:
                psf[combination_key + "/psfpsf"] = self.psf_mult
                psf[combination_key + "/x"] = deltax
                psf[combination_key + "/y"] = deltay
                psf[combination_key + "/z"] = deltaz

        # Split into unique delta-xyz along each axis
        self.deltax_unique, self.deltax_index = np.unique(deltax, return_inverse=True)
        self.deltay_unique, self.deltay_index = np.unique(deltay, return_inverse=True)
        self.deltaz_unique, self.deltaz_index = np.unique(deltaz, return_inverse=True)

        # Print PSF info
        print("Voxel volume: ", self.voxel_volume)
        print("voxel_x:      ", self.voxel_x)
        print("voxel_y:      ", self.voxel_y)
        print("voxel_z:      ", self.voxel_z)
        print("PSF*PSF all combinations:", psf_value.shape[0] * psf_value.shape[0])
        print("PSF*PSF unique values:", self.psf_mult.shape[0])
        print("PSF*PSF in MB:", self.psf_mult.nbytes / 1024.0 / 1024)

    @property
    def psf_scale(self):
        return self._psf_scale

    @property
    def voxel_x(self):
        return self._voxel_x * self.psf_scale

    @property
    def voxel_y(self):
        return self._voxel_y * self.psf_scale

    @property
    def voxel_z(self):
        return self._voxel_z * self.psf_scale

    @property
    def voxel_volume(self):
        return self.voxel_x * self.voxel_y * self.voxel_z

    @psf_scale.setter
    def psf_scale(self, a):
        self._psf_scale = a

    def integrate(self, func):
        X = self.deltax_unique[self.deltax_index] * self._voxel_x
        Y = self.deltay_unique[self.deltay_index] * self._voxel_y
        Z = self.deltaz_unique[self.deltaz_index] * self._voxel_z

        result = np.dot(self.psf_mult, func(X, Y, Z))
        return result
