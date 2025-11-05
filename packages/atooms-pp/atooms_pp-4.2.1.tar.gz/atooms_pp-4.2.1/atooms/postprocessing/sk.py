# This file is part of atooms
# Copyright 2010-2025, Daniele Coslovich

"""Structure factor."""

import logging
import numpy

from .progress import progress
from .fourierspace import FourierSpaceCorrelation, expo_sphere

__all__ = ['StructureFactor', 'StructureFactorLegacy', 'StructureFactorOptimized', 'StructureFactorFast']

_log = logging.getLogger(__name__)


def is_cell_variable(trajectory, tests=1):
    """
    Simple test to check if cell changes.

    We compare the first frame to an integer number `tests` of other
    frames starting from the end of `trajectory`.
    """
    is_variable = False
    frames = len(trajectory)
    if tests > 0:
        skip = max(1, int(frames / float(tests)))
    else:
        skip = 1
    L0 = trajectory[0].cell.side
    for sample in range(frames-1, 0, -skip):
        cell = trajectory[sample].cell
        L1 = cell.side
        if numpy.any(L0 != L1):
            is_variable = True
            break
    return is_variable


class StructureFactorLegacy(FourierSpaceCorrelation):
    """
    Structure factor.

    See the documentation of the `FourierSpaceCorrelation` base class
    for information on the instance variables.
    """

    nbodies = 2
    symbol = 'sk'
    short_name = 'S(k)'
    long_name = 'structure factor'
    variables = ['pos']

    def __init__(self, trajectory, kgrid=None, norigins=-1, nk=20,
                 dk=0.1, kmin=-1.0, kmax=15.0, ksamples=30, **kwargs):
        FourierSpaceCorrelation.__init__(self, trajectory, kgrid, norigins,
                                         nk, dk, kmin, kmax, ksamples, **kwargs)
        self._is_cell_variable = None

    def _compute(self):
        nsteps = len(self._pos_0)
        ndims = len(self.k0)
        kgrid = self.kgrid

        # Setup k vectors and tabulate rho
        cnt = [0 for k in kgrid]
        rho_0_av = [complex(0., 0.) for k in kgrid]
        rho_1_av = [complex(0., 0.) for k in kgrid]
        rho2_av = [complex(0., 0.) for k in kgrid]
        variable_cell = is_cell_variable(self.trajectory)
        for i in progress(range(0, nsteps, self.skip), total=nsteps // self.skip):
            # If cell changes we have to update the wave vectors
            if variable_cell:
                self._kgrid.setup(self.trajectory[i].cell.side)
            
            # Tabulate exponentials
            # Note: tabulating and computing takes about the same time
            if self._pos_0[i] is self._pos_1[i]:
                # Identical species
                expo_0 = expo_sphere(self.k0, self._koffset, self._pos_0[i])
                expo_1 = expo_0
            else:
                # Cross correlation
                expo_0 = expo_sphere(self.k0, self._koffset, self._pos_0[i])
                expo_1 = expo_sphere(self.k0, self._koffset, self._pos_1[i])

            # Define weights
            if self._weight is None:
                weight_0, weight_1 = 1.0, 1.0
            else:
                weight_0, weight_1 = self._weight_0[i], self._weight_1[i]

            # Nice spaghetti here
            for k, klist in enumerate(self._kvectors):
                for kvec in klist:
                    if expo_0 is expo_1:
                        # Identical species
                        if ndims == 3:
                            rho_0 = numpy.sum(weight_0 *
                                              expo_0[..., 0, kvec[0]] *
                                              expo_0[..., 1, kvec[1]] *
                                              expo_0[..., 2, kvec[2]])
                        elif ndims == 2:
                            rho_0 = numpy.sum(weight_0 *
                                              expo_0[..., 0, kvec[0]] *
                                              expo_0[..., 1, kvec[1]])
                        else:
                            tmp = weight_0 * expo_0[..., 0, kvec[0]]
                            for idim in range(1, ndims):
                                tmp *= expo_0[..., idim, kvec[idim]]
                            rho_0 = numpy.sum(tmp)

                        rho_1 = rho_0
                    else:
                        # Cross correlation
                        if ndims == 3:
                            rho_0 = numpy.sum(weight_0 *
                                              expo_0[..., 0, kvec[0]] *
                                              expo_0[..., 1, kvec[1]] *
                                              expo_0[..., 2, kvec[2]])
                            rho_1 = numpy.sum(weight_1 *
                                              expo_1[..., 0, kvec[0]] *
                                              expo_1[..., 1, kvec[1]] *
                                              expo_1[..., 2, kvec[2]])
                        elif ndims == 2:
                            rho_0 = numpy.sum(weight_0 *
                                              expo_0[..., 0, kvec[0]] *
                                              expo_0[..., 1, kvec[1]])
                            rho_1 = numpy.sum(weight_1 *
                                              expo_1[..., 0, kvec[0]] *
                                              expo_1[..., 1, kvec[1]])
                        else:
                            tmp = weight_0 * expo_0[..., 0, kvec[0]]
                            for idim in range(ndims):
                                tmp *= expo_0[..., idim, kvec[idim]]
                            rho_0 = numpy.sum(tmp)
                            tmp = weight_0 * expo_1[..., 0, kvec[0]]
                            for idim in range(ndims):
                                tmp *= expo_1[..., idim, kvec[idim]]
                            rho_1 = numpy.sum(tmp)

                    # Cumulate averages
                    rho_0_av[k] += rho_0
                    rho_1_av[k] += rho_1
                    rho2_av[k] += (rho_0 * rho_1.conjugate())
                    cnt[k] += 1

        # In the absence of a microscopic field, the average density is zero.
        # We get rid of the average and compute <rho(k)rho*(k)>.
        if self._weight_0 is None:
            rho_0_av = [complex(0., 0.) for k in kgrid]
            rho_1_av = [complex(0., 0.) for k in kgrid]

        # Normalization
        npart_0 = sum([p.shape[0] for p in self._pos_0]) / float(len(self._pos_0))
        npart_1 = sum([p.shape[0] for p in self._pos_1]) / float(len(self._pos_1))
        self.grid = kgrid
        self.value, self.value_nonorm = [], []
        for k in range(len(self.grid)):
            norm = float(npart_0 * npart_1)**0.5
            value = (rho2_av[k] / cnt[k] - rho_0_av[k] * rho_1_av[k].conjugate() / cnt[k]**2).real
            self.value.append(value / norm)
            self.value_nonorm.append(value)


class StructureFactorFast(StructureFactorLegacy):
    """
    Optimized structure factor.

    It uses a fortran 90 extension.
    """

    nbodies = 2
    symbol = 'sk'
    short_name = 'S(k)'
    long_name = 'structure factor'
    variables = ['pos']

    def _compute(self):
        from atooms.trajectory.utils import is_cell_variable
        try:
            from atooms.postprocessing.core import f90
        except ImportError:
            _log.error('f90 wrapper missing or not functioning')
            raise

        nsteps = len(self._pos_0)
        kgrid = self.kgrid
        assert self._weight is None, 'StructureFactorFast does not handle weights'

        # Setup k vectors and tabulate rho
        cnt = [0 for k in kgrid]
        rho_av = [complex(0., 0.) for k in kgrid]
        rho2_av = [complex(0., 0.) for k in kgrid]
        variable_cell = is_cell_variable(self.trajectory)
        for i in progress(range(0, nsteps, self.skip), total=nsteps // self.skip):
            # If cell changes we have to update the wave vectors
            if variable_cell:
                self._kgrid.setup(self.trajectory[i].cell.side)

            # Tabulate exponentials
            # Note: tabulating and computing takes about the same time
            if self._pos_0[i] is self._pos_1[i]:
                # Identical species
                expo_0 = expo_sphere(self.k0, self._koffset, self._pos_0[i])
                expo_1 = expo_0
            else:
                # Cross correlation
                expo_0 = expo_sphere(self.k0, self._koffset, self._pos_0[i])
                expo_1 = expo_sphere(self.k0, self._koffset, self._pos_1[i])

            for k, klist in enumerate(self._kvectors):
                # TODO: do it by transpose()
                # Fill array of kvectors in this bin                
                ikvec = numpy.ndarray((3, len(klist)), order='F', dtype=numpy.int32)
                for i, kvec in enumerate(klist):
                    ikvec[:, i] = kvec
                if self._pos_0[i] is self._pos_1[i]:
                    rho_0 = numpy.zeros(len(klist), dtype=numpy.complex128)
                    f90.fourierspace.sk_bare(expo_0, ikvec, rho_0)
                    rho_1 = rho_0
                else:
                    rho_0 = numpy.zeros(len(klist), dtype=numpy.complex128)
                    rho_1 = numpy.zeros(len(klist), dtype=numpy.complex128)
                    f90.fourierspace.sk_bare(expo_0, ikvec, rho_0)
                    f90.fourierspace.sk_bare(expo_1, ikvec, rho_1)
                rho2_av[k] += numpy.sum(rho_0 * rho_1.conjugate())
                cnt[k] += rho_0.shape[0]

        # Normalization.
        npart_0 = sum([p.shape[0] for p in self._pos_0]) / float(len(self._pos_0))
        npart_1 = sum([p.shape[0] for p in self._pos_1]) / float(len(self._pos_1))
        self.grid = kgrid
        self.value, self.value_nonorm = [], []
        for k in range(len(self.grid)):
            norm = float(npart_0 * npart_1)**0.5
            value = (rho2_av[k] / cnt[k] - rho_av[k]*rho_av[k].conjugate() / cnt[k]**2).real
            self.value.append(value / norm)
            self.value_nonorm.append(value)


# Defaults to legacy
StructureFactor = StructureFactorLegacy
# Backward compatible alias
StructureFactorOptimized = StructureFactorFast
