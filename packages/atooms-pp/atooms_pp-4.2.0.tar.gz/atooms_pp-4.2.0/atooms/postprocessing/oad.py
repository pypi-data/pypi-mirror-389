# This file is part of atooms
# Copyright 2010-2024, Daniele Coslovich

"""Orientational Angle distribution.

This module provides tools to compute the distribution of angles between
orientation vectors of neighboring molecules.
"""

import logging
import numpy
from .correlation import Correlation
from .progress import progress

__all__ = ['OrientationAngleDistribution']

_log = logging.getLogger(__name__)

# TODO: optimize all this
# TODO: fix PBC!
def _compute_neighbor_pairs(x, rcut):
    """
    Compute and return all pairs of particles in x that are separated by less than rcut.

    Parameters
    ----------
    x : numpy.ndarray
        Array of particle positions (N, D).
    rcut : float
        Cutoff distance to consider two particles as neighbors.

    Returns
    -------
    pairs : list of tuple
        List of index pairs (i, j) such that the distance between x[i] and x[j] is less than rcut.
    """
    n = x.shape[0]
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            rij = numpy.linalg.norm(x[i] - x[j])
            if rij < rcut:
                pairs.append((i, j))
    return pairs

def _apply_pairwise_function(f, x, pairs):
    """
    Apply a binary function f to all pairs of elements in x specified by pairs.

    Parameters
    ----------
    f : callable
        Function taking two arguments (elements of x) and returning a value.
    x : numpy.ndarray
        Array of elements to apply the function to.
    pairs : list of tuple
        List of index pairs (i, j) on which to apply f.

    Returns
    -------
    numpy.ndarray
        Array of results f(x[i], x[j]) for each pair.
    """
    fij = []
    for i, j in pairs:
        fij.append(f(x[i], x[j]))
    return numpy.array(fij)

def _angle_between_vectors(v1, v2):
    """
    Compute the angle (in radians) between two vectors v1 and v2.

    Parameters
    ----------
    v1, v2 : numpy.ndarray
        The two vectors to compare.

    Returns
    -------
    float
        The angle between v1 and v2 in radians.
    """
    v1, v2 = v1.flatten(), v2.flatten()
    dot = numpy.dot(v1, v2)
    norm1 = numpy.linalg.norm(v1)
    norm2 = numpy.linalg.norm(v2)
    return numpy.arccos(dot / (norm1 * norm2))

def _get_orientation(system, custom_orientation=None):
    """
    Extract and normalize the orientation vectors of each molecule in the system.

    Parameters
    ----------
    system : object
        System containing the molecules.
    custom_orientation : callable, optional
        Custom function to compute the orientation of a molecule.

    Returns
    -------
    numpy.ndarray
        Array of normalized orientation vectors for each molecule.
    """
    orientation = []
    molecule = system.molecule
    for molecule_i in molecule:
        # Select the appropriate orientation function
        if custom_orientation is None:
            orientation_i = molecule_i.orientation
        else:
            orientation_i = molecule_i.custom_orientation(custom_orientation)
        # Process each orientation element
        orientation_i = [elt / numpy.linalg.norm(elt) for elt in orientation_i]              
        orientation.append(orientation_i)
    return numpy.array(orientation)

def _get_cm_position(system):
    """
    Get the center of mass positions of all molecules in the system.

    Parameters
    ----------
    system : object
        System containing the molecules.

    Returns
    -------
    numpy.ndarray
        Array of center of mass positions for each molecule.
    """
    cm_pos = []
    for molecule in system.molecule:
        cm_pos.append(molecule.center_of_mass)
    return numpy.array(cm_pos)

class OrientationAngleDistribution(Correlation):
    """
    Orientation angle distribution between neighboring molecules.

    This class computes the histogram of angles between the orientation vectors
    of neighboring molecules, i.e., those separated by less than a given cutoff distance.

    Note: this distribution function cannot be used with `Partial` at the moment.

    Parameters
    ----------
    trajectory : Molecular trajectory
        Trajectory on which to perform the calculation.
    grid : array-like, optional
        Grid of bin centers for the angle histogram.
    custom_orientation : callable, optional
        Custom function to extract the orientation of a molecule.
    rcut : float, optional
        Cutoff distance to define neighbors (default 2).
    nbins : int, optional
        Number of bins for the histogram (default 10).

    Attributes
    ----------
    value : numpy.ndarray
        Computed histogram of angles.
    grid : numpy.ndarray
        Centers of the histogram bins.
    """

    nbodies = 2
    symbol = 'oa'
    short_name = 'D(theta)'
    long_name = 'orientation angle distribution'
    variables = [('pos', 'molecule.center_of_mass')]

    # TODO: align with bond angle distribution
    def __init__(self, trajectory, grid=None, orientation=None, rcut=None,
                 nbins=10, **kwargs):
        Correlation.__init__(self, trajectory, grid, **kwargs)
        # TODO: allow automatic calculation of rcut like in ba
        assert rcut is not None, 'provide rcut'
        self.grid = grid
        self.rcut = rcut
        self.nbins = nbins
        self.orientation = orientation
        self._hist_density = True

    def _setup_grid(self):
        """
        Initialize the grid of bins for the angle histogram.
        If no grid is provided, creates a linear grid from -pi to pi.
        """
        if self.grid is None:
            self.bin_edges = numpy.linspace(0, numpy.pi, self.nbins + 1)
            self.grid = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        else:
            bin_length = self.grid[1] - self.grid[0]
            self.bin_edges = numpy.empty((len(self.grid) + 1))
            for i in range(len(self.grid)):
                self.bin_edges[i] = (self.grid[i] - bin_length / 2)
            self.bin_edges[-1] = self.grid[-1] + bin_length / 2
            
    def _compute(self):
        """
        Compute the orientational angle distribution over the trajectory.

        For each configuration, extracts orientations, finds neighbors,
        computes angles between neighboring orientations, and builds the histogram.
        """
        ncfg = len(self.trajectory)
        system = self.trajectory.read(0)
        self._setup_grid()

        # Reconstruct bounds of grid for numpy histogram
        origins = range(0, ncfg, self.skip)
        angles = []
        for i in progress(origins):
            system = self.trajectory.read(i)
            
            # Get positions and orientation vectors of all CMs
            orientation = _get_orientation(system, self.orientation)
            # cm_position = _get_cm_position(system)
            cm_position = self._data['pos'][i]

            neighbours = _compute_neighbor_pairs(cm_position, self.rcut)
            # Calculate angle between orientation vectors. Only neighbour
            # molecules are considered
            angles.extend(_apply_pairwise_function(_angle_between_vectors, orientation, neighbours))

        # Compute and normalize histogram
        self.value, _ = numpy.histogram(angles, bins=self.bin_edges, density=self._hist_density)
        self.value /= numpy.sin(self.grid)
        
