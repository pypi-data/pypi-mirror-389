import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import tblite.interface as tb

ANGSTROM_TO_BOHR = 1.88972612456506
HARTREE_TO_KCAL = 627.509


def get_boltzmann_weighted_average(*, properties: np.ndarray, energies: np.ndarray, T: float = 298):
    """ Some simple Python code to calculate Boltzmann weights from energies in kcal/mol """

    assert len(properties)==len(energies)

    if len(properties)==1:
        return properties[0], np.ones(1)

    energies = energies - np.min(energies)

    R = 3.1668105e-6 # eH/K
    weights = np.exp(-1*energies/(627.509*R*T))
    weights = weights / np.sum(weights)


    return np.average(properties, weights=weights), weights

def embed(mol: Chem.Mol, /, *, num_confs: int = 100, rmsd_threshold: float | None = 0.25) -> Chem.Mol:
    """Embed `nconf` ETKDGv3 conformers and MMFF94‑optimise them in place."""
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xC0FFEE
    if rmsd_threshold:
        params.pruneRmsThresh = rmsd_threshold
    params.numThreads = 0  # use all cores for embedding
    AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=params)

    props = AllChem.MMFFGetMoleculeProperties(mol, mmffVariant="MMFF94")
    for cid in range(mol.GetNumConformers()):
        ff = AllChem.MMFFGetMoleculeForceField(mol, props, confId=cid)
        if ff:
            ff.Minimize(maxIts=10000)
    return mol



def optimize_geometry(*, calc: tb.Calculator, positions: np.ndarray, max_steps: int=100, force_tol: float=1e-3):
    """
    Simple geometry optimization using steepest descent.
    
    Parameters:
    - calc: tblite Calculator object
    - positions: Initial positions in Bohr
    - max_steps: Maximum optimization steps
    - force_tol: Convergence threshold (Hartree/Bohr)
    
    Returns:
    - optimized_positions: Final geometry in Bohr
    - final_energy: Final energy in Hartree
    """
    pos = positions.copy()
    
    for step in range(max_steps):
        # Update calculator with current positions
        calc.update(pos)
        
        # Get energy and gradient
        res = calc.singlepoint()
        energy = res.get("energy")
        gradient = res.get("gradient")  # dE/dx in Hartree/Bohr
        
        # Force is negative gradient
        forces = -gradient
        max_force = np.max(np.abs(forces))
        
        # Check convergence
        if max_force < force_tol:
            break
        
        # Simple steepest descent step
        step_size = 0.01  # Bohr
        pos += step_size * forces
    
    return pos, energy

def get_xtb_solvation(mol: Chem.Mol, charge: int = 0) -> tuple[float, float]:
    """
    Run GFN2-xTB optimisation in ALPB water and return total energy and solvation energy (kcal/mol).
    Uses tblite Python interface instead of subprocess calls.
    
    Parameters:
    - mol: RDKit molecule object
    - charge: Molecular charge (default 0)
    - num_cores: Number of cores (not used in tblite interface, kept for API compatibility)
    
    Returns:
    - total_energy: Total energy in kcal/mol
    - solvation_energy: Solvation energy in kcal/mol
    """
    # Extract atomic numbers and positions
    numbers = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()])
    positions = mol.GetConformer().GetPositions() * ANGSTROM_TO_BOHR  # Convert Å to Bohr
    
    # Gas phase optimization
    calc_gas = tb.Calculator("GFN2-xTB", numbers, positions, charge=charge)
    calc_gas.set("verbosity", 0)
    opt_pos, E_gas = optimize_geometry(calc=calc_gas, positions=positions, max_steps=3)
    
    # Solvated phase calculation (single point on optimized geometry)
    calc_solv = tb.Calculator("GFN2-xTB", numbers, opt_pos, charge=charge)
    calc_solv.set("verbosity", 0)
    calc_solv.add("alpb-solvation", "water")
    E_solv = calc_solv.singlepoint().get("energy")
    
    # Calculate energies in kcal/mol
    total_energy = E_solv * HARTREE_TO_KCAL
    solvation_energy = (E_solv - E_gas) * HARTREE_TO_KCAL
    
    return total_energy, solvation_energy
    

def get_solvation_energy(mol: Chem.Mol, /, *, num_rdkit_confs: int = 50, rmsd_threshold: float | None = 0.25) -> float:
    mol = embed(Chem.AddHs(mol), num_confs=num_rdkit_confs, rmsd_threshold=rmsd_threshold)

    solvation_energies = []
    total_energies = []
    for conf in mol.GetConformers():
        _mol = Chem.Mol(mol)
        _mol.RemoveAllConformers()
        _mol.AddConformer(Chem.Conformer(conf), assignId=True)
        total_energy, solvation_energy = get_xtb_solvation(_mol)
        total_energies.append(total_energy)
        solvation_energies.append(solvation_energy)

    solvation_energies = np.array(solvation_energies)
    total_energies = np.array(total_energies)

    solvation_energy, _ = get_boltzmann_weighted_average(properties=solvation_energies, energies=total_energies)

    return solvation_energy



