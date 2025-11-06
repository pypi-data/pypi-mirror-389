# IOCBIO FCS: A Unified Platform for FCS and RICS Analysis with Advanced Statistical Inference

**IOCBIO FCS** is an open-source Python-based platform for analyzing fluorescence intensity traces and images obtained from Fluorescence Correlation Spectroscopy (FCS) and Raster Image Correlation Spectroscopy (RICS) experiments.

This software provides a complete workflow from data visualization and autocorrelation calculation to model fitting and parameter estimation.


The software package includes Python libraries and command-line interface tools that enable users to:

- Visualize individual fluorescence trace/image and averaged traces/images across multiple measurements.  
- Calculate the autocorrelation function (ACF) for both FCS traces and RICS images using GPU/CPU acceleration.  
- Fit ACF data with flexible diffusion models to estimate diffusion coefficients and other parameters, using both nonlinear least-squares (NLS) and Bayesian approaches.  
- Plot results including fitted ACF data, pre-analysis scatter plots, posterior diagnostics, angular dependence plots in RICS, and spatially resolved parameter maps from sector analysis.


## Links

- [Project page](https://gitlab.com/iocbio/fcs)
- [Releases](https://gitlab.com/iocbio/fcs/-/releases)
- [Feature requests and bugs](https://gitlab.com/iocbio/fcs/issues)



## Copyright

Copyright (C) 2024-2025 Laboratory of Systems Biology, Department of Cybernetics, School of Science, Tallinn University of Technology.

Contact: Marko Vendelin (markov@sysbio.ioc.ee)

Software license: GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. 
See [LICENSE](https://gitlab.com/iocbio/fcs/-/blob/main/LICENSE.md) for details.

Authors: Software authors are listed in [AUTHORS](https://gitlab.com/iocbio/fcs/-/blob/main/AUTHORS.md)
