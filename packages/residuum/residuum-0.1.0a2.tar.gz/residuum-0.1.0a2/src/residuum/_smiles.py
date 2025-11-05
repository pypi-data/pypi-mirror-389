"""Handling SMILES strings for residues."""

from functools import cache

from rdkit import Chem

from residuum._molecule import add_c_terminus, add_n_terminus


@cache
def to_n_terminal(smiles: str) -> str:
    """Convert SMILES with backbone asterisks to N-terminal form.

    Parameters
    ----------
    smiles
        SMILES string with backbone asterisks

    Returns
    -------
    str
        SMILES string with N-terminal modification (H at N-terminus, * at C-terminus)
    """
    mol = Chem.MolFromSmiles(smiles)
    mol = add_n_terminus(mol)
    return Chem.MolToSmiles(mol)


@cache
def to_c_terminal(smiles: str) -> str:
    """Convert SMILES with backbone asterisks to C-terminal form.

    Parameters
    ----------
    smiles
        SMILES string with backbone asterisks

    Returns
    -------
    str
        SMILES string with C-terminal modification (O at C-terminus, * at N-terminus)
    """
    mol = Chem.MolFromSmiles(smiles)
    mol = add_c_terminus(mol)
    return Chem.MolToSmiles(mol)
