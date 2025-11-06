#!/usr/bin/env python3
from iocbio.fcs.lib.base_model import AbstractModel
from .. import analytical_acf as aa


# Model: 3D-diffusion - Triplet
class Diff3D_triplet(AbstractModel):
    def __init__(self, args):
        super().__init__(args)
        self.component_num = 1

        # Isotropic model
        if args.isotropic:
            self.parameters = [
                "concentration_nanomolar",
                "diffusion",
                "triplet_amplitude",
                "triplet_tau",
            ]
            self.set_parameters = self.set_parameters_isotropic

        # Anisotropic model
        else:
            self.parameters = [
                "concentration_nanomolar",
                "diffusion_x",
                "diffusion_y",
                "triplet_amplitude",
                "triplet_tau",
            ]
            self.set_parameters = self.set_parameters_anisotropic

        # psf_scale (α): Extra parameter for adjusting PSF (0 < α < 2). Default value is 1.
        if args.psf_scale:
            self.parameters.append("psf_scale")

    def set_parameters_isotropic(self, concentration, diffusion, triplet_amplitude, triplet_tau, psf_scale=1):
        self.set_parameters_anisotropic(concentration, diffusion, diffusion, triplet_amplitude, triplet_tau, psf_scale)
        self.diffusion = diffusion

    def set_parameters_anisotropic(
        self, concentration, diffusion_x, diffusion_y, triplet_amplitude, triplet_tau, psf_scale=1
    ):
        self.concentration_nanomolar = concentration
        self.diffusion_x = diffusion_x
        self.diffusion_y = diffusion_y
        self.diffusion_z = diffusion_y
        self.triplet_amplitude = triplet_amplitude
        self.triplet_tau = triplet_tau
        self.psf_scale = psf_scale

    def calc_acf(self, delta_x, delta_y, delta_z, delta_t):
        w_x = self.psf_scale * self.wx
        w_y = self.psf_scale * self.wy
        w_z = self.psf_scale * self.wz

        concentration_micrometer3 = self.concentration_nanomolar * self.convert_c

        x = aa.diffusion(delta_x, delta_t, self.diffusion_x, w_x)
        y = aa.diffusion(delta_y, delta_t, self.diffusion_y, w_y)
        z = aa.diffusion(delta_z, delta_t, self.diffusion_z, w_z)

        triplet_part = aa.triplet(self.triplet_amplitude, delta_t, self.triplet_tau)

        func = x * y * z * triplet_part / concentration_micrometer3
        return func
