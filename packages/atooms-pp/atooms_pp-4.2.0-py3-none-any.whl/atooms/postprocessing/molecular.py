import copy
from atooms.postprocessing import RadialDistributionFunction, StructureFactor, \
    SpectralDensity, SelfIntermediateScattering, IntermediateScattering, \
    BondAngleDistribution, MeanSquareDisplacement, NonGaussianParameter, \
    CollectiveOverlap, SelfOverlap, S4ktOverlap, Chi4SelfOverlap, \
    SelfVanHoveDistribution


def _CenterOfMass(cls):    

    class CenterOfMass(cls):
        variables = copy.copy(_variables)
        symbol = cls.symbol + '_cm'
        short_name = cls.short_name[0] + '_cm' + cls.short_name[1:]
        long_name = cls.long_name + 'of CM'

    CenterOfMass.__name__ += cls.__name__
    return CenterOfMass

_variables = [('pos', 'molecule.center_of_mass')]
CenterOfMassRadialDistributionFunction = _CenterOfMass(RadialDistributionFunction)
CenterOfMassStructureFactor = _CenterOfMass(StructureFactor)
CenterOfMassBondAngleDistribution = _CenterOfMass(BondAngleDistribution)
CenterOfMassSpectralDensity = _CenterOfMass(SpectralDensity)
CenterOfMassSelfIntermediateScattering = _CenterOfMass(SelfIntermediateScattering)
CenterOfMassIntermediateScattering = _CenterOfMass(IntermediateScattering)
CenterOfMassCollectiveOverlap = _CenterOfMass(CollectiveOverlap)

_variables = [('pos_unf', 'molecule.center_of_mass_unfolded')]
CenterOfMassMeanSquareDisplacement = _CenterOfMass(MeanSquareDisplacement)
CenterOfMassSelfVanHoveDistribution = _CenterOfMass(SelfVanHoveDistribution)
CenterOfMassNonGaussianParameter = _CenterOfMass(NonGaussianParameter)
CenterOfMassSelfOverlap = _CenterOfMass(SelfOverlap)
CenterOfMassS4ktOverlap = _CenterOfMass(S4ktOverlap)
CenterOfMassChi4SelfOverlap = _CenterOfMass(Chi4SelfOverlap)

