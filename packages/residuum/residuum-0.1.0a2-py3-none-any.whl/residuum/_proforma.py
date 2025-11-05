"""Core functionality for residuum package."""

from typing import Any, Mapping, Protocol, Sequence, cast

from pyteomics.proforma import ProForma, TagBase

from residuum.exceptions import UnsupportedProFormaError
from residuum._psimod import PsiModResolver
from residuum._smiles import to_c_terminal, to_n_terminal

TERMINAL_CONSTANTS: dict[str, dict[str, int | str]] = {
    "n_term": {
        "index": 0,
        "term_spec": "N-term",
    },
    "c_term": {
        "index": -1,
        "term_spec": "C-term",
    },
}


class Peptidoform(Protocol):
    """
    Protocol for Peptidoform-like objects.

    Any object with these attributes can be used as input to proforma_to_smiles.
    This allows duck-typing without requiring pyteomics.proforma.ProForma specifically.

    Attributes
    ----------
    sequence
        Sequence of (amino_acid, modifications) tuples
    properties
        Dictionary of properties including 'n_term', 'c_term', etc.
    """

    sequence: Sequence[tuple[str, list[TagBase] | None]]
    properties: Mapping[str, Any]


def proforma_to_smiles(
    peptidoform: ProForma | Peptidoform | str,
    case_sensitive: bool = False,
    take_first: bool = False,
    fallback: bool = False,
    psimod_lookup: PsiModResolver | None = None,
) -> list[str]:
    """
    Convert peptidoform to list of SMILES strings.

    Parameters
    ----------
    peptidoform
        Peptidoform as ProForma object, Peptidoform-like object, or string
    case_sensitive
        Whether to perform case-sensitive search for modification names
    take_first
        When multiple matches found: If True, return first match, if False, raise ValueError
    fallback
        Whether to fallback to unmodified residue SMILES if modification cannot be resolved
    psimod_lookup
        Optional PsiModResolver instance to use for resolving modifications; if None, a new instance
        will be created.

    Returns
    -------
    list[str]
        List of SMILES strings for each residue in the peptidoform

    Raises
    ------
    UnsupportedProFormaError
        If unsupported ProForma features are used.

    Examples
    --------
    >>> smiles_list = proforma_to_smiles("PEPT[Phospho]IDE")
    >>> for smiles in smiles_list:
    ...     print(smiles)
    ['*C(=O)[C@@H]1CCCN1',
    'OC(=O)CC[C@H](N-*)C(-*)=O',
    '*-N1CCC[C@H]1C(-*)=O',
    '*N[C@H](C(*)=O)[C@@H](C)OP(=O)(O)O',
    'CC[C@H](C)[C@H](N-*)C(-*)=O',
    'OC(=O)C[C@H](N-*)C(-*)=O',
    '*N[C@@H](CCC(=O)O)C(=O)O']

    """
    # Parse and validate input
    parsed = _parse_and_validate_proforma(peptidoform)

    # Handle empty peptide
    if not parsed.sequence:
        return []

    # Initialize PSI-MOD resolver
    psimod = psimod_lookup or PsiModResolver()

    # Process terminal modifications
    n_term_smiles = _process_terminal_modification(
        parsed, "n_term", psimod, case_sensitive, take_first, fallback
    )
    c_term_smiles = _process_terminal_modification(
        parsed, "c_term", psimod, case_sensitive, take_first, fallback
    )

    # Process sequence residues
    smiles_list: list[str] = _process_sequence(
        parsed.sequence, psimod, case_sensitive, take_first, fallback
    )

    # Apply N-terminal modification or cap
    if n_term_smiles is not None:
        smiles_list[0] = n_term_smiles
    else:
        smiles_list[0] = to_n_terminal(smiles_list[0])

    # Apply C-terminal modification or cap
    if c_term_smiles is not None:
        smiles_list[-1] = c_term_smiles
    else:
        smiles_list[-1] = to_c_terminal(smiles_list[-1])

    return smiles_list


def _parse_and_validate_proforma(input_peptidoform: str | ProForma | Peptidoform) -> ProForma:
    """Parse and validate that ProForma features are supported."""
    if isinstance(input_peptidoform, str):
        parsed_peptidoform = ProForma.parse(input_peptidoform)
    elif isinstance(input_peptidoform, ProForma):
        parsed_peptidoform = input_peptidoform
    elif hasattr(input_peptidoform, "sequence") and hasattr(input_peptidoform, "properties"):
        parsed_peptidoform = ProForma(input_peptidoform.sequence, input_peptidoform.properties)
    else:
        raise TypeError("Input must be a ProForma object, Peptidoform-like object, or string.")

    # Check for unsupported features using properties dict (safe for custom objects)
    if (
        parsed_peptidoform.properties.get("fixed_modifications")
        or parsed_peptidoform.properties.get("isotopes")
        or parsed_peptidoform.properties.get("labile_modifications")
        or parsed_peptidoform.properties.get("unlocalized_modifications")
    ):
        raise UnsupportedProFormaError(
            "Fixed, isotopic, labile, and unlocalized modifications are not supported."
        )

    return parsed_peptidoform


def _process_terminal_modification(
    parsed_peptidoform: ProForma,
    terminus: str,
    psimod: PsiModResolver,
    case_sensitive: bool,
    take_first: bool,
    fallback: bool,
) -> str | None:
    """Process terminal modification and return SMILES."""
    if not parsed_peptidoform.properties.get(terminus):
        return None

    term_spec: str = cast(str, TERMINAL_CONSTANTS[terminus]["term_spec"])
    index: int = cast(int, TERMINAL_CONSTANTS[terminus]["index"])

    term_mods: list[TagBase] = parsed_peptidoform.properties[terminus]
    if len(term_mods) > 1:
        raise UnsupportedProFormaError(f"Multiple {term_spec} modifications not supported.")

    aa, side_chain_tags = parsed_peptidoform.sequence[index]
    if side_chain_tags:
        raise UnsupportedProFormaError(
            f"{term_spec} modification on side-chain modified residue not supported."
        )

    smiles = psimod.resolve_smiles(
        str(term_mods[0]),
        residue=aa,
        term_spec=term_spec,  # type: ignore
        case_sensitive=case_sensitive,
        take_first=take_first,
        fallback=fallback,
    )
    return smiles


def _process_sequence(
    sequence: list[tuple[str, list[TagBase] | None]],
    psimod: PsiModResolver,
    case_sensitive: bool,
    take_first: bool,
    fallback: bool,
) -> list[str]:
    """Resolve SMILES for the sequential positions in the peptidoform."""
    smiles_list: list[str] = []
    for aa, mods in sequence:
        # If no modifications, immediately add residue SMILES
        if not mods:
            try:
                smiles_list.append(psimod.natural_residue_smiles[aa])
            except KeyError:
                raise KeyError(f"Amino acid '{aa}' not found in natural residues")

        # If multiple modifications, raise error
        elif len(mods) > 1:
            raise UnsupportedProFormaError("Multiple modifications per residue not supported.")

        # Else, resolve modified residue SMILES
        else:
            smiles_list.append(
                psimod.resolve_smiles(
                    str(mods[0]),
                    residue=aa,
                    term_spec="none",
                    case_sensitive=case_sensitive,
                    take_first=take_first,
                    fallback=fallback,
                )
            )

    return smiles_list
