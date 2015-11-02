import numpy as np
import ase
import pyscf_ase
import pyscf.pbc.gto as pbcgto
import pyscf.pbc.dft as pbcdft

import ase.lattice
from ase.lattice.cubic import Diamond
from ase.units import kJ
from ase.utils.eos import EquationOfState

def test_pyscf():
    """
    Take ASE Diamond structure, input into PySCF and run
    """
    ase_atom=Diamond(symbol='C', latticeconstant=3.5668)
    print ase_atom.get_volume()

    cell = pbcgto.Cell()
    cell.atom=pyscf_ase.ase_atoms_to_pyscf(ase_atom)
    cell.h=ase_atom.cell
    cell.basis = 'gth-szv'
    cell.pseudo = 'gth-pade'
    #cell.gs=np.array([10,10,10])
    cell.gs=np.array([20,20,20])
    cell.verbose=7

    cell.build(None,None)
    print cell._atom

    print "Cell nimgs =", cell.nimgs
    print "Cell _basis =", cell._basis
    print "Cell _pseudo =", cell._pseudo
    print "Cell nelectron =", cell.nelectron

    mf=pbcdft.RKS(cell)
    mf.xc='lda,vwn'
    mf.analytic_int=False
    print mf.scf() # [10,10,10]: -44.8811199336
                   # [20,20,20]: -44.8804853049
    
def test_calculator():
    """
    Take ASE structure, PySCF object,
    and run through ASE calculator interface. 
    
    This allows other ASE methods to be used with PySCF;
    here we try to compute an equation of state.
    """
    ase_atom=Diamond(symbol='C', latticeconstant=3.5668)

    # Set up a cell; everything except atom; the ASE calculator will
    # set the atom variable
    cell = pbcgto.Cell()
    cell.h=ase_atom.cell
    cell.basis = 'gth-szv'
    cell.pseudo = 'gth-pade'
    cell.gs=np.array([8,8,8])
    cell.verbose = 0

    # Set up the kind of calculation to be done
    # Additional variables for mf_class are passed through mf_dict
    mf_class=pbcdft.RKS
    mf_dict = { 'xc' : 'lda,vwn' }

    # Once this is setup, ASE is used for everything from this point on
    ase_atom.set_calculator(pyscf_ase.PySCF(molcell=cell, mf_class=mf_class, mf_dict=mf_dict))

    print "ASE energy", ase_atom.get_potential_energy()
    print "ASE energy (should avoid re-evaluation)", ase_atom.get_potential_energy()
    # Compute equation of state
    ase_cell=ase_atom.cell
    volumes = []
    energies = []
    for x in np.linspace(0.95, 1.2, 5):
        ase_atom.set_cell(ase_cell * x, scale_atoms = True)
        print "[x: %f, E: %f]" % (x, ase_atom.get_potential_energy())
        volumes.append(ase_atom.get_volume())
        energies.append(ase_atom.get_potential_energy())

    eos = EquationOfState(volumes, energies)
    v0, e0, B = eos.fit()
    print(B / kJ * 1.0e24, 'GPa')
    eos.plot('eos.png')
