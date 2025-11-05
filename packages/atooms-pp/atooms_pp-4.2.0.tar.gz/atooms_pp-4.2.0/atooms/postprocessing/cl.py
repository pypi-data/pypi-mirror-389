# This file is part of atooms
# Copyright 2010-2025, Daniele Coslovich

"""Rotational Time-Correlation Functions"""

import logging
import numpy
import re
try:
    from scipy.special import eval_legendre
except ImportError:
    def eval_legendre(l, x):
        if l == 1:
            return x
        elif l == 2:
            return (3*x**2 - 1) / 2
        elif l == 3:
            return (5*x**3 - 3*x) / 2
        elif l == 4:
            return (35*x**4 - 30*x**2 + 3) / 8
        elif l == 5:
            return (63*x**5 - 70*x**3 + 15*x) / 8
        else:
            print('Cannot compute Legendre polynomials for l>5 w/o scipy')
            raise

from .helpers import linear_grid
from .correlation import Correlation, gcf_offset
from .helpers import setup_t_grid

__all__ = ['RotationalCorrelation', 'EndToEndCorrelation', 'C1Correlation', 'C2Correlation']

_log = logging.getLogger(__name__)


class RotationalCorrelation(Correlation):
    """
    Rotational Correlation
    """

    variables = ['molecule.theta']

    def __init__(self, trajectory, l=1, custom_orientation=None, unit_orientation=True, tgrid=None, norigins=None,
                 tsamples=30, no_offset=False, **kwargs):
        self.symbol = f'c{l}'
        self.short_name = f'C_{l}(t)'
        self.long_name = f'Rotational time-correlation of order {l}'
        self.l = l
        """Order of Legendre polynomial"""
        self.tsamples = tsamples
        self._norigins = norigins
        # Offsets in time grid are only relevant with periodic blocks
        # Use the no_offset parameter to disable them
        self._no_offset = no_offset
        Correlation.__init__(self, trajectory, tgrid, norigins=norigins, **kwargs)
        self._ndim = self.trajectory.read(0).number_of_dimensions
        self.unit_orientation = unit_orientation
        if isinstance(custom_orientation, str):
            custom_orientation = [custom_orientation]

        # Callback to set the theta molcule attribute
        def _get_theta(system, orientation):
            for m in system.molecule:
                if orientation:
                    m.theta = m.custom_orientation(orientation)
                else:
                    m.theta = m.orientation
            return system
        self.trajectory.add_callback(_get_theta, custom_orientation)

    # def _get_orientation(self):
    #     self._orientation = []
    #     for system in self.trajectory:
    #         orientation_step = []
    #         for molecule in system.molecule:
    #             orientation_i = []
    #             # Select the appropriate orientation function
    #             if self.custom_orientation is None:
    #                 orientations = molecule.orientation
    #             else:
    #                 orientations = molecule.custom_orientation(self.custom_orientation)
    #             # Process each orientation element                
    #             for elt in orientations:
    #                 if self.unit_orientation:
    #                     elt =  elt / numpy.linalg.norm(elt)
    #                 orientation_i.append(elt)
    #             orientation_step.append(orientation_i)
    #         self._orientation.append(orientation_step)
    #     self._orientation = numpy.array(self._orientation)

    def _compute(self):
        def cl(x, y):
            # dot_product = numpy.dot(x.flatten(), y.flatten()) / x.shape[0] / x.shape[1]
            dot_product = numpy.array([numpy.dot(_x[0], _y[0]) for _x, _y in zip(x, y)])
            return numpy.mean(eval_legendre(self.l, dot_product)).item()

        # self._get_orientation()
        theta = self._data['molecule.theta']
        if self.unit_orientation:
            theta /= numpy.linalg.norm(theta, axis=-1, keepdims=True)
            
        if self.grid is None:
            t_max = self.trajectory.total_time
            self.grid = linear_grid(0.0, t_max, self.tsamples)

        # Setup time grid
        # We disable offsets if only one time origin is requested or if no_offset is True
        self._discrete_tgrid = setup_t_grid(self.trajectory, self.grid,
                                            offset=self._norigins != '1' and not self._no_offset)
        # Note that the grid is redefined
        self.grid, self.value = gcf_offset(cl, self._discrete_tgrid, self.skip,
                                           self.trajectory.steps, theta)
        # To normalize, t=0 must be in the grid
        # assert self.grid[0] == 0.0
        # self.value = [x / self.value[0] for x in self.value]
        # Update grid to real time
        self.grid = [ti * self.trajectory.timestep for ti in self.grid]

# class RotationalCorrelationBis(RotationalCorrelation):
    
#     def _compute(self):
#         def cl(x, y):
#             # dot_product = numpy.dot(x.flatten(), y.flatten()) / x.shape[0] / x.shape[1]
#             dot_product = numpy.array([numpy.dot(_x[0], _y[0]) for _x, _y in zip(x, y)])
#             return numpy.mean(eval_legendre(self.l, dot_product))

#         theta = self._data['molecule.theta']
#         if self.unit_orientation:
#             theta /= numpy.linalg.norm(theta, axis=-1, keepdims=True)
#         if self.grid is None:
#             t_max = self.trajectory.total_time
#             self.grid = linear_grid(0.0, t_max, self.tsamples)

#         # Setup time grid
#         # We disable offsets if only one time origin is requested or if no_offset is True
#         self._discrete_tgrid = setup_t_grid(self.trajectory, self.grid,
#                                             offset=self._norigins != '1' and not self._no_offset)
#         # Note that the grid is redefined
#         self.grid, self.value = gcf_offset(cl, self._discrete_tgrid, self.skip,
#                                            self.trajectory.steps, theta)
#         # To normalize, t=0 must be in the grid
#         # assert self.grid[0] == 0.0
#         # self.value = [x / self.value[0] for x in self.value]
#         # Update grid to real time
#         self.grid = [ti * self.trajectory.timestep for ti in self.grid]
        
# Shortcuts

class EndToEndCorrelation(RotationalCorrelation):
    symbol = 'e2e'
    short_name = 'C_{e2e}(t)'
    long_name = 'End-to-end time-correlation'
    def __init__(self, trajectory, l=1, unit_orientation=True, tgrid=None, norigins=None,
                 tsamples=30, no_offset=False, **kwargs):
        super().__init__(trajectory, l=l, custom_orientation='etoe', unit_orientation=unit_orientation,
                         tgrid=tgrid, norigins=norigins, tsamples=tsamples, no_offset=no_offset, **kwargs)

class C1Correlation(RotationalCorrelation):
    symbol = 'c1'
    short_name = 'C_1(t)'
    long_name = 'Rotational time-correlation of order 1'
    def __init__(self, trajectory, custom_orientation=None, tgrid=None, norigins=None,
                 tsamples=30, no_offset=False, **kwargs):
        super().__init__(trajectory, l=1, custom_orientation=custom_orientation, unit_orientation=True,
                         tgrid=tgrid, norigins=norigins, tsamples=tsamples, no_offset=no_offset, **kwargs)

class C2Correlation(RotationalCorrelation):
    symbol = 'c2'
    short_name = 'C_2(t)'
    long_name = 'Rotational time-correlation of order 2'
    def __init__(self, trajectory, custom_orientation=None, tgrid=None, norigins=None,
                 tsamples=30, no_offset=False, **kwargs):
        super().__init__(trajectory, l=2, custom_orientation=custom_orientation, unit_orientation=True,
                         tgrid=tgrid, norigins=norigins, tsamples=tsamples, no_offset=no_offset, **kwargs)

