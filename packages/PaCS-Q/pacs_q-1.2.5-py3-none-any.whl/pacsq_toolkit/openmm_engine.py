from openmm.app import *
from openmm import *
from openmm.unit import *
from sys import stdout
from parmed.openmm.reporters import NetCDFReporter




def openmm_run(crd, top, i, j, opt=False):
    inpcrd = AmberInpcrdFile(f"../../../{crd}")
    prmtop = AmberPrmtopFile(f"../../../{top}", periodicBoxVectors=inpcrd.boxVectors)

    system = prmtop.createSystem(nonbondedMethod=PME,
                                 nonbondedCutoff=1 * nanometer,
                                 constraints=HBonds)

    barostat = MonteCarloBarostat(1.0 * bar, 300 * kelvin, 25)
    system.addForce(barostat)

    integrator = LangevinMiddleIntegrator(300 * kelvin, 1 / picosecond, 0.002 * picoseconds)

    simulation = Simulation(prmtop.topology, system, integrator)

    simulation.context.setPositions(inpcrd.positions)
    if inpcrd.boxVectors is not None:
        simulation.context.setPeriodicBoxVectors(*inpcrd.boxVectors)

    simulation.context.setVelocitiesToTemperature(300 * kelvin)

    if opt == True:
        simulation.minimizeEnergy()

    # dcd save
    # simulation.reporters.append(DCDReporter(f'./md{i}_{j}.dcd', 1000))

    simulation.reporters.append(
        NetCDFReporter(f'./md{i}_{j}.nc', reportInterval=500, crds=True, vels=False, frcs=False)
    )

    simulation.reporters.append(StateDataReporter(
        'md.log', 500, step=True, potentialEnergy=True, temperature=True, density=True
    ))

    simulation.step(50000)



def openmm_run_cyc(crd, top, i, j, location, foldername, ref, opt=False):
    inpcrd = AmberInpcrdFile(f'{location}/{foldername}/{i - 1}/{ref}/min.rst')
    prmtop = AmberPrmtopFile(f"../../../{top}", periodicBoxVectors=inpcrd.boxVectors)
    system = prmtop.createSystem(nonbondedMethod=PME, nonbondedCutoff=1 * nanometer,
                                 constraints=HBonds)

    barostat = MonteCarloBarostat(1.0 * bar, 300 * kelvin, 25)
    system.addForce(barostat)

    integrator = LangevinMiddleIntegrator(300 * kelvin, 1 / picosecond, 0.002 * picoseconds)

    simulation = Simulation(prmtop.topology, system, integrator)

    simulation.context.setPositions(inpcrd.positions)
    if inpcrd.boxVectors is not None:
        simulation.context.setPeriodicBoxVectors(*inpcrd.boxVectors)

    simulation.context.setVelocitiesToTemperature(300 * kelvin)

    if opt == True:
        simulation.minimizeEnergy()

    # dcd save
    # simulation.reporters.append(DCDReporter(f'./md{i}_{j}.dcd', 1000))

    simulation.reporters.append(
        NetCDFReporter(f'./md{i}_{j}.nc', reportInterval=500, crds=True, vels=False, frcs=False)
    )

    simulation.reporters.append(StateDataReporter(
        'md.log', 500, step=True, potentialEnergy=True, temperature=True, density=True
    ))

    simulation.step(50000)
