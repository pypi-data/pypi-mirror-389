# Postprocessing

[![pypi](https://img.shields.io/pypi/v/atooms-pp.svg)](https://pypi.python.org/pypi/atooms-pp/)
[![version](https://img.shields.io/pypi/pyversions/atooms-pp.svg)](https://pypi.python.org/pypi/atooms-pp/)
[![license](https://img.shields.io/pypi/l/atooms-pp.svg)](https://en.wikipedia.org/wiki/GNU_General_Public_License)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fframagit.org%2Fatooms%2Fpostprocessing/HEAD?labpath=docs%2Findex.ipynb)
[![pipeline](https://framagit.org/atooms/postprocessing/badges/master/pipeline.svg)](https://framagit.org/atooms/postprocessing/badges/master/pipeline.svg)
[![coverage report](https://framagit.org/atooms/postprocessing/badges/master/coverage.svg)](https://framagit.org/atooms/postprocessing/-/commits/master)

A Python package to compute static and dynamic correlation functions from simulations of interacting particles, such as molecular dynamics or Monte Carlo simulations. Based on [atooms](https://framagit.org/atooms/atooms).

## Quick start

Postprocessing works on trajectories. Any trajectory format recognized by
[atooms](https://framagit.org/atooms/atooms.git) can be processed, for instance most "xyz" files
should work fine. If you use a custom trajectory format, it is easy to [add it](https://atooms.frama.io/atooms/).

As an example, we compute the structure factor S(k) from the file `trajectory.xyz` in the `data/` folder.

### From the command line

```sh
pp.py --norigins 0.2 msd data/trajectory.xyz
```
We just used 20% of the available time frames to compute the averages using the `--norigins` flag. Without it, `atooms-pp` applies an heuristics to determine the number of time frames required to achieve a reasonable data quality. The results of the calculation are stored in the file `data/trajectory.xyz.pp.sk`. 

### From Python

The same calculation can be done from Python:

```python
from atooms.trajectory import Trajectory
import atooms.postprocessing as pp

with Trajectory('data/trajectory.xyz') as t:
     p = pp.StructureFactor(t)
     p.do()
```

## Features

Available correlation and distribution functions

- *Real space*
  - radial distribution function
  - mean square displacement
  - velocity auto-correlation function
  - self overlap functions
  - collective overlap functions
  - dynamic susceptibility of the self overlap function
  - non-Gaussian parameter
  - bond-angle distribution
  - self van Hove distribution function
  - distinct van Hove distribution function
  - orientational time-dependent correlation functions
  - orientation-angle distribution
- *Fourier space*
  - structure factor
  - spectral density
  - self intermediate scattering functions
  - collective intermediate scattering functions
  - four-point dynamic susceptibility

Most correlation functions admits a center-of-mass variant suitable for the molecular centers of mass.

## Documentation

Check out the [tutorial](https://atooms.frama.io/docs/) for more examples and the [public API](https://atooms.frama.io/postprocessing/api/postprocessing) for full details.

Org-mode and jupyter notebooks are available under `docs/`. You can run the tutorial interactively on [Binder]( https://mybinder.org/v2/git/https%3A%2F%2Fframagit.org%2Fatooms%2Fpostprocessing/HEAD?labpath=docs%2Findex.ipynb).

## Installation

Install with `pip`
```
pip install atooms-pp
```

Or clone the project repository
```
git clone https://framagit.org/atooms/postprocessing.git
cd postprocessing
make install
```

## Contributing

Contributions to the project are welcome. If you wish to contribute, check out [these guidelines](https://framagit.org/atooms/atooms/-/blob/master/CONTRIBUTING.md).

## Authors

Daniele Coslovich: https://www.units.it/daniele.coslovich/
