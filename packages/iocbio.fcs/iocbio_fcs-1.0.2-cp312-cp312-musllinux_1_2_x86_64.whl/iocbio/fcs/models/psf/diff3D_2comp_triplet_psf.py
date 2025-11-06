#!/usr/bin/env python3

import numpy as np

from iocbio.fcs.lib.base_model import AbstractModel
from .. import analytical_acf as aa
from .engines.prodtools import proddot
from .psf import PSF


# Model: 3D-diffusion - 2 components - triplet - PSF
class Diff3D_2comp_triplet_psf(AbstractModel):
    def __init__(self, args):
        super().__init__(args)
        self.component_num = 2
        self.psf = PSF(args.psf_file, args.downscale_xy, args.downscale_z)

        # Isotropic model
        if args.isotropic:
            self.parameters = [
                "concentration1_nanomolar",
                "diffusion1",
                "concentration2_nanomolar",
                "diffusion2 - diffusion1",
                "triplet_amplitude",
                "triplet_tau",
            ]
            self.set_parameters = self.set_parameters_isotropic

        # Anisotropic model
        else:
            self.parameters = [
                "concentration1_nanomolar",
                "diffusion1_x",
                "diffusion1_y",
                "concentration2_nanomolar",
                "diffusion2_x - diffusion1_x",
                "diffusion2_y - diffusion1_y",
                "triplet_amplitude",
                "triplet_tau",
            ]
            self.set_parameters = self.set_parameters_anisotropic

        # psf_scale (α): Extra parameter for adjusting PSF (0 < α < 2). Default value is 1.
        if args.psf_scale:
            self.parameters.append("psf_scale")

    def set_parameters_isotropic(
        self,
        concentration1,
        diffusion1,
        concentration2,
        diffusion2,
        triplet_amplitude,
        triplet_tau,
        psf_scale=1,
    ):
        self.set_parameters_anisotropic(
            concentration1,
            diffusion1,
            diffusion1,
            concentration2,
            diffusion2,
            diffusion2,
            triplet_amplitude,
            triplet_tau,
            psf_scale,
        )

    def set_parameters_anisotropic(
        self,
        concentration1,
        diffusion1_x,
        diffusion1_y,
        concentration2,
        diffusion2_x,
        diffusion2_y,
        triplet_amplitude,
        triplet_tau,
        psf_scale=1,
    ):
        self.concentration1_nanomolar = concentration1
        self.diffusion1_x = diffusion1_x
        self.diffusion1_y = diffusion1_y
        self.diffusion1_z = diffusion1_y
        self.concentration2_nanomolar = concentration2
        self.diffusion2_x = diffusion2_x + diffusion1_x
        self.diffusion2_y = diffusion2_y + diffusion1_y
        self.diffusion2_z = diffusion2_y + diffusion1_y
        self.triplet_amplitude = triplet_amplitude
        self.triplet_tau = triplet_tau
        self.psf_scale = psf_scale
        self.psf.psf_scale = psf_scale

    def integrate_propagator(self, x, y, z, t):
        # First component
        x1_integ, d1_x = aa.integration(x, self.psf.deltax_unique, self.diffusion1_x, self.psf.voxel_x, t)
        y1_integ, d1_y = aa.integration(y, self.psf.deltay_unique, self.diffusion1_y, self.psf.voxel_y, t)
        z1_integ, d1_z = aa.integration(z, self.psf.deltaz_unique, self.diffusion1_z, self.psf.voxel_z, t)

        # Second component
        x2_integ, d2_x = aa.integration(x, self.psf.deltax_unique, self.diffusion2_x, self.psf.voxel_x, t)
        y2_integ, d2_y = aa.integration(y, self.psf.deltay_unique, self.diffusion2_y, self.psf.voxel_y, t)
        z2_integ, d2_z = aa.integration(z, self.psf.deltaz_unique, self.diffusion2_z, self.psf.voxel_z, t)

        triplet_part = aa.triplet(self.triplet_amplitude, t, self.triplet_tau)

        conc1_micrometer = self.concentration1_nanomolar * self.convert_c
        conc2_micrometer = self.concentration2_nanomolar * self.convert_c

        p1 = 1 / (conc1_micrometer + conc2_micrometer) ** 2

        # Multiply main matrixes
        prod1 = proddot(
            self.psf.psf_mult,
            x1_integ,
            y1_integ,
            z1_integ,
            self.psf.deltax_index,
            self.psf.deltay_index,
            self.psf.deltaz_index,
        )
        prod2 = proddot(
            self.psf.psf_mult,
            x2_integ,
            y2_integ,
            z2_integ,
            self.psf.deltax_index,
            self.psf.deltay_index,
            self.psf.deltaz_index,
        )

        # Integral scaled by psf_scale^6 to reflect PSF integral scaling
        # to one and its impact in PSF*PSF integral
        integ1 = -(0.5**3) * d1_x * d1_y * d1_z * prod1 / (self.psf_scale**6)
        integ2 = -(0.5**3) * d2_x * d2_y * d2_z * prod2 / (self.psf_scale**6)

        integ = p1 * ((conc1_micrometer * integ1) + (conc2_micrometer * integ2)) * triplet_part
        return integ

    def calc_acf(self, delta_x, delta_y, delta_z, delta_t):
        acf_arr = np.array([])
        for i in range(delta_x.size):
            l_x = delta_x[i]
            l_y = delta_y[i]
            l_z = delta_z[i]
            l_t = delta_t[i]
            acf = self.integrate_propagator(l_x, l_y, l_z, l_t)
            acf_arr = np.append(acf_arr, acf)
        return acf_arr
