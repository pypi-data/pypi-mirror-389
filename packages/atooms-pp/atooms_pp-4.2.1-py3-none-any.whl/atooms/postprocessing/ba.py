# This file is part of atooms
# Copyright 2010-2025, Daniele Coslovich

"""Bond angle distribution."""

import sys
import math
import logging

import numpy

from .helpers import linear_grid
from .correlation import Correlation
from .progress import progress

__all__ = ['BondAngleDistribution']

_log = logging.getLogger(__name__)


def _default_rcut(th):
    """
    Look for the first minimum in the partial g(r)
    """
    from atooms.system.particle import distinct_species
    from atooms.postprocessing.partial import Partial
    from atooms.postprocessing import RadialDistributionFunction
    from .helpers import ifabsmm

    ids = distinct_species(th[0].particle)
    gr = Partial(RadialDistributionFunction, ids, th, dr=0.1)
    gr.do()
    rcut = {}
    for isp in ids:
        for jsp in ids:
            # First find absolute maximum
            _, m = ifabsmm(list(gr.partial[(isp, jsp)].grid),
                           list(gr.partial[(isp, jsp)].value))
            # Then look for first minimum after the maximum
            for i in range(len(gr.partial[(isp, jsp)].grid)):
                if gr.partial[(isp, jsp)].grid[i] >= m[0]:
                    delta = gr.partial[(isp, jsp)].value[i+1] - gr.partial[(isp, jsp)].value[i]
                    if delta >= 0:
                        rcut[(isp, jsp)] = gr.partial[(isp, jsp)].grid[i]
                        break

    return rcut

class BondAngleDistribution(Correlation):
    """
    Bond angle distribution function.
    """

    nbodies = 2
    symbol = 'ba'
    short_name = 'D(theta)'
    long_name = 'bond-angle distribution'
    variables = ['pos', 'ids']
    _symmetric = False

    def __init__(self, trajectory, dtheta=4.0, rcut=None, **kwargs):
        Correlation.__init__(self, trajectory, None, **kwargs)
        self.grid = linear_grid(0.0, 180.0, dtheta)  # reassign grid anyway
        self.rcut = rcut

    def _compute(self):
        from atooms.trajectory.decorators import change_species
        from atooms.system.particle import distinct_species        
        from atooms.postprocessing.core import f90
       
        hist_all = []
        hist_one = numpy.ndarray(len(self.grid), dtype=numpy.int32)
        origins = range(0, len(self.trajectory), self.skip)
        dtheta = self.grid[1] - self.grid[0]

        # Setup array of cutoff distances based on g(r) calculated for
        # the whole trajectory.
        # We store the cutoffs into a (nsp, nsp) array
        # where the index follows the alphabetic order of species names
        ids = distinct_species(self.trajectory[0].particle)
        if self.rcut is None:
            rcut = _default_rcut(self.trajectory)
            self.rcut = numpy.ndarray((len(ids), len(ids)))
            for species_pair in rcut:
                self.rcut[ids.index(species_pair[0]), ids.index(species_pair[1])] = rcut[species_pair]
        else:
            self.rcut = numpy.array(self.rcut)

        for isp in range(len(ids)):
            for jsp in range(len(ids)):
                self._analysis[f'cutoff distance, rc_{isp}-{jsp}'] = self.rcut[isp, jsp]

        for frame in progress(origins):
            system = self.trajectory[frame]
            ndims = system.number_of_dimensions
            pos_0 = self._pos_0[frame]
            pos_1 = self._pos_1[frame].transpose()
            # ids_0 = numpy.array(self._ids_0[frame], dtype=numpy.int32)
            # ids_1 = numpy.array(self._ids_1[frame], dtype=numpy.int32)
            from .helpers import _set_species_layout
            # TODO: we modify the underlying data, this is not clean but reasonably safe
            ids_0 = numpy.array(_set_species_layout(self._ids_0[frame], 'C'), dtype=numpy.int32)
            ids_1 = numpy.array(_set_species_layout(self._ids_1[frame], 'C'), dtype=numpy.int32)
            # With a non-periodic cell, which just bounds the physical
            # domain, we crop particles away from the surface (within rmax)
            if system.cell is not None and hasattr(system.cell, 'periodic') and \
               sum(system.cell.periodic) == 0:
                # Booleans do not work here, so we just use integers,
                # which are 1 is particles are on the surface and 0 otherwise
                mask = f90.realspace.on_surface_c(pos_0, system.cell.side, numpy.max(self.rcut))
                pos_0 = pos_0[mask == 0, :]
                ids_0 = ids_0[mask == 0]

            # Store side (copied over from gr)
            # TODO: refactor
            # If there is no cell and anyway along non-periodic directions,
            # we replace sides with infty to work with f90 kernels (which apply PBC)
            if system.cell is not None:
                side = system.cell.side.copy()
                # TODO: fix partly periodic boundaries
                assert sum(system.cell.periodic) in [0, ndims], 'partly periodic cells not supported'
                for i in range(len(side)):
                    if not system.cell.periodic[i]:
                        side[i] = sys.float_info.max
            else:
                # If the system does not have a cell, wrap it in an
                # infinite cell. This way we can still use PBC in f90 kernels
                side = sys.float_info.max * numpy.ones(ndims, dtype=float)
            
            nn = numpy.array(0, dtype=numpy.int32)
            # TODO: max neighbors is hardcoded
            neighbors = numpy.ndarray(50, dtype=numpy.int32)
            for idx in range(len(pos_0)):
                isp = ids_0[idx]
                f90.realspace.neighbors('C', side, pos_0[idx], pos_1, ids_1,
                                        self.rcut[isp, :], nn, neighbors)
                f90.realspace.bond_angle(pos_0[idx, :], pos_1, neighbors[0: nn],
                                         side, dtheta, hist_one)
                hist_all.append(hist_one.copy())

        # Normalization
        hist = numpy.sum(hist_all, axis=0)
        norm = float(numpy.sum(hist[:-1]))
        self.grid = (numpy.array(self.grid[:-1]) + numpy.array(self.grid[1:])) / 2.0
        self.value = hist[:-1] / (norm * dtheta)
