# This file is part of atooms
# Copyright 2010-2025, Daniele Coslovich

"""van Hove distribution function."""

from collections import defaultdict
import logging
import numpy

from .helpers import linear_grid
from .correlation import Correlation
from .helpers import setup_t_grid
from .progress import progress

__all__ = ['SelfVanHoveDistribution', 'DistinctVanHoveDistribution']

_log = logging.getLogger(__name__)
from atooms.postprocessing.core import f90

# Internal kernels
def _func_x(x, y, *args):
    return (x-y).ravel()

def _func_r(x, y, *args):
    return numpy.sqrt(numpy.sum((x-y)**2, axis=1))

def _func_distinct_r(x, y, box, nbl):
    distances = numpy.ndarray((nbl*x.shape[0]*2))
    for start in range(0, x.shape[0], nbl):
        k = f90.realspace.distances_distinct_c(1+start, 1+start+nbl, x, y, box, box/2, distances)
        yield distances[:k]

class _VanHoveDistribution(Correlation):

    def __init__(self, trajectory, tgrid=None, norigins=None, tsamples=10, rsamples=20,
                 no_offset=False, radial=True, **kwargs):
        self.tsamples = tsamples
        self.rsamples = rsamples
        self._norigins = norigins
        # Offsets in time grid are only relevant with periodic blocks
        # Use the no_offset parameter to disable them
        self._nblock = 10
        self._radial = radial
        self._func = _func_distinct_r
        Correlation.__init__(self, trajectory, tgrid, norigins=norigins, **kwargs)
        # Setup time grid
        if self.grid is None:
            t_max = self.trajectory.total_time
            self.grid = linear_grid(0.0, t_max, self.tsamples)
        # We disable offsets if only one time origin is requested or if no_offset is True
        self._discrete_tgrid = setup_t_grid(self.trajectory, self.grid,
                                            offset=self._norigins != '1' and not no_offset)
       
class SelfVanHoveDistribution(_VanHoveDistribution):
    """
    Self part of the van Hove distribution function.
    """

    symbol = 'gs'
    short_name = 'G_s(x,t)'
    long_name = 'self van Hove distribution function'
    variables = 'pos-unf'

    def __init__(self, trajectory, tgrid=None, norigins=None, tsamples=10, rsamples=20,
                 no_offset=False, radial=False, **kwargs):
        super().__init__(trajectory, tgrid=tgrid, norigins=norigins, tsamples=tsamples,
                         rsamples=rsamples, no_offset=no_offset, radial=radial,
                         **kwargs)
        if radial:
            self.short_name = 'G_s(r,t)'
            self._func = _func_r
        else:
            self.short_name = 'G_s(x,t)'
            self._func = _func_x
            
    def _compute(self):
        # Shortcuts
        grid, x, t = self._discrete_tgrid, self._pos_unf, self.trajectory.times

        # Find the binning range
        _max = defaultdict(list)
        for off, i in progress(grid, total=len(grid)):
            for i0 in range(off, len(x)-i, self.skip):
                dt = t[i0+i] - t[i0]
                dx = self._func(x[i0+i], x[i0])
                _max[dt].append(numpy.max(numpy.abs(dx)))

        # Get the global maximum for each time
        for dt in _max:
            _max[dt] = numpy.max(_max[dt])

        # Now compute the histogram
        hist, edges = {}, {}
        cnt = defaultdict(int)
        for off, i in progress(grid, total=len(grid)):
            for i0 in range(off, len(x)-i, self.skip):
                dt = t[i0+i] - t[i0]
                dx = self._func(x[i0+i], x[i0])
                if self._radial:
                    _range = (0, _max[dt])
                else:
                    _range = (-_max[dt], _max[dt])
                _hist, _edges = numpy.histogram(dx, bins=self.rsamples, range=_range,
                                                density=False)
                edges[dt] = (_edges[:-1] + _edges[1:]) / 2  # they are always the same
                cnt[dt] += 1
                if dt not in hist:
                    hist[dt] = _hist
                else:
                    hist[dt] += _hist

        # Update grid and values
        self.grid = [None, None]
        self.grid[0] = list(sorted(hist.keys()))
        self.grid[1] = [edges[dt] for dt in sorted(hist)]
        # TODO: fix normalization with radial average
        self.value = [hist[dt] / (cnt[dt] * (edges[dt][1] - edges[dt][0])) for dt in hist]

class DistinctVanHoveDistribution(_VanHoveDistribution):
    """
    Distinct part of the van Hove distribution function.
    """

    symbol = 'gd'
    short_name = 'G_d(r,t)'
    long_name = 'distinct van Hove distribution function'
    variables = 'pos'

    def __init__(self, trajectory, tgrid=None, norigins=None, tsamples=10, rsamples=20,
                 no_offset=False, radial=True, **kwargs):
        super().__init__(trajectory, tgrid=tgrid, norigins=norigins, tsamples=tsamples,
                         rsamples=rsamples, no_offset=no_offset, radial=radial,
                         **kwargs)
        assert radial, 'cannot compute G_d(x,t)'

    def _compute(self):
        # Shortcuts
        grid, x, t = self._discrete_tgrid, self._pos, self.trajectory.times
        # Now compute the histogram
        hist, edges = {}, {}
        cnt = defaultdict(int)
        # TODO: check that cell does not fluctuate
        box = self.trajectory[0].cell.side
        _range = (0, max(box) / 2)
        for off, i in progress(grid, total=len(grid)):
            #if i > 0: continue
            for i0 in range(off, len(x)-i, self.skip):
                dt = t[i0+i] - t[i0]
                # We group the distance calculation in blocks of size self._nblock
                cnt[dt] += 1
                for dx in _func_distinct_r(x[i0+i], x[i0], box, self._nblock):
                    _hist, _edges = numpy.histogram(dx, bins=self.rsamples,
                                                    range=_range, density=False)
                    edges[dt] = (_edges[:-1] + _edges[1:]) / 2  # always the same
                    if dt not in hist:
                        hist[dt] = _hist
                    else:
                        hist[dt] += _hist

        # Update grid and values
        self.grid = [None, None]
        self.grid[0] = list(sorted(hist.keys()))
        self.grid[1] = [edges[dt][:-1] for dt in sorted(hist)]
        vol = {dt: 0.5 * 4 * numpy.pi / 3 * (edges[dt][1:]**3 - edges[dt][:-1]**3) for dt in hist}
        self.value = [hist[dt][:-1] / (cnt[dt] * len(x[0]) * vol[dt]) for dt in hist]
