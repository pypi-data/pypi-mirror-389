#!/usr/bin/env python3

import numpy as np

from iocbio.fcs.lib.base_model import AbstractModel
from .. import analytical_acf as aa
from .engines.prodtools import proddot
from .psf import PSF


# Model: 3D-diffusion - PSF model
class Diff3D_psf(AbstractModel):
    def __init__(self, args):
        super().__init__(args)
        self.component_num = 1
        self.psf = PSF(args.psf_file, args.downscale_xy, args.downscale_z)

        # Isotropic model
        if args.isotropic:
            self.parameters = ["concentration_nanomolar", "diffusion"]
            self.set_parameters = self.set_parameters_isotropic

        # Anisotropic model
        else:
            self.parameters = [
                "concentration_nanomolar",
                "diffusion_x",
                "diffusion_y",
            ]
            self.set_parameters = self.set_parameters_anisotropic

        # psf_scale (α): Extra parameter for adjusting PSF (0 < α < 2). Default value is 1.
        if args.psf_scale:
            self.parameters.append("psf_scale")

    def set_parameters_isotropic(self, concentration, diffusion, psf_scale=1):
        self.set_parameters_anisotropic(concentration, diffusion, diffusion, psf_scale)
        self.diffusion = diffusion

    def set_parameters_anisotropic(self, concentration, diffusion_x, diffusion_y, psf_scale=1):
        self.concentration_nanomolar = concentration
        self.diffusion_x = diffusion_x
        self.diffusion_y = diffusion_y
        self.diffusion_z = diffusion_y
        self.psf_scale = psf_scale
        self.psf.psf_scale = psf_scale

    def integrate_propagator(self, x, y, z, t):
        x_integ, d_x = aa.integration(x, self.psf.deltax_unique, self.diffusion_x, self.psf.voxel_x, t)
        y_integ, d_y = aa.integration(y, self.psf.deltay_unique, self.diffusion_y, self.psf.voxel_y, t)
        z_integ, d_z = aa.integration(z, self.psf.deltaz_unique, self.diffusion_z, self.psf.voxel_z, t)

        # Multiply main matrixes
        prod = proddot(
            self.psf.psf_mult,
            x_integ,
            y_integ,
            z_integ,
            self.psf.deltax_index,
            self.psf.deltay_index,
            self.psf.deltaz_index,
        )

        # Integral scaled by psf_scale^6 to reflect PSF integral scaling
        # to one and its impact in PSF*PSF integral
        integ = (-(0.5**3)) * d_x * d_y * d_z * prod / (self.psf_scale**6)
        return integ

    def calc_acf(self, delta_x, delta_y, delta_z, delta_t):
        acf_arr = np.array([])
        concentration_micrometer3 = self.concentration_nanomolar * self.convert_c
        for i in range(delta_x.size):
            l_x = delta_x[i]
            l_y = delta_y[i]
            l_z = delta_z[i]
            l_t = delta_t[i]
            acf = self.integrate_propagator(l_x, l_y, l_z, l_t) / concentration_micrometer3
            acf_arr = np.append(acf_arr, acf)
        return acf_arr
