"""Molecular structure operations for residues."""

import logging
from typing import Literal

from rdkit import Chem

LOGGER = logging.getLogger(__name__)

# SMARTS patterns for structural validation
RESIDUE_BACKBONE_PATTERN = Chem.MolFromSmarts("[#0]-[NX3]-[CX4H,CX4H2]-[CX3](=[OX1])-[#0]")
AMINO_ACID_BACKBONE_PATTERN = Chem.MolFromSmarts("[NX3][C@H](C)C(=O)O")
N_TERM_PATTERN = Chem.MolFromSmarts("[#0]-[NX3]-[CX4H,CX4H2]-[CX3](=[OX1])")
C_TERM_PATTERN = Chem.MolFromSmarts("[NX3]-[CX4H,CX4H2]-[CX3](=[OX1])-[#0]")

TermSpec = Literal["N-term", "C-term", "none"]


def is_amino_acid(mol: Chem.Mol) -> bool:
    """Check if the molecule represents a complete amino acid structure."""
    return mol.HasSubstructMatch(AMINO_ACID_BACKBONE_PATTERN)


def has_free_backbone(mol: Chem.Mol) -> bool:
    """Check if molecule has complete amino acid backbone with both termini free (marked with dummy atoms)."""
    return mol.HasSubstructMatch(RESIDUE_BACKBONE_PATTERN)


def has_free_n_terminus(mol: Chem.Mol) -> bool:
    """Check if molecule has free N-terminus (marked with dummy atom)."""
    return mol.HasSubstructMatch(N_TERM_PATTERN)


def has_free_c_terminus(mol: Chem.Mol) -> bool:
    """Check if molecule has free C-terminus (marked with dummy atom)."""
    return mol.HasSubstructMatch(C_TERM_PATTERN)


def is_valid_residue(mol: Chem.Mol, term_spec: TermSpec) -> bool:
    """
    Check if the molecule represents a valid residue structure, given the term_spec type.

    Validates that the residue has appropriate backbone termini based on term_spec type:
    - none: both termini free (marked with dummy atoms)
    - N-term: C-terminus free
    - C-term: N-terminus free

    Returns
    -------
    bool
        True if structure is valid for the term_spec type

    Examples
    --------
    >>> residue = Residue(
    ...     name="Phosphoserine", residue="S", term_spec="none",
    ...     smiles="*NC(COP(O)(O)=O)C(*)=O", ...)
    >>> residue.smiles_is_amino_acid()
    True

    """
    if term_spec == "none":
        return has_free_backbone(mol)
    else:
        has_full_backbone = has_free_backbone(mol)

        if has_full_backbone:
            raise ValueError(
                f"Terminal residue ({term_spec}) has both "
                "backbone asterisks - should have one terminal replaced"
            )

        if term_spec == "N-term":
            return has_free_c_terminus(mol)
        elif term_spec == "C-term":
            return has_free_n_terminus(mol)
        else:
            raise ValueError(f"Invalid term_spec value: {term_spec}")


def contains_residue(mol: Chem.Mol, residue: str) -> bool:
    """
    Check if an unmodified residue is contained within the structure of the (modified) residue.

    Parameters
    ----------
    mol
        Input molecule to check
    residue
        One-letter code of the amino acid residue to check for

    Returns
    -------
    bool
        True if the residue structure is contained within the molecule

    Notes
    -----
    This will not be true for residues where parts are removed, even if they have a correct SMILES
    string.

    """
    return mol.HasSubstructMatch(Chem.MolFromSequence(residue))


def add_n_terminus(mol: Chem.Mol) -> Chem.Mol:
    """
    Replace N-terminal asterisk with hydrogen.

    For molecules with full backbone (both asterisks), uses SMARTS pattern matching.
    For molecules with partial backbone (one asterisk), searches for the remaining dummy.

    Parameters
    ----------
    mol
        Input molecule with N-terminal dummy atom marking backbone connection

    Returns
    -------
    Chem.Mol
        Modified molecule with N-terminal hydrogen added

    Raises
    ------
    ValueError
        If molecule doesn't contain N-terminal dummy atom
    """
    # Determine which preparation function to use
    has_full = has_free_backbone(mol)
    has_partial = has_free_n_terminus(mol)

    if has_full:
        return _add_terminus_full_backbone(mol, "N-term")
    elif has_partial:
        return _add_terminus_partial_backbone(mol, "N-term")

    raise ValueError("Molecule does not contain free N-terminus")


def add_c_terminus(mol: Chem.Mol) -> Chem.Mol:
    """
    Replace C-terminal asterisk with hydroxyl group (OH).

    For molecules with full backbone (both asterisks), uses SMARTS pattern matching.
    For molecules with partial backbone (one asterisk), searches for the remaining dummy.

    Parameters
    ----------
    mol
        Input molecule with C-terminal dummy atom marking backbone connection

    Returns
    -------
    Chem.Mol
        Modified molecule with C-terminal hydroxyl group added

    Raises
    ------
    ValueError
        If molecule doesn't contain C-terminal dummy atom
    """
    # Determine which preparation function to use
    has_full = has_free_backbone(mol)
    has_partial = has_free_c_terminus(mol)

    if has_full:
        return _add_terminus_full_backbone(mol, "C-term")
    elif has_partial:
        return _add_terminus_partial_backbone(mol, "C-term")

    raise ValueError("Molecule does not contain free C-terminus")


def to_amino_acid(mol: Chem.Mol) -> Chem.Mol:
    """
    Convert molecule to complete amino acid by replacing both terminal asterisks.

    Parameters
    ----------
    mol
        Input molecule with one or two dummy atoms

    Returns
    -------
    Chem.Mol
        Complete amino acid molecule with both terminals replaced

    Raises
    ------
    ValueError
        If molecule doesn't have the required backbone structure

    Examples
    --------
    >>> from rdkit import Chem
    >>> mol = Chem.MolFromSmiles("*NC(C)C(*)=O")  # Alanine with asterisks
    >>> complete = to_amino_acid(mol)
    >>> Chem.MolToSmiles(complete)
    'CC(N)C(=O)O'
    """
    if has_free_backbone(mol):
        # Full backbone: add both terminals
        intermediate = add_n_terminus(mol)
        return add_c_terminus(intermediate)

    # Partial backbone: add the remaining terminal
    if has_free_n_terminus(mol):
        return add_n_terminus(mol)
    if has_free_c_terminus(mol):
        return add_c_terminus(mol)

    # Already complete amino acid
    return mol


def _add_terminus_full_backbone(mol: Chem.Mol, terminus: str) -> Chem.Mol:
    """
    Add terminal group for molecule with full amino acid backbone.

    Uses SMARTS pattern matching to find exact atom positions.
    """
    matches = mol.GetSubstructMatches(RESIDUE_BACKBONE_PATTERN)
    if not matches:
        raise ValueError("Molecule does not contain amino acid backbone structure (*-N-C-C(=O)-*)")

    # Get backbone atom indices from first match
    # Pattern: [#0]-[NX3]-[CX4]-[CX3](=[OX1])-[#0]
    # Indices:  0     1     2     3     4     5
    n_term_dummy_idx, n_idx, c_alpha_idx, c_term_carbon_idx, o_idx, c_term_dummy_idx = matches[0]

    # Create editable molecule copy
    editable_mol = Chem.RWMol(mol)

    if terminus == "N-term":
        # Remove N-terminal dummy atom (RDKit adds implicit H)
        editable_mol.RemoveAtom(n_term_dummy_idx)

    elif terminus == "C-term":
        # Add OH group first, then remove dummy
        o_idx = editable_mol.AddAtom(Chem.Atom("O"))
        editable_mol.AddBond(c_term_carbon_idx, o_idx, Chem.BondType.SINGLE)
        editable_mol.RemoveAtom(c_term_dummy_idx)

    # Sanitize and return
    new_mol = editable_mol.GetMol()
    Chem.SanitizeMol(new_mol)
    return new_mol


def _add_terminus_partial_backbone(mol: Chem.Mol, terminus: str) -> Chem.Mol:
    """
    Add terminal group for molecule that already has one terminal replaced.

    Searches for the remaining dummy atom by iterating through atoms.
    """
    editable_mol = Chem.RWMol(mol)

    # Find the dummy atom and its neighbor
    dummy_idx: int | None = None
    target_atom_idx: int | None = None

    for atom in editable_mol.GetAtoms():
        if atom.GetSymbol() != "*" or len(atom.GetNeighbors()) != 1:
            continue

        neighbor = atom.GetNeighbors()[0]

        if terminus == "N-term" and neighbor.GetSymbol() == "N":
            dummy_idx = atom.GetIdx()
            break
        elif terminus == "C-term" and neighbor.GetSymbol() == "C":
            # Check if this is the carbonyl carbon
            is_carbonyl = any(
                bond.GetBondType() == Chem.BondType.DOUBLE
                and bond.GetOtherAtom(neighbor).GetSymbol() == "O"
                for bond in neighbor.GetBonds()
            )
            if is_carbonyl:
                dummy_idx = atom.GetIdx()
                target_atom_idx = neighbor.GetIdx()
                break

    if dummy_idx is None:
        raise ValueError(f"Could not find {terminus} dummy atom in molecule")

    # Apply modifications
    if terminus == "C-term":
        if target_atom_idx is None:
            raise ValueError("Could not find C-terminal carbonyl carbon")
        # Add OH group before removing dummy (hydrogen is implicit)
        o_idx = editable_mol.AddAtom(Chem.Atom("O"))
        editable_mol.AddBond(target_atom_idx, o_idx, Chem.BondType.SINGLE)

    # Remove dummy atom
    editable_mol.RemoveAtom(dummy_idx)

    # Sanitize and return
    new_mol = editable_mol.GetMol()
    Chem.SanitizeMol(new_mol)
    return new_mol
