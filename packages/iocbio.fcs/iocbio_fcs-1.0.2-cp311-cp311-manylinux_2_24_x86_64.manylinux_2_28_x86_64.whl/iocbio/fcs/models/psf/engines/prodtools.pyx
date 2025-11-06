import cython
from cython.parallel import prange


@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def proddot(const double[:] psfpsf,
            const double[:] x_integ,
            const double[:] y_integ,
            const double[:] z_integ,
            const long[:] x_index,
            const long[:] y_index,
            const long[:] z_index):
    cdef int sz = psfpsf.shape[0]
    cdef double result = 0;
    cdef int i
    for i in prange(sz, nogil=True):
        result += psfpsf[i] * \
            x_integ[x_index[i]] * \
            y_integ[y_index[i]] * \
            z_integ[z_index[i]]
    return result

        
