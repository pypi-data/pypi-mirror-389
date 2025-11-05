# This file is part of atooms
# Copyright 2010-2025, Daniele Coslovich

"""Fourier-space post processing code."""

import math
import logging
import random
from collections import defaultdict

import numpy

from .helpers import linear_grid
from .correlation import Correlation

__all__ = ['expo_sphere', 'expo_sphere_safe', 'FourierSpaceCorrelation', 'FourierSpaceGrid']

_log = logging.getLogger(__name__)


def expo_sphere(k0, nk_max, pos):
    """Returns the exponentials of the input positions for each k."""

    # Technical note: we use ellipsis, so that we can pass either a
    # single sample or multiple samples without having to add a
    # trivial extra dimension to input array
    im = numpy.complex128('0+1j')
    # The integer grid must be the same as the one set in kgrid,
    # otherwise there is an offset the problem is that integer
    # negative indexing is impossible in python and rounding or
    # truncating kmax can slightly offset the grid

    # We pick up the smallest k0 to compute the integer grid
    # This leaves many unused vectors in the other directions, which
    # could be dropped using different nkmax for x, y, z
    # The shape of expo is nframes, N, ndim, 2*nk+1
    expo = numpy.ndarray((len(pos), ) + pos[0].shape + (2*nk_max+1, ), numpy.complex128)
    expo[..., nk_max] = numpy.complex128('1+0j')
    # First fill positive k
    for j in range(pos[0].shape[-1]):
        expo[..., j, nk_max+1] = numpy.exp(im * k0[j] * pos[..., j])
        expo[..., j, nk_max-1] = expo[..., j, nk_max+1].conjugate()
        for i in range(2, nk_max):
            expo[..., j, nk_max+i] = expo[..., j, nk_max+i-1] * expo[..., j, nk_max+1]
    # Then take complex conj for negative ones
    for i in range(2, nk_max+1):
        # TODO: why is this line necessary?
        expo[..., nk_max+i] = expo[..., nk_max+i-1] * expo[..., nk_max+1]
        expo[..., nk_max-i] = expo[..., nk_max+i].conjugate()

    return expo


def expo_sphere_safe(k0, kmax, pos):
    """
    Returns the exponentials of the input positions for each k.
    It does not use ellipsis.
    """
    im = numpy.complex128('0+1j')
    ndims = pos.shape[-1]
    nk_max = 1 + int(kmax / min(k0))
    expo = numpy.ndarray(pos.shape + (2*nk_max+1, ), numpy.complex128)
    expo[:, :, :, nk_max] = numpy.complex128('1+0j')

    for j in range(ndims):
        expo[:, :, j, nk_max+1] = numpy.exp(im*k0[j]*pos[:, :, j])
        expo[:, :, j, nk_max-1] = expo[:, :, j, nk_max+1].conjugate()
        for i in range(2, nk_max):
            expo[:, :, j, nk_max+i] = expo[:, :, j, nk_max+i-1] * expo[:, :, j, nk_max+1]

    for i in range(2, nk_max+1):
        expo[:, :, :, nk_max+i] = expo[:, :, :, nk_max+i-1] * expo[:, :, :, nk_max+1]
        expo[:, :, :, nk_max-i] = expo[:, :, :, nk_max+i].conjugate()

    return expo


def _k_norm(ik, k0, offset):
    k_shift = k0 * (numpy.array(ik) - offset)
    k_sq = numpy.dot(k_shift, k_shift)
    return math.sqrt(k_sq)

def _sphere(kmax):
    ikvec = numpy.ndarray(3, dtype=int)
    for ix in range(-kmax, kmax+1):
        for iy in range(-kmax, kmax+1):
            for iz in range(-kmax, kmax+1):
                ikvec[0] = ix
                ikvec[1] = iy
                ikvec[2] = iz
                yield ikvec

def _disk(kmax):
    ikvec = numpy.ndarray(2, dtype=int)
    for ix in range(-kmax, kmax+1):
        for iy in range(-kmax, kmax+1):
            ikvec[0] = ix
            ikvec[1] = iy
            yield ikvec


class FourierSpaceCorrelation(Correlation):

    """
    Base class for Fourier space correlation functions.

    The correlation function is computed for each of the scalar values
    k_i of the provided `kgrid`. If the latter is `None`, the grid is
    built using `ksamples` entries linearly spaced between `kmin` and
    `kmax`.

    For each sample k_i in `kgrid`, the correlation function is
    computed over at most `nk` wave-vectors (k_x, k_y, k_z) such that
    their norm (k_x^2+k_y^2+k_z^2)^{1/2} lies within `dk` of the
    prescribed value k_i.

    See the doc of `Correlation` for information about the rest of the
    instance variables.
    """

    def __init__(self, trajectory, grid, norigins=None, nk=8, dk=0.1,
                 kmin=-1, kmax=10, ksamples=20, normalize=True, **kwargs):
        super(FourierSpaceCorrelation, self).__init__(trajectory, grid,
                                                      norigins=norigins, **kwargs)
        # Some additional variables. 
        self.normalize = normalize
        
        # Find grid of k-vector norms and store it sorted as self.kgrid
        if len(self.grid_name) > 1:
            kgrid = self.grid[self.grid_name.index('k')]
        else:
            kgrid = self.grid

        # Define k-vectors
        if isinstance(kgrid, FourierSpaceGrid):
            # We keep the FourierSpaceGrid instance as a private variable
            self._kgrid = kgrid
        else:
            # The user has not provided a FourierSpaceGrid: we construct it internally
            # from the other input arguments
            self._kgrid = FourierSpaceGrid(kgrid=kgrid, nk=nk,
                                           dk=dk, kmin=kmin, kmax=kmax,
                                           ksamples=ksamples)

    def compute(self):
        self._kgrid.setup(self.trajectory[0].cell.side)
        super(FourierSpaceCorrelation, self).compute()

    # Wrap attributes of FourierSpaceGrid to keep compatibility with previous code
    @property
    def k0(self):
        """Smallest k-vector compatible with the boundary conditions"""
        return self._kgrid.k0

    @property
    def kgrid(self):
        """Actual grid of k-vector norms"""
        return self._kgrid.kgrid

    @property
    def kvectors(self):
        return self._kgrid.kvectors
    
    @kvectors.setter
    def kvectors(self, kvectors):
        raise AttributeError('cannot set kvectors, pass them to the constructor')
    
    # Private properties, used by subclasses
    @property
    def _kvectors(self):
        return self._kgrid._kvectors

    @property
    def _koffset(self):
        return self._kgrid._koffset
    
    def report(self, verbose=False):
        return self._kgrid.report(verbose=verbose)
    

class FourierSpaceGrid:

    """
    Grid of vectors in Fourier space.

    The correlation function is computed for each of the scalar values
    k_i of the provided `kgrid`. If the latter is `None`, the grid is
    built using `ksamples` entries linearly spaced between `kmin` and
    `kmax`.

    For each sample k_i in `kgrid`, the correlation function is
    computed over at most `nk` wave-vectors (k_x, k_y, k_z) such that
    their norm (k_x^2+k_y^2+k_z^2)^{1/2} lies within `dk` of the
    prescribed value k_i.

    See the doc of `Correlation` for information about the rest of the
    instance variables.
    """

    def __init__(self, kgrid=None, nk=8, dk=0.1, kmin=-1, kmax=10,
                 ksamples=20, kvectors=None):
        """
        Possible inputs:

        1. kgrid is None:

        the k grid is determined internally from kmin, kmax, ksamples
        and the kvectors are sampled using nk and dk parameters

        2. kgrid is not None, via grid or setting the variable after
        construction:

        kvectors are sampled using nk and dk and the kgrid is
        eventually redefined so that its values correspond exactly to
        the norms of the kvectors in each group

        3. kvectors is not None or set after construction: 

        kvectors must be a list of lists of kvectors in natural units

        Internal variables:

        - k0 : norm of the smallest kvector allowed by cell,
          determined internally at compute time.

        - _kvectors: list of lists of ndim arrays, grouped by
          the averaged norm, whose indices are (ix, iy, iz), which
          identify the kvectors according to the following
          formulas. We write kvectors as

          k = k0 * (jx, jy, jz)

          where jx, jy, jz are relative numbers. We tabulate
          exponentials over a grid and the indices (ix, iy, iz) of the
          tabulated array obey Fortran indexing. We symmetrize the j
          indices like this

          ix = jx + offset_j + 1, iy = jy + offset_j + 1, iz = jz + offset_j + 1

          where offset_j is the absolute value of the minimum of the
          whole set of (jx, jy, jz). This way we are sure that indices
          start from 1. This is necessary with numpy arrays, for which
          negative indices have a different meaning.

        - _koffset: value of offset_j defined above
        """
        self.kgrid = kgrid
        self.nk = nk
        self.dk = dk
        self.kmin = kmin
        self.kmax = kmax
        self.ksamples = ksamples
        self.kvectors_input = kvectors
        self.k0 = []
        
        # Some internal variables
        # compatible with the boundary conditions
        self._kvectors = []
        self._koffset = 0

    def setup(self, side):
        # Smallest kvector
        k0 = 2*math.pi / side
        if len(self.k0) > 0 and numpy.all(self.k0 == k0):
            return
        
        # Setup the grid of wave-vectors
        self.k0 = k0
        if self.kvectors_input is not None:
            self._kvectors, self._koffset = self._setup_from_kvectors(self.kvectors_input, self.k0)
        else:
            # If kgrid of kvectors are not provided, setup a linear grid from kmin,kmax,ksamples data
            # TODO: This shouldnt be allowed with fluctuating cells
            # Or we should fix the smallest k to some average of smallest k per sample
            if self.kgrid is None:
                if self.kmin > 0:
                    self.kgrid = linear_grid(self.kmin, self.kmax, self.ksamples)
                else:
                    self.kgrid = linear_grid(min(self.k0), self.kmax, self.ksamples)
            else:
                # Sort, since code below depends on kgrid[0] being the smallest k-value.
                self.kgrid.sort()
                # If the first wave-vector is negative we replace it by k0
                if self.kgrid[0] < 0.0:
                    self.kgrid[0] = min(self.k0)

            # Now find the wave-vectors
            self._kvectors, self._koffset = self._setup_grid_sphere(len(self.kgrid) * [self.dk],
                                                                    self.kgrid, self.k0)
            # Decimate them.
            # Setting the seed here once so as to get the same set
            # independent of filters.
            # TODO: use a local random instance here
            random.seed(1)
            # Pick up a random, unique set of nk vectors out ot the avilable ones
            # without exceeding maximum number of vectors in shell nkmax
            # self.kgrid, self.selection = self._decimate_k()
            for i, klist in enumerate(self._kvectors):
                self._kvectors[i] = random.sample(klist, min(self.nk, len(klist)))

        # Define the actual kgrid now
        self.kgrid = []
        for klist in self._kvectors:
            knorm = numpy.mean([_k_norm(kvec, self.k0, self._koffset) for kvec in klist])
            self.kgrid.append(knorm)

    @staticmethod
    def _setup_grid_sphere(dk, kgrid, k0):
        """
        Setup wave vector grid with spherical average (no symmetry),
        picking up vectors that fit into shells of width `dk` centered around
        the values specified in the input list `kgrid`.

        Returns a list of lists of kvectors, one entry for each element in the grid.
        """
        _log.info('setting up the wave-vector grid')
        kvec = [[] for _ in range(len(kgrid))]  # defaultdict(list)

        # With elongated box, we choose the smallest k0 component to
        # setup the integer grid. This must be consistent with
        # expo_grid() otherwise it wont find the vectors
        kmax = kgrid[-1] + dk[-1]
        kmax_sq = kmax**2
        kbin_max = 1 + int(kmax / min(k0))

        # Choose iterator of spatial grid
        ndims = len(k0)
        if ndims == 3:
            _iterator = _sphere
        elif ndims == 2:
            _iterator = _disk
        else:
            raise ValueError('unsupported dimension {}'.format(ndims))

        # Fill kvec array with kvectors matching the input kgrid within dk
        for ik in _iterator(kbin_max):
            ksq = numpy.dot(k0*ik, k0*ik)
            if ksq > kmax_sq:
                continue
            # beware: numpy.sqrt is x5 slower than math one!
            knorm = math.sqrt(ksq)
            # Look for a shell of vectors in which the vector could fit.
            # This expression is general and allows arbitrary k grids
            # However, searching for the shell like this is not fast
            # (it costs about as much as the above)
            for i in range(len((kgrid))):
                if abs(knorm - kgrid[i]) < dk[i]:
                    kvec[i].append(tuple(ik + kbin_max))
                    break

        # Check
        all_good = True
        for i in range(len(kvec)):
            if len(kvec[i]) == 0:
                dk[i] *= 1.2
                _log.info('increasing kbin {} to {}'.format(i, dk[i]))
                all_good = False
        if not all_good:
            return FourierSpaceGrid._setup_grid_sphere(dk, kgrid, k0)
        else:
            return kvec, kbin_max

    @staticmethod
    def _setup_from_kvectors(kvectors, k0):
        # Collect kvectors and compute shift
        _kvectors = []
        shift = 0
        for klist in kvectors:
            _kvectors.append([])
            for kvec in klist:
                rounded = numpy.rint(kvec / k0)
                _kvectors[-1].append(numpy.array(rounded, dtype=int))
                # Update shift
                shift = min(shift, int(min(rounded)))

        # Shift to make all array indices start from 0
        _koffset = int(abs(shift)) + 1
        for klist in _kvectors:
            for i in range(len(klist)):
                klist[i] = tuple(klist[i] + _koffset)

        return _kvectors, _koffset

    @property
    def kvectors(self):
        # Return actual kvectors
        kvectors = []
        for k, klist in enumerate(self._kvectors):
            kvectors.append([])
            for kvec in klist:
                actual_vec = self.k0 * (numpy.array(kvec) - self._koffset)
                kvectors[-1].append(list(actual_vec))
        return kvectors
            
    def report(self, verbose=False):
        """
        Return a formatted report of the wave-vector grid used to compute
        the correlation function

        The `verbose` option turns on writing of the individuals
        wavectors (also accessible via the `kvectors` property).
        """
        txt = '# k-point, average, std, vectors in shell\n'
        for i, klist in enumerate(self.kvectors):
            knorms = numpy.array([numpy.dot(kvec, kvec)**0.5 for kvec in klist])
            txt += "{} {:f} {:f} {}\n".format(self.kgrid[i], knorms.mean(),
                                              knorms.std(), len(klist))
        if verbose:
            txt += '\n# k-point, k-vector\n'
            for i, klist in enumerate(self.kvectors):
                for kvec in klist:
                    # Reformat numpy array
                    as_str = str(kvec)
                    as_str = as_str.replace(',', '')
                    as_str = as_str.replace('[', '')
                    as_str = as_str.replace(']', '')
                    txt += '{} {}\n'.format(self.kgrid[i], as_str)
        return txt
    
