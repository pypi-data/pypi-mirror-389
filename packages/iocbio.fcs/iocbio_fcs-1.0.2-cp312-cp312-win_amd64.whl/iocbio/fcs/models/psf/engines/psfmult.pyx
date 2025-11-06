from libcpp.vector cimport vector
import numpy as np
cimport numpy as np

ctypedef np.float64_t DTYPE_t
ctypedef np.int64_t ITYPE_t

cdef extern from "psfmult_impl.cpp":
    cdef void psfmult_impl(const vector[double] &psf,
                           const vector[int] &x,
                           const vector[int] &y,
                           const vector[int] &z,
                           vector[double] &psfpsf,
                           vector[int] &dx,
                           vector[int] &dy,
                           vector[int] &dz)

def psfmult(np.ndarray[DTYPE_t, ndim=1, mode="c"] psf,
            np.ndarray[ITYPE_t, ndim=1, mode="c"] x,
            np.ndarray[ITYPE_t, ndim=1, mode="c"] y,
            np.ndarray[ITYPE_t, ndim=1, mode="c"] z):
    cdef vector[double] psfpsf
    cdef vector[int] dx
    cdef vector[int] dy
    cdef vector[int] dz
    psfmult_impl(psf, x, y, z, psfpsf, dx, dy, dz)
    return np.array(psfpsf), np.array(dx), np.array(dy), np.array(dz)
