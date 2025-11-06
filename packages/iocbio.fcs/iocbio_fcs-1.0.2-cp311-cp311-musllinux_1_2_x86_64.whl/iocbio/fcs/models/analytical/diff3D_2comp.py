#!/usr/bin/env python3
from iocbio.fcs.lib.base_model import AbstractModel
from .. import analytical_acf as aa


# Model: 3D-diffusion - 2 components
class Diff3D_2comp(AbstractModel):
    def __init__(self, args):
        super().__init__(args)
        self.component_num = 2

        # Isotropic model
        if args.isotropic:
            self.parameters = [
                "concentration1_nanomolar",
                "diffusion1",
                "concentration2_nanomolar",
                "diffusion2 - diffusion1",
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
            ]
            self.set_parameters = self.set_parameters_anisotropic

        # psf_scale (α): Extra parameter for adjusting PSF (0 < α < 2). Default value is 1.
        if args.psf_scale:
            self.parameters.append("psf_scale")

    def set_parameters_isotropic(self, concentration1, diffusion1, concentration2, diffusion2, psf_scale=1):
        self.set_parameters_anisotropic(
            concentration1, diffusion1, diffusion1, concentration2, diffusion2, diffusion2, psf_scale
        )

    def set_parameters_anisotropic(
        self,
        concentration1,
        diffusion1_x,
        diffusion1_y,
        concentration2,
        diffusion2_x,
        diffusion2_y,
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
        self.psf_scale = psf_scale

    def calc_acf(self, delta_x, delta_y, delta_z, delta_t):
        w_x = self.psf_scale * self.wx
        w_y = self.psf_scale * self.wy
        w_z = self.psf_scale * self.wz

        conc1_micrometer = self.concentration1_nanomolar * self.convert_c
        conc2_micrometer = self.concentration2_nanomolar * self.convert_c
        c = (conc1_micrometer + conc2_micrometer) ** 2

        x1 = aa.diffusion(delta_x, delta_t, self.diffusion1_x, w_x)
        y1 = aa.diffusion(delta_y, delta_t, self.diffusion1_y, w_y)
        z1 = aa.diffusion(delta_z, delta_t, self.diffusion1_z, w_z)

        x2 = aa.diffusion(delta_x, delta_t, self.diffusion2_x, w_x)
        y2 = aa.diffusion(delta_y, delta_t, self.diffusion2_y, w_y)
        z2 = aa.diffusion(delta_z, delta_t, self.diffusion2_z, w_z)

        comp1 = conc1_micrometer * x1 * y1 * z1
        comp2 = conc2_micrometer * x2 * y2 * z2

        func = (comp1 + comp2) / c
        return func
