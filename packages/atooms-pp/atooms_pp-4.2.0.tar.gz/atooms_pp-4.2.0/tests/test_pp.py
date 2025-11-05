#!/usr/bin/env python

import sys
import os
import random
import unittest
import numpy
from atooms import trajectory
import atooms.postprocessing as postprocessing
from atooms.postprocessing.helpers import filter_species


def filter_random(s, n):
    """Keep only n particles"""
    ids = random.sample(range(len(s.particle)), len(s.particle)-n)
    nop = [s.particle[i] for i in ids]
    for p in nop:
        s.particle.remove(p)
    return s

def filter_selected_ids(s, ids):
    """Keep only selected ids of particles"""
    nop = [s.particle[i] for i in ids]
    for p in nop:
        s.particle.remove(p)
    return s

def deviation(x, y):
    return (numpy.sum((x-y)**2)/len(x))**0.5

def filter_2d(s):
    s.cell.side = s.cell.side[0:2]
    s.cell.center = s.cell.center[0:2]
    for p in s.particle:
        p.position = p.position[0:2]
        p.velocity = p.velocity[0:2]
    return s

class Test(unittest.TestCase):

    def test_name(self):
        reference_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        default = postprocessing.core.pp_output_path
        postprocessing.core.pp_output_path = '{trajectory.filename}.pp.{qualified_name}.{tag_description}'
        corr = postprocessing.SelfIntermediateScattering(os.path.join(reference_path, 'trajectory.xyz'))
        self.assertEqual(os.path.basename(corr._output_file), 'trajectory.xyz.pp.F_s(k,t).the_whole_system')
        self.assertEqual(corr.grid_name, ['k', 't'])
        self.assertEqual(corr.qualified_name, 'F_s(k,t)')
        postprocessing.core.pp_output_path = default
        corr.trajectory.close()

        import atooms.postprocessing as pp
        import atooms.trajectory as trj
        th = trj.Trajectory(os.path.join(reference_path, 'kalj-small.xyz'))
        corr = pp.Partial(pp.SelfIntermediateScattering, th)
        self.assertEqual(set(['F_s_A(k,t)', 'F_s_B(k,t)']),
                         set([value.qualified_name for value in corr.partial.values()]))
        corr.compute()
        self.assertEqual(set(['F_s_A(k,t)', 'F_s_B(k,t)']), set(corr.results.keys()))
        self.assertEqual(corr.results['F_s_A(k,t)'].shape[0], 3)

        corr = pp.Partial(pp.StructureFactor, th)
        self.assertEqual(set(['S_{A-A}(k)', 'S_{A-B}(k)', 'S_{B-A}(k)', 'S_{B-B}(k)']),
                         set([value.qualified_name for value in corr.partial.values()]))

    def test_pickle(self):
        import pickle
        import atooms.postprocessing as pp
        import atooms.trajectory as trj
        reference_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        th = trj.Trajectory(os.path.join(reference_path, 'kalj-small.xyz'))
        corr = pp.SelfIntermediateScattering(th, kgrid=[7.0])
        corr.compute()
        corr.analyze()
        dump = pickle.dumps(corr)
        corr_pickled = pickle.loads(dump)
        self.assertEqual(corr.grid, corr_pickled.grid)
        self.assertEqual(corr.value, corr_pickled.value)
        self.assertEqual(corr.analysis, corr_pickled.analysis)
        th.close()

class TestRealSpace(unittest.TestCase):

    def setUp(self):
        self.reference_path = 'data'
        if not os.path.exists(self.reference_path):
            self.reference_path = os.path.join(os.path.dirname(sys.argv[0]), '../data')

    def test_vanhove(self):
        # TODO: add proper assertion
        def _plot():
            import matplotlib.pyplot as plt
            plot_func = plt.plot
            # This is the usual way: first grid index is t, second grid index is r
            for i, dt in enumerate(p.grid[0]):
                plot_func(p.grid[1][i], p.value[i], label=f'{dt}')
            plt.legend()
            plt.show()
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as ts:
            tgrid = numpy.linspace(0, ts.total_time/4, 5)
            p = postprocessing.vanhove.SelfVanHoveDistribution(ts, radial=True, tgrid=tgrid)
            p.compute()
            # _plot()
            p = postprocessing.vanhove.SelfVanHoveDistribution(ts, radial=False, tgrid=tgrid)
            p.compute()
            # _plot()
            p = postprocessing.vanhove.DistinctVanHoveDistribution(ts, rsamples=50,
                                                                   tgrid=tgrid)
            p.compute()
            #_plot()

    def test_msd_unfolding_fixcm(self):
        from atooms.trajectory import Unfolded

        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        tu = Unfolded(ts) #, fixed_cm=True)
        p = postprocessing.MeanSquareDisplacement(ts)
        t, msd = p.compute()
        p.add_filter(filter_species, 'B')
        ts = trajectory.TrajectoryXYZ(f)
        p = postprocessing.MeanSquareDisplacement(ts, fix_cm=True)
        t, _msd = p.compute()
        self.assertAlmostEqual(msd[-1], _msd[-1])

    def test_correlation_with_data(self):
        from atooms.postprocessing import Correlation, MeanSquareDisplacement,\
            RadialDistributionFunction
        from atooms.trajectory import TrajectoryXYZ

        class MyCorrelation(Correlation):
            variables = [('myvar', 'position')]
            nbodies = 2
        with TrajectoryXYZ(os.path.join(self.reference_path, 'kalj-small.xyz')) as th:
            cf = MyCorrelation(th, [])
            cf._setup_arrays()
        with TrajectoryXYZ(os.path.join(self.reference_path, 'kalj-small.xyz')) as th:
            cf0 = RadialDistributionFunction(th, [])
            cf0._setup_arrays()
        self.assertEqual(list(cf._data.keys()), ['myvar'])
        self.assertTrue(numpy.all(cf._data_0['myvar'][0] == cf0._data_0['pos'][0]))
        self.assertTrue(numpy.all(cf._data_1['myvar'][0] == cf0._data_1['pos'][0]))

        class MyCorrelation(Correlation):
            variables = [('myvar', 'position_unfolded')]
            nbodies = 1
        with TrajectoryXYZ(os.path.join(self.reference_path, 'kalj-small.xyz')) as th:
            cf = MyCorrelation(th, [])
            cf._setup_arrays()
            mydata = cf._data
        with TrajectoryXYZ(os.path.join(self.reference_path, 'kalj-small.xyz')) as th:
            cf = MeanSquareDisplacement(th, [])
            cf._setup_arrays()
            data = cf._data
        self.assertEqual(list(mydata.keys()), ['myvar'])
        self.assertTrue(numpy.all(mydata['myvar'][-1] == data['pos_unf'][-1]))

    def test_msd_partial(self):
        import warnings
        warnings.simplefilter('ignore', RuntimeWarning)
        from atooms.postprocessing.partial import Partial
        ref_grid = numpy.array([0, 3.0, 45.0, 90.0])
        ref_value = {'A': numpy.array([0.0, 0.12708190185520277, 1.2131017102523827, 2.1696872045992075]),
                     'B': numpy.array([0.0, 0.22107274740436153, 2.3018226393609473, 4.354207960272026])}

        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
            p = postprocessing.MeanSquareDisplacement(t, [0.0, 3.0, 45.0, 90])
            p.do()
            p = postprocessing.SelfIntermediateScattering(t, kgrid=[5.0, 6.0])
            p.do()

        # Filter species
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
            for i in ['A', 'B']:
                p = postprocessing.MeanSquareDisplacement(t, tgrid=[0.0, 3.0, 45.0, 90], fix_cm=True)
                p.add_filter(filter_species, i)
                p.compute()
                self.assertLess(deviation(p.grid, ref_grid), 4e-2)
                self.assertLess(deviation(p.value, ref_value[i]), 4e-2)

        # Pass species
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
            p = Partial(postprocessing.MeanSquareDisplacement, ['A', 'B'], t, [0.0, 3.0, 45.0, 90], fix_cm=True)
            p.do()
            for i in ['A', 'B']:
                self.assertLess(deviation(p.partial[i].grid, ref_grid), 4e-2)
                self.assertLess(deviation(p.partial[i].value, ref_value[i]), 4e-2)

        # Automatic detection
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
            p = Partial(postprocessing.MeanSquareDisplacement, t, [0.0, 3.0, 45.0, 90], fix_cm=True)
            p.compute()
            for i in ['A', 'B']:
                self.assertLess(deviation(p.partial[i].grid, ref_grid), 4e-2)
                self.assertLess(deviation(p.partial[i].value, ref_value[i]), 4e-2)

        f = os.path.join(self.reference_path, 'kalj-small-unfolded.xyz')
        for i in ['A', 'B']:
            with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
                p = postprocessing.MeanSquareDisplacement(t, [0.0, 3.0, 45.0, 90], fix_cm=True)
                p.add_filter(filter_species, i)
                p.compute()
                self.assertLess(deviation(p.grid, ref_grid), 4e-2)
                self.assertLess(deviation(p.value, ref_value[i]), 4e-2)

        # This calculation is correct, because filter is applied after unfolding
        # If we apply the filter to the trajectory, there are slight differences for small particles
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ts = trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1))
        for i in ['A', 'B']:
            p = postprocessing.MeanSquareDisplacement(ts, [0.0, 3.0, 45.0, 90], fix_cm=True)
            p.add_filter(filter_species, i)
            p.compute()
            self.assertLess(deviation(p.grid, ref_grid), 4e-2)
            self.assertLess(deviation(p.value, ref_value[i]), 4e-2)
        ts.close()

    def test_alpha2_partial(self):
        # TODO: refactor this test
        from atooms.postprocessing.partial import Partial

        ref_grid = numpy.array([0, 3.0, 45.0, 90.0])
        ref_value = {'A': numpy.array([0.0, 0.23826908036706707, 0.11017543614431814, 0.027930496964089325]),
                     'B': numpy.array([0.0, 0.32500088047702086, 0.0570248581420214, 0.027965490398575533])}
        cls = postprocessing.NonGaussianParameter

        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.Sliced(trajectory.TrajectoryXYZ(f), slice(0, 1000, 1)) as t:
            p = Partial(cls, ['A', 'B'], t, ref_grid)
            p.do()
            for i in ['A', 'B']:
                self.assertLess(deviation(p.partial[i].grid, ref_grid), 4e-2)
                self.assertLess(deviation(p.partial[i].value, ref_value[i]), 4e-2)

    def _test_gr_partial(self, cls):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        ref = {}
        ref[('A', 'A')] = numpy.array([0., 0.00675382, 0.27087136, 1.51486318])
        ref[('B', 'B')] = numpy.array([0.31065645, 0.51329066, 0.67485665, 0.78039485])
        ref[('A', 'B')] = numpy.array([4.25950671, 3.86572027, 2.70020052, 1.78935426])
        for i in ['A', 'B']:
            p = cls(ts)
            p.add_filter(filter_species, i)
            r, gr = p.compute()
            self.assertLess(deviation(gr[21:25], ref[(i, i)]), 4e-2)

        p = cls(ts)
        p.add_filter(filter_species, 'A')
        p.add_filter(filter_species, 'B')
        r, gr = p.compute()
        self.assertLess(deviation(gr[21:25], ref[('A', 'B')]), 4e-2)
        ts.close()

    def test_gr_partial_big(self):
        f = os.path.join(self.reference_path, 'ka_N20000.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        isp = 'B'
        res = {}
        grid = numpy.linspace(0.1, 5.0, int(5.0/0.1))
        p = postprocessing.RadialDistributionFunctionFast(ts, dr=0.1, rgrid=grid, rmax=-1)
        p.add_filter(filter_species, isp)
        res[-1] = p.compute()
        # TODO: fix issue with arbitrary grid
        p1 = postprocessing.RadialDistributionFunctionFast(ts, rmax=5)
        p1.add_filter(filter_species, isp)
        res[5] = p1.compute()
        #p.show(now=False)
        #p1.show()
        #self.assertLess(deviation(res[-1][1], res[5][1]), 1e-3)
        ts.close()

    def test_gr_big(self):
        f = os.path.join(self.reference_path, 'ka_N20000.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        p = postprocessing.RadialDistributionFunctionFast(ts, rmax=5)
        p.compute()
        #self.assertLess(deviation(res[-1][1], res[5][1]), 1e-6)
        ts.close()

    def test_gr_partial_fast(self):
        # This will test fast if available
        self._test_gr_partial(postprocessing.RadialDistributionFunction)

    def test_gr_partial_legacy(self):
        self._test_gr_partial(postprocessing.RadialDistributionFunctionLegacy)

    def test_gr_partial_2(self):
        from atooms.postprocessing.partial import Partial
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ref = {}
        ref[('A', 'A')] = numpy.array([0., 0.00675382, 0.27087136, 1.51486318])
        ref[('B', 'B')] = numpy.array([0.31065645, 0.51329066, 0.67485665, 0.78039485])
        ref[('A', 'B')] = numpy.array([4.25950671, 3.86572027, 2.70020052, 1.78935426])
        with trajectory.TrajectoryXYZ(f) as ts:
            gr = Partial(postprocessing.RadialDistributionFunction, ['A', 'B'], ts)
            gr.compute()
            for ab in [('A', 'A'), ('A', 'B'), ('B', 'B')]:
                self.assertLess(deviation(gr.partial[ab].value[21:25], ref[ab]), 4e-2)

    def test_gr_filter(self):
        from atooms.postprocessing.filter import Filter
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        ref = {}
        ref[('A', 'A')] = numpy.array([0., 0.00675382, 0.27087136, 1.51486318])
        ref[('B', 'B')] = numpy.array([0.31065645, 0.51329066, 0.67485665, 0.78039485])
        ref[('A', 'B')] = numpy.array([4.25950671, 3.86572027, 2.70020052, 1.78935426])

        gr = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "A", species == "A"')
        gr.compute()
        self.assertLess(deviation(gr.value[21:25], ref[('A', 'A')]), 4e-2)

        gr = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "A", species == "B"')
        gr.compute()
        self.assertLess(deviation(gr.value[21:25], ref[('A', 'B')]), 4e-2)

        gr = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "B", species == "B"')
        gr.compute()
        self.assertLess(deviation(gr.value[21:25], ref[('B', 'B')]), 4e-2)
        ts.close()

    def test_gr_filter_2(self):
        from atooms.postprocessing.filter import Filter
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ts = trajectory.TrajectoryXYZ(f)

        gr_AX = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "A"')
        gr_AX.compute()

        gr_AA = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "A", species == "A"')
        gr_AA.compute()

        gr_AB = Filter(postprocessing.RadialDistributionFunction(ts), 'species == "A", species == "B"')
        gr_AB.compute()

        self.assertLess(deviation(gr_AX.value[15:25], 0.8 * gr_AA.value[15:25] + 0.2 * gr_AB.value[15:25]), 0.04)
        ts.close()

    def test_gr_partial_2d_open(self):
        from atooms.trajectory import TrajectoryRam
        from atooms.system import System
        from atooms.postprocessing.partial import Partial
        import numpy
        numpy.random.seed(1)

        def fix_2d(system, periodic):
            system.cell.periodic = numpy.array(periodic)
            system.cell.side = system.cell.side[0: 2]
            for p in system.particle:
                p.position = p.position[0: 2]
            return system

        def _kernel(rmax, periodic):
            s = System(N=1000)
            for p in s.particle:
                p.position[:] = numpy.random.random(s.cell.side.shape) - 0.5
            s.density = 1.0
            s = fix_2d(s, periodic)
            ts = TrajectoryRam()
            ts.write(s)
            gr = postprocessing.RadialDistributionFunction(ts, dr=0.1, rmax=rmax)
            gr.compute()
            # import matplotlib.pyplot as plt
            # plt.plot(gr.grid, gr.value)
            # p = ts[0].dump('pos')
            # #plt.plot(p[:, 0], p[:, 1], 'o')
            # plt.show()
            ts.close()

            self.assertTrue(numpy.all(numpy.abs(gr.value - 1) < 0.1))

        _kernel(rmax=-1.0, periodic=[True, True])
        _kernel(rmax=+2.0, periodic=[True, True])
        _kernel(rmax=+2.0, periodic=[False, False])


class TestFourierSpace(unittest.TestCase):

    def setUp(self):
        random.seed(10)
        self.reference_path = 'data'
        if not os.path.exists(self.reference_path):
            self.reference_path = os.path.join(os.path.dirname(sys.argv[0]), '../data')

    def _test_sk(self, cls):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = cls(t, kmin=-1, kmax=4, ksamples=3, dk=0.2)
        p.compute()
        ref_value = numpy.array([0.075820086512828039, 0.065300213310725302, 0.082485082309989494])
        self.assertLess(deviation(p.value, ref_value), 0.04)
        # Trivial report dump (no check)
        txt = p.report()
        t.close()

    def test_sk(self):
        self._test_sk(postprocessing.StructureFactor)

    def test_sk_fast(self):
        try:
            from atooms.postprocessing.core import f90
            self._test_sk(postprocessing.StructureFactorFast)
        except ImportError:
            self.skipTest('missing f90')

    def test_sk_fixgrid(self):
        # TODO: this test fails with python 3 (small deviations)
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = postprocessing.StructureFactor(t, [4, 7.3, 10])
        p.compute()
        ref_value = numpy.array([0.083411717745282138, 2.76534619194135, 0.67129958432631986])
        self.assertLess(deviation(p.value, ref_value), 0.08)
        t.close()

    def assertAlmostEqualIter(self, x, y):
        for xi, yi in zip(x, y):
            self.assertAlmostEqual(xi, yi)

    def test_kvectors(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = postprocessing.StructureFactor(t, [4, 7.3, 10], nk=10)
        p.compute()
        kgrid = postprocessing.fourierspace.FourierSpaceGrid(kvectors=p.kvectors)
        kgrid.setup(t[0].cell.side)
        q = postprocessing.StructureFactor(t, kgrid=kgrid)
        self.assertAlmostEqualIter(q.kvectors, p.kvectors)
        self.assertAlmostEqualIter(q.kgrid, p.kgrid)
        q.compute()
        self.assertAlmostEqualIter(q.grid, p.grid)
        self.assertAlmostEqualIter(q.value, p.value)
        t.close()

    def test_fsgrid(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        grid = postprocessing.fourierspace.FourierSpaceGrid([4, 7.3, 10], nk=10)
        q = postprocessing.StructureFactor(t, [4, 7.3, 10], nk=10)
        self.assertAlmostEqualIter(q.kvectors, grid.kvectors)
        t.close()

    def test_sk_variable_cell(self):
        # TODO: this test has no assertion btw
        def deformation(s, scale=0.01):
            # Note this random scaling changes every time read is called,
            # even for the same sample
            x = 1 + (random.random()-0.5) * scale
            s.cell.side *= x
            for p in s.particle:
                p.position *= x
            return s
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as t:
            p = postprocessing.StructureFactor(t, [4, 7.3, 10])
            p.compute()
        with trajectory.TrajectoryXYZ(f) as t:
            t.add_callback(deformation, 1e-3)
            p = postprocessing.StructureFactor(t, [4, 7.3, 10])
            p.compute()

    def _test_sk_partial(self, cls):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ref_value = {'A': numpy.array([0.078218, 2.896436, 0.543363]),
                     'B': numpy.array([0.867164, 0.869868, 0.981121]),
                     'AB': numpy.array([-0.1907, 0.399360, 0.050480])}
        for species in ['A', 'B']:
            with trajectory.TrajectoryXYZ(f) as t:
                t.add_callback(filter_species, species)
                p = cls(t, [4, 7.3, 10])
                p.do()
                self.assertLess(deviation(p.value, ref_value[species]), 1e-1)

        with trajectory.TrajectoryXYZ(f) as t:
            sk = postprocessing.Partial(cls, ['A', 'B'], t, [4, 7.3, 10])
            sk.do()
            self.assertLess(deviation(sk.partial[('A', 'A')].value, ref_value['A']), 1e-1)
            self.assertLess(deviation(sk.partial[('B', 'B')].value, ref_value['B']), 1e-1)
            self.assertLess(deviation(sk.partial[('A', 'B')].value, ref_value['AB']), 1e-1)

    def test_sk_partial(self):
        self._test_sk_partial(postprocessing.StructureFactor)

    def test_sk_partial_fast(self):
        self._test_sk_partial(postprocessing.StructureFactorFast)

    def test_sk_random(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        t.add_callback(filter_random, 75)
        p = postprocessing.StructureFactor(t, [4, 7.3, 10, 30.0], nk=40)
        p.compute()
        t.close()

    def test_sk_field(self):
        """
        Test that S(k) with a field that is 0 if id=A and 1 if id=B gives
        the BB partial structure factor.
        """
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ff = os.path.join(self.reference_path, 'kalj-small-field.xyz')
        th = trajectory.TrajectoryXYZ(f)
        tt = trajectory.TrajectoryXYZ(ff)
        p = postprocessing.StructureFactor(th, [4, 7.3, 10])
        p.add_weight(trajectory=tt, field='field_B')
        p.compute()
        # We multiply by x because the S(k) is normalized to 1/N
        from atooms.system.particle import composition
        x = composition(th[0].particle)['B'] / float(len(th[0].particle))
        ref_value = x * numpy.array([0.86716496871363735, 0.86986885176760842, 0.98112175463699136])
        self.assertLess(deviation(p.value, ref_value), 1e-2)
        th.close()
        tt.close()

    def test_sk_field_partial(self):
        """
        Test that weight works with partial correlation
        """
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        ff = os.path.join(self.reference_path, 'kalj-small-field.xyz')
        th = trajectory.TrajectoryXYZ(f)
        p = postprocessing.Partial(postprocessing.StructureFactor, ['A', 'B'], th, [4, 7.3, 10])
        from atooms.postprocessing.helpers import copy_field
        from atooms.trajectory import TrajectoryXYZ
        p.add_weight(trajectory=trajectory.TrajectoryXYZ(ff), field='field_B')
        p.compute()
        from atooms.system.particle import composition
        ref_value = numpy.array([0.86716496871363735, 0.86986885176760842, 0.98112175463699136])
        zeros = numpy.zeros(3)
        self.assertLess(deviation(p.partial[('B', 'B')].value, ref_value), 2.3e-2)
        self.assertLess(deviation(p.partial[('A', 'A')].value, zeros), 2e-2)
        th.close()

    @unittest.skip('Broken test')
    def test_fkt_random(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as t:
            s = t[0]
            ids = random.sample(range(len(s.particle)), len(s.particle))
            t.add_callback(filter_selected_ids, ids)
            p = postprocessing.IntermediateScattering(t, [4, 7.3, 10], nk=40)
            p.compute()

    def test_fkt_partial(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = postprocessing.IntermediateScattering(t, [4, 7.3, 10], nk=40)
        p.add_filter(filter_species, 'A')
        p.tag = 'A'
        p.compute()
        p.analyze()
        tau = p.analysis['tau_c_A(k)'][1]
        self.assertLess(abs(tau[0] - 2.2792074711157104), 0.4)
        self.assertLess(abs(tau[1] - 5.8463508731564975), 0.4)
        self.assertLess(abs(tau[2] - 0.85719855804743605), 0.4)
        t.close()

    def test_fkt_nonorm_partial(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = postprocessing.IntermediateScattering(t, [4, 7.3, 10], nk=40, normalize=False)
        p.add_filter(filter_species, 'A')
        p.tag = 'A'
        p.compute()
        p.analyze()
        tau = p.analysis['tau_c_A(k)'][1]
        self.assertLess(abs(tau[0] - 2.2792074711157104), 0.4)
        self.assertLess(abs(tau[1] - 5.8463508731564975), 0.4)
        self.assertLess(abs(tau[2] - 0.85719855804743605), 0.4)
        t.close()

    def test_fskt_partial(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        for cls in [postprocessing.SelfIntermediateScatteringLegacy, postprocessing.SelfIntermediateScatteringFast]:
            p = cls(t, [4, 7.3, 10], nk=40, norigins=0.2)
            p.add_filter(filter_species, 'A')
            p.compute()
            p.analyze()
            tau = p.analysis['tau(k)'][1]
            self.assertLess(abs(tau[0] - 14.081572329287619), 0.04)
            self.assertLess(abs(tau[1] - 3.1034088042905967), 0.04)
            self.assertLess(abs(tau[2] - 0.97005294966138289), 0.04)
        t.close()

    def test_fskt_mask(self):
        import numpy
        def mask_species(th, frame, species):
            return th[frame].view('species') == species
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        pf = postprocessing.SelfIntermediateScattering(t, [7.3], nk=40, norigins=0.2)
        pf.add_filter(filter_species, 'A')
        pf.compute()
        p = postprocessing.SelfIntermediateScattering(t, [7.3], nk=40, norigins=0.2)
        p.add_mask(mask_species, 'A')
        p.compute()
        self.assertEqual(p.value, pf.value)
        t.close()
        
    def test_fskt_from_array(self):
        from atooms.system import System

        from atooms.core._version import __version__
        x, y, z = __version__.split('.')
        if int(x) <= 2 or (int(x) == 3 and int(y) <= 14):
            self.skipTest('passing only with atooms >= 3.15.0')

        f = os.path.join(self.reference_path, 'kalj-small.xyz')

        # Get positions and species as numpy array
        pos, spe, box = [], [], []
        with trajectory.TrajectoryXYZ(f) as th:
            for s in th:
                pos.append(s.dump('position'))
                spe.append(s.dump('species'))
                box.append(s.dump('box'))

        # Keep trajectory in RAM
        with trajectory.TrajectoryRam() as th:
            for p, i, b in zip(pos, spe, box):
                s = System(N=p.shape[0])
                s.cell.side[:] = b
                s.view('species')[:] = i
                s.view('position')[:, :] = p
                th.append(s)

        p = postprocessing.SelfIntermediateScattering(th, [4, 7.3, 10], nk=40, norigins=0.2)
        p.add_filter(filter_species, 'A')
        p.compute()
        p.analyze()
        tau = p.analysis['tau(k)'][1]
        self.assertLess(abs(tau[0] - 14.081572329287619), 0.04)
        self.assertLess(abs(tau[1] - 3.1034088042905967), 0.04)
        self.assertLess(abs(tau[2] - 0.97005294966138289), 0.04)
        th.close()

    def test_chi4_overlap(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as th:
            tgrid = postprocessing.helpers.logx_grid(0.0, th.total_time * 0.5, 10)
            fct = postprocessing.Susceptibility(postprocessing.SelfOverlap, th, tgrid=tgrid)
            fct.compute()
            ref = postprocessing.Chi4SelfOverlap(th, tgrid=tgrid)
            ref.compute()
            self.assertLess(deviation(numpy.array(ref.value), numpy.array(fct.value)), 0.1)

    def test_s4kt_overlap(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as th:
            tgrid = [th.times[0]]
            s4k = postprocessing.S4ktOverlap(th, tgrid=tgrid, kgrid=numpy.linspace(3, 10, 3))
            s4k.do()
            sk = postprocessing.StructureFactor(th, kgrid=numpy.linspace(3, 10, 3))
            sk.do()
            self.assertLess(deviation(numpy.array(sk.value), numpy.array(s4k.value)), 0.1)

    def test_fskt_2d(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        t.add_callback(filter_2d)
        p = postprocessing.SelfIntermediateScattering(t, [4, 7.3, 10], nk=10)
        p.add_filter(filter_species, 'A')
        p.compute()
        p.analyze()
        tau = p.analysis['tau(k)'][1]
        self.assertLess(abs(tau[0] - 13.48342847723456), 0.04)
        self.assertLess(abs(tau[1] - 3.07899513664358), 0.04)
        self.assertLess(abs(tau[2] - 0.9802163934982774), 0.04)
        t.close()

    def test_fskt_legacy_2d(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        t.add_callback(filter_2d)
        p = postprocessing.SelfIntermediateScatteringLegacy(t, [4, 7.3, 10], nk=10)
        p.add_filter(filter_species, 'A')
        p.compute()
        p.analyze()
        tau = p.analysis['tau(k)'][1]
        self.assertLess(abs(tau[0] - 13.48342847723456), 0.04)
        self.assertLess(abs(tau[1] - 3.07899513664358), 0.04)
        self.assertLess(abs(tau[2] - 0.9802163934982774), 0.04)
        t.close()

    def test_fkt_2d(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        t.add_callback(filter_2d)
        p = postprocessing.IntermediateScattering(t, [4, 7.3, 10], nk=100)
        p.add_filter(filter_species, 'A')
        p.compute()
        p.analyze()
        tau = p.analysis['tau_c(k)'][1]
        self.assertLess(abs(tau[0] - 1.1341521365187757), 0.04)
        self.assertLess(abs(tau[1] - 5.83114954720099), 0.04)
        self.assertLess(abs(tau[2] - 0.859950963462569), 0.04)
        t.close()

    def test_sk_2d(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        t.add_callback(filter_2d)
        p = postprocessing.StructureFactorLegacy(t, kmin=-1, kmax=4, ksamples=3, dk=0.2)
        p.compute()
        ref_value = numpy.array([[0.06899986228704291, 0.0629709003150001, 0.07397620251792263]])
        self.assertLess(deviation(p.value, ref_value), 0.04)
        t.close()

    def test_fourierspace_kgrid_unsorted(self):
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p_sorted = postprocessing.SelfIntermediateScatteringLegacy(t, [4, 7.3, 10], nk=40, norigins=0.2)
        p_unsorted = postprocessing.SelfIntermediateScatteringLegacy(t, [10, 4, 7.3], nk=40, norigins=0.2)

        p_sorted.compute()
        p_sorted.analyze()
        p_unsorted.compute()
        p_unsorted.analyze()

        self.assertEqual(p_sorted.kgrid, p_unsorted.kgrid)
        self.assertLess(deviation(numpy.array(p_sorted.value), numpy.array(p_unsorted.value)), 1e-14)
        t.close()

    def test_ba(self):
        """Check on cut-off for neighbors determination"""
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        t = trajectory.TrajectoryXYZ(f)
        p = postprocessing.BondAngleDistribution(t)
        p.compute()
        q = postprocessing.BondAngleDistribution(t, rcut=p.rcut)
        q.compute()
        self.assertLess(deviation(p.value, q.value), 0.001)
        t.close()

    def test_gr_crop(self):
        """Test gr with a non-periodic, inifinite bounding cell"""
        import numpy
        import atooms.postprocessing as pp
        import atooms.trajectory as trj
        import atooms.system
        numpy.random.seed(10)
        N = 5000
        L = 1000.0
        pos = numpy.random.random([N, 3]) * L
        system = atooms.system.System()
        system.particle = [atooms.system.Particle(position=pos[i, :]) for i in range(N)]

        def center(system):
            cm = system.cm_position
            for p in system.particle:
                p.position[:] -= cm
            return system

        def bounding_box(system):
            L = []
            periodic = numpy.ndarray(system.number_of_dimensions, dtype=bool)
            periodic[:] = False
            for axis in range(system.number_of_dimensions):
                L.append(1.01 * 2 * numpy.max([abs(p.position[axis]) for p in system.particle]))
            system.cell = atooms.system.Cell(L, periodic=periodic)
            return system

        def crop(system, L):
            new = []
            for p in system.particle:
                if numpy.all(numpy.abs(p.position) < L / 2):
                    new.append(p)
            system.particle = new
            return system

        rmax = L / 10
        th = trj.TrajectoryRam()
        th[0] = system
        th.add_callback(center)
        th.add_callback(crop, numpy.array([L, L, L]))
        th.add_callback(bounding_box)

        cf = pp.RadialDistributionFunction(th, rmax=rmax)
        cf.compute()
        self.assertLess(abs(cf.value[-1] - 1.0), 0.1)

        cf = pp.BondAngleDistribution(th, rcut=[[50.0]])
        cf.compute()
        self.assertLess(cf.value[len(cf.value)//2], 0.01)

    def test_crop(self):
        """Test crop an existing system"""
        import numpy
        import atooms.postprocessing as pp
        import atooms.trajectory as trj
        import atooms.system

        def crop(system, L):
            new = []
            for p in system.particle:
                if numpy.all(numpy.abs(p.position) < L / 2):
                    new.append(p)
            system.particle = new
            system.cell.periodic[:] = False
            return system

        def open_boundary(system):
            system.cell.periodic[:] = False
            return system

        def no_boundary(system):
            system.cell = None
            return system

        dL = 3.0

        # gr
        f = os.path.join(self.reference_path, 'ka_N20000.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        p = pp.RadialDistributionFunctionFast(ts, rmax=dL)
        p.compute()
        #ts.add_callback(crop, ts[0].cell.side - dL)
        ts.add_callback(open_boundary)
        pc = pp.RadialDistributionFunction(ts, rmax=dL)
        pc.compute()
        ts.close()
        for x, y in zip(pc.value, p.value):
            self.assertLess(abs(x-y), 0.05)

        # ba
        f = os.path.join(self.reference_path, 'ka_N20000.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        p = pp.BondAngleDistribution(ts, rcut=[[1.5, 1.5], [1.5, 1.5]])
        p.compute()
        ts.add_callback(open_boundary)
        pc = pp.BondAngleDistribution(ts, rcut=[[1.5, 1.5], [1.5, 1.5]])
        pc.compute()
        for x, y in zip(pc.value, p.value):
            self.assertLess(abs(x-y), 0.05)

        # ba
        f = os.path.join(self.reference_path, 'ka_N20000.xyz')
        ts = trajectory.TrajectoryXYZ(f)
        p = pp.BondAngleDistribution(ts, rcut=[[1.5, 1.5], [1.5, 1.5]])
        p.compute()
        ts.add_callback(no_boundary)
        pc = pp.BondAngleDistribution(ts, rcut=[[1.5, 1.5], [1.5, 1.5]])
        pc.compute()
        for x, y in zip(pc.value, p.value):
            self.assertLess(abs(x-y), 0.05)

    def test_partial_plot(self):
        from atooms.postprocessing.partial import Partial
        f = os.path.join(self.reference_path, 'kalj-small.xyz')
        with trajectory.TrajectoryXYZ(f) as th:
            p = Partial(postprocessing.MeanSquareDisplacement, th)
            p.compute()
            p.plot(show=False)
        
if __name__ == '__main__':
    unittest.main()
