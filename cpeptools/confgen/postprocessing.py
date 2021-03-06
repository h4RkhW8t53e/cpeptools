from ..utils import get_data_filename
#TODO add need off omm parmed decorator: https://stackoverflow.com/questions/739654/how-to-make-a-chain-of-function-decorators
def minimise_energy_all_confs(mol, models = None, epsilon = 4, allow_undefined_stereo = True, **kwargs ):
    from simtk import unit
    from simtk.openmm import LangevinIntegrator
    from simtk.openmm.app import Simulation, HBonds, NoCutoff
    from rdkit import Chem
    from rdkit.Geometry import Point3D
    import mlddec
    import copy
    import tqdm
    mol = Chem.AddHs(mol, addCoords = True)

    if models is None:
        models  = mlddec.load_models(epsilon)
    charges = mlddec.get_charges(mol, models)

    from openforcefield.utils.toolkits import RDKitToolkitWrapper, ToolkitRegistry
    from openforcefield.topology import Molecule, Topology
    from openforcefield.typing.engines.smirnoff import ForceField
    # from openforcefield.typing.engines.smirnoff.forcefield import PME

    import parmed
    import numpy as np

    forcefield = ForceField(get_data_filename("modified_smirnoff99Frosst.offxml")) #FIXME better way of identifying file location

    tmp = copy.deepcopy(mol)
    tmp.RemoveAllConformers() #XXX workround for speed beacuse seemingly openforcefield records all conformer informations, which takes a long time. but I think this is a ill-practice

    molecule = Molecule.from_rdkit(tmp, allow_undefined_stereo = allow_undefined_stereo)
    molecule.partial_charges = unit.Quantity(np.array(charges), unit.elementary_charge)
    topology = Topology.from_molecules(molecule)
    openmm_system = forcefield.create_openmm_system(topology, charge_from_molecules= [molecule])

    structure = parmed.openmm.topsystem.load_topology(topology.to_openmm(), openmm_system)


    system = structure.createSystem(nonbondedMethod=NoCutoff, nonbondedCutoff=1*unit.nanometer, constraints=HBonds)

    integrator = LangevinIntegrator(273*unit.kelvin, 1/unit.picosecond, 0.002*unit.picoseconds)
    simulation = Simulation(structure.topology, system, integrator)

    out_mol = copy.deepcopy(mol)
    for i in tqdm.tqdm(range(out_mol.GetNumConformers())):
        conf = mol.GetConformer(i)
        structure.coordinates =  unit.Quantity(np.array([np.array(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]), unit.angstroms)

        simulation.context.setPositions(structure.positions)

        simulation.minimizeEnergy()
        # simulation.step(1)

        coords = simulation.context.getState(getPositions = True).getPositions(asNumpy = True).value_in_unit(unit.angstrom)
        conf = out_mol.GetConformer(i)
        for j in range(out_mol.GetNumAtoms()):
            conf.SetAtomPosition(j, Point3D(*coords[j]))

    return out_mol

# def parameterise_molecule(mol, which_conf = -1, models = None, epsilon = 4, allow_undefined_stereo = True, **kwargs):
#     """
#     which_conf : when -1 write out multiple parmed structures, one for each conformer
#     """
#     from rdkit import Chem
#     import mlddec
#     mol = Chem.AddHs(mol, addCoords = True)
#
#     if models is None:
#         models  = mlddec.load_models(epsilon)
#     charges = mlddec.get_charges(mol, models)
#
#
#     from openforcefield.utils.toolkits import RDKitToolkitWrapper, ToolkitRegistry
#     from openforcefield.topology import Molecule, Topology
#     from openforcefield.typing.engines.smirnoff import ForceField
#     # from openforcefield.typing.engines.smirnoff.forcefield import PME
#
#     import parmed
#     import numpy as np
#
#     forcefield = ForceField('test_forcefields/smirnoff99Frosst.offxml')
#
#     # molecule = Molecule.from_rdkit(mol, allow_undefined_stereo = True)
#     molecule = Molecule.from_rdkit(mol, allow_undefined_stereo = allow_undefined_stereo)
#     molecule.partial_charges = Quantity(np.array(charges), elementary_charge)
#     topology = Topology.from_molecules(molecule)
#     openmm_system = forcefield.create_openmm_system(topology, charge_from_molecules= [molecule])
#
#
#     if which_conf == -1 : #TODO better design here
#         for i in range(mol.GetNumConformers()):
#             conf = mol.GetConformer(which_conf)
#             positions = Quantity(np.array([np.array(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]), angstroms)
#             structure = parmed.openmm.topsystem.load_topology(topology.to_openmm(), openmm_system, positions)
#             yield structure
#
#     else:
#         conf = mol.GetConformer(which_conf)
#         positions = Quantity(np.array([np.array(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]), angstroms)
#
#         structure = parmed.openmm.topsystem.load_topology(topology.to_openmm(), openmm_system, positions)
#         yield structure
#
# def parameterise_molecule_am1bcc(mol, which_conf = 0, allow_undefined_stereo = True, **kwargs):
#     from rdkit import Chem
#     mol = Chem.AddHs(mol, addCoords = True)
#
#     from openforcefield.topology import Molecule, Topology
#     from openforcefield.typing.engines.smirnoff import ForceField
#     # from openforcefield.typing.engines.smirnoff.forcefield import PME
#     from openforcefield.utils.toolkits import AmberToolsToolkitWrapper
#
#     import parmed
#     import numpy as np
#
#     forcefield = ForceField('test_forcefields/smirnoff99Frosst.offxml')
#
#     # molecule = Molecule.from_rdkit(mol, allow_undefined_stereo = True)
#     molecule = Molecule.from_rdkit(mol, allow_undefined_stereo = allow_undefined_stereo)
#
#     molecule.compute_partial_charges_am1bcc(toolkit_registry = AmberToolsToolkitWrapper())
#
#     topology = Topology.from_molecules(molecule)
#     openmm_system = forcefield.create_openmm_system(topology, charge_from_molecules= [molecule])
#
#
#     conf = mol.GetConformer(which_conf)
#     positions = Quantity(np.array([np.array(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]), angstroms)
#
#     structure = parmed.openmm.topsystem.load_topology(topology.to_openmm(), openmm_system, positions)
#     return structure
#
#
# def minimise_energy(structure, output_name, **kwargs):
#     # structure = parameterise_molecule_am1bcc(mol, **kwargs)
#
#     system = structure.createSystem(nonbondedMethod=NoCutoff, nonbondedCutoff=1*nanometer, constraints=HBonds)
#
#     integrator = LangevinIntegrator(273*kelvin, 1/picosecond, 0.002*picoseconds)
#     simulation = Simulation(structure.topology, system, integrator)
#     simulation.context.setPositions(structure.positions)
#
#     simulation.minimizeEnergy()
#
#     simulation.reporters.append(PDBReporter(output_name, 1))
#     simulation.step(1)
#     return simulation
#
# def simulate_vacuum(structure, output_name, num_frames = 10):
#     """
#         writes out every 10 ps
#     """
#     # structure = parameterise_molecule(mol)
#
#     system = structure.createSystem(nonbondedMethod=NoCutoff, nonbondedCutoff=1*nanometer, constraints=HBonds)
#
#     integrator = LangevinIntegrator(1*kelvin, 1/picosecond, 0.002*picoseconds)
#     simulation = Simulation(structure.topology, system, integrator)
#     simulation.context.setPositions(structure.positions)
#
#
#     simulation.minimizeEnergy(maxIterations = 50)
#
#     step = 5000
#     # step = 5
#     simulation.reporters.append(PDBReporter(output_name, step))
#     simulation.step(step * num_frames)
