#!/usr/bin/env python
import unittest
import numpy
from atooms.trajectory import MolecularTrajectoryXYZ
from atooms.postprocessing.cl import RotationalCorrelation, C1Correlation, \
    C2Correlation, EndToEndCorrelation

# TODO: speed up these tests / optimize cl correlations
class Test(unittest.TestCase):

    def test_orient(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ

        finp = '/tmp/test_molecular.xyz'
        molecule = Molecule([Particle(position=[1.0, 0.0], species=1),
                             Particle(position=[0.0, 0.0], species=2),
                             Particle(position=[0.0, 1.0], species=2),], bond=[0, 1])
        s = System(molecule=[Molecule([Particle(position=[1.0, 0.0], species=1),
                                       Particle(position=[0.0, 0.0], species=2),
                                       Particle(position=[0.0, 1.0], species=2)],
                                      bond=[0, 1]) for _ in range(10)],
                   cell=Cell([6.0, 6.0]))

        numpy.random.seed(1)
        with MolecularTrajectoryXYZ(finp, 'w') as th:
            for step in range(1000):
                th.write(s, step)
                for m in s.molecule:
                    theta = 0.5*(numpy.random.random() - 0.5)
                    m.rotate(theta)

        with MolecularTrajectoryXYZ(finp) as th:
            cf = EndToEndCorrelation(th)
            cf.compute()
            self.assertAlmostEqual(cf.value[0], 1.0)
            #cf.show()
            cf = C1Correlation(th)
            cf.compute()
            self.assertAlmostEqual(cf.value[0], 1.0)
            #cf.show()
            cf = C2Correlation(th)
            cf.compute()
            self.assertAlmostEqual(cf.value[0], 1.0)
            #cf.show()

    def test_orient_place(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ

        finp = '/tmp/test_molecular.xyz'
        molecule = Molecule([Particle(position=[1.0, 0.0, 0.], species=1),
                             Particle(position=[0.0, 0.0, 0.], species=2),
                             Particle(position=[0.0, 1.0, 0.], species=2),], bond=[0, 1])
        s = System(molecule=[Molecule([Particle(position=[1.0, 0.0, 0.], species=1),
                                       Particle(position=[0.0, 0.0, 0.], species=2),
                                       Particle(position=[0.0, 1.0, 0.], species=2)],
                                      bond=[0, 1]) for _ in range(10)],
                   cell=Cell([6.0, 6.0, 6.0]))

        numpy.random.seed(1)
        with MolecularTrajectoryXYZ(finp, 'w') as th:
            for step in range(500):
                for m in s.molecule:
                    theta = 0.5*(numpy.random.random() - 0.5)
                    m.rotate(theta, axis=[0., 0., 1.])
                th.write(s, step)

        with MolecularTrajectoryXYZ(finp) as th:
            cf = RotationalCorrelation(th, custom_orientation=['2-3x2-1'])
            cf.compute()
            self.assertTrue(sum(numpy.array(cf.value) != 1.0) == 0)

    def setUp(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ
        
        self.finp = '/tmp/test_molecular.xyz'
        molecule = Molecule([Particle(position=[1.0, 0.0, 0.], species=1),
                             Particle(position=[0.0, 0.0, 0.], species=2),
                             Particle(position=[0.0, 1.0, 0.], species=2),], bond=[0, 1])
        s = System(molecule=[Molecule([Particle(position=[1.0, 0.0, 0.], species=1),
                                       Particle(position=[0.0, 0.0, 0.], species=2),
                                       Particle(position=[0.0, 1.0, 0.], species=2)],
                                      bond=[0, 1]) for _ in range(10)],
                   cell=Cell([6.0, 6.0, 6.0]))

        numpy.random.seed(1)
        with MolecularTrajectoryXYZ(self.finp, 'w') as th:
            for step in range(500):
                for m in s.molecule:
                    theta = 0.5*(numpy.random.random() - 0.5)
                    m.rotate(theta, axis=[0., 0., 1.])
                th.write(s, step)
            
    def test_orient_angle(self):
        from atooms.trajectory import MolecularTrajectoryXYZ, MolecularTrajectoryLAMMPS
        from atooms.postprocessing import OrientationAngleDistribution
        
        # with MolecularTrajectoryXYZ(self.finp) as th:
        with MolecularTrajectoryLAMMPS('data/trimer.lammpstrj') as th:
            cf = OrientationAngleDistribution(th, orientation=['1-2'], rcut=2.0)
            cf.compute()
            ref_grid = [0.15707963267948966,
                        0.47123889803846897, 0.7853981633974483,
                        1.0995574287564276, 1.413716694115407,
                        1.7278759594743862, 2.0420352248333655,
                        2.356194490192345, 2.670353755551324,
                        2.9845130209103035]
            ref_value = [0.5252016003538106,
                         0.4808688239460224, 0.5037721274957259,
                         0.5038612938353498, 0.4854366654976734,
                         0.4806833076959826, 0.5275724135452484,
                         0.5062619403169567, 0.47182021704381216,
                         0.5176987203487557]
            self.assertTrue(sum(numpy.abs(cf.grid - ref_grid)) < 1e-10)
            self.assertTrue(sum(numpy.abs(cf.value - ref_value)) < 1e-10)
            # import matplotlib.pyplot as plt
            # plt.plot(cf.grid, cf.value, '-o')
            # plt.show()
            
    def test_orient_partial(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ

        # TODO: writing molecule species in trajectories not supported yet
        finp = '/tmp/test_molecular.xyz'
        molecule_A = Molecule([Particle(position=[1.0, 0.0], species=1),
                               Particle(position=[0.0, 0.0], species=1),
                               Particle(position=[0.0, 1.0], species=1),],
                              #species='A',
                              bond=(0, 1))
        molecule_B = Molecule([Particle(position=[1.0, 0.0], species=1),
                               Particle(position=[0.0, 1.0], species=1)],
                              #species='B',
                              bond=(0, 1))
        import copy

        s = System(molecule=[copy.deepcopy(molecule_A) for _ in range(50)] + \
                            [copy.deepcopy(molecule_B) for _ in range(50)],
                   cell=Cell([6.0, 6.0]))
        # delta = {'A': 0.1, 'B': 1.0}
        delta = {'111': 0.2, '11': 0.5}
        numpy.random.seed(1)
        finp_A = '/tmp/test_molecular_A.xyz'
        with MolecularTrajectoryXYZ(finp, 'w') as th, \
             MolecularTrajectoryXYZ(finp_A, 'w') as th_A:
            for step in range(1000):
                th.write(s, step)
                # sA = System(molecule=[m for m in s.molecule if m.species == '111'],
                #             cell=s.cell)
                # th_A.write(sA, step)
                for m in s.molecule:
                    theta = delta[m.species]*(numpy.random.random() - 0.5)
                    m.rotate(theta)

        # Note: here we MUST use partial for C_l, we cannot compute the total
        # correlation of molecules with different number of orientations.
        # However, for e2e it would work, although probably not make sense.
        from atooms.postprocessing import Partial
        with MolecularTrajectoryXYZ(finp) as th:
            # cf = EndToEndCorrelation(th)
            # cf.compute()
            # self.assertAlmostEqual(cf.value[0], 1.0)
            # cf.show()
            cf = Partial(C2Correlation, th)
            cf.compute()
            #print(cf.partial['111'].values)
            self.assertAlmostEqual(cf.partial['111'].value[0], 1.0)

            # cfA = C2Correlation(th_A)
            # cfA.compute()
            # print(cfA.values)
            # self.assertAlmostEqual(cfA.value,
            #                        cf.partial['111'].value)

            # cf.partial['111'].show(now=True)
            #print(cf.partial['11'].values)
            self.assertAlmostEqual(cf.partial['11'].value[0], 1.0)
            # cf.partial['11'].show(now=True)

    def test_molecular_gr(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ, TrajectoryXYZ


        with TrajectoryXYZ('./data/lj.xyz') as th:
            slj = th[0]

        finp = '/tmp/test_molecular.xyz'
        s = System(molecule=[Molecule([Particle(position=[1.0, 0.0, 0.], species=1),
                                       Particle(position=[0.0, 0.0, 0.], species=2),
                                       Particle(position=[0.0, 1.0, 0.], species=2)],
                                      bond=[0, 1]) for _ in range(len(slj.particle))],
                   cell=slj.cell)

        numpy.random.seed(1)
        with MolecularTrajectoryXYZ(finp, 'w') as th:
            for m, p in zip(s.molecule, slj.particle):
                theta = 1.0*(numpy.random.random() - 0.5)
                m.rotate(theta, axis=[0., 0., 1.])
                m.center_of_mass = p.position
            th.write(s, 0)

        from atooms.postprocessing import RadialDistributionFunction
        from atooms.postprocessing.molecular import CenterOfMassRadialDistributionFunction, _CenterOfMass

        with MolecularTrajectoryXYZ(finp) as th, \
             TrajectoryXYZ('./data/lj.xyz') as thlj:
            cf = CenterOfMassRadialDistributionFunction(th)
            cf.compute()
            cfp = RadialDistributionFunction(thlj)
            cfp.compute()
            self.assertTrue(all(cf.values == cfp.values))


    def test_molecular_msd(self):
        import numpy
        from atooms.system import Particle, Molecule, System, Cell
        from atooms.trajectory import MolecularTrajectoryXYZ, TrajectoryXYZ
        from atooms.postprocessing import MeanSquareDisplacement
        from atooms.postprocessing.molecular import CenterOfMassMeanSquareDisplacement
        from atooms.trajectory import Unfolded

        numpy.random.seed(1)
        finp = '/tmp/test_molecular.xyz'
        with Unfolded(TrajectoryXYZ('./data/kalj-small.xyz')) as thlj, \
             MolecularTrajectoryXYZ(finp, 'w') as th:
            for slj, step in zip(thlj, thlj.steps):
                s = System(molecule=[Molecule([Particle(position=[1.0, 0.0, 0.]),
                                               Particle(position=[0.0, 0.0, 0.]),
                                               Particle(position=[0.0, 1.0, 0.])],
                                      bond=[0, 1]) for _ in range(len(slj.particle))],
                           cell=slj.cell)
                for m, p in zip(s.molecule, slj.particle):
                    theta = 1.0*(numpy.random.random() - 0.5)
                    m.rotate(theta, axis=[0., 0., 1.])
                    m.center_of_mass = p.position
                s.fold()
                th.write(s, step)

        with MolecularTrajectoryXYZ(finp) as th, \
             TrajectoryXYZ('./data/kalj-small.xyz') as thlj:
            # for s, sm in zip(Unfolded(thlj), Unfolded(th)):
            #     print(s.particle[0].position,
            #           sm.molecule[0].center_of_mass, 'A')
            # return
            cf = CenterOfMassMeanSquareDisplacement(th)
            cf.compute()
            cfp = MeanSquareDisplacement(thlj)
            cfp.compute()
            # import matplotlib.pyplot as plt
            # plt.plot(cf.values)
            # plt.plot(cfp.values, 'o')
            # plt.show()
            self.assertTrue(all(numpy.abs((numpy.array(cf.values) - numpy.array(cfp.values))) < 1e-6))

    def tearDown(self):
        from atooms.core.utils import rmf
        rmf('/tmp/test_molecular*.xyz')
