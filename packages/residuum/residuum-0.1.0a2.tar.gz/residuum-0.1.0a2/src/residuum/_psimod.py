"""Resolve SMILES from PSI-MOD ontology."""

from functools import cache
from os import PathLike
from typing import Literal

from pronto.ontology import Ontology
from pronto.term import Term

from residuum.exceptions import (
    MultipleResiduesMatchedError,
    ResidueNotFoundError,
    SMILESNotFoundError,
)

DOWNLOAD_URL = "https://raw.githubusercontent.com/HUPO-PSI/psi-mod-CV/refs/heads/proposal-structural-info/PSI-MOD.obo"


class PsiModResolver:
    """Interface for querying SMILES from the PSI-MOD ontology."""

    def __init__(self, psimod_path: str | PathLike[str] | None = None):
        """
        Initialize PSI-MOD lookup with ontology file.

        Parameters
        ----------
        psimod_path
            Path to PSI-MOD.obo file. If None, uses bundled version.

        Attributes
        ----------
        natural_residue_smiles : dict[str, str]
            Mapping of natural amino acid single-letter codes to their SMILES strings.

        Examples
        --------
        >>> lookup = PsiModResolver()
        >>> smiles = lookup.resolve_smiles('Acetyl', 'A', 'N-term')


        """
        self._ontology: Ontology = self._load_ontology(psimod_path)

        self.natural_residue_smiles: dict[str, str] = self._get_natural_residue_smiles()

    @cache
    def resolve_smiles(
        self,
        tag: str,
        residue: str,
        term_spec: Literal["N-term", "C-term", "none"],
        case_sensitive: bool = False,
        take_first: bool = False,
        fallback: bool = False,
    ) -> str:
        """
        Resolve SMILES for a modification tag and residue.

        Parameters
        ----------
        tag
            Accession (MOD:00046), name/synonym (Phospho), or UNIMOD ID (UNIMOD:21).
        residue
            Single-letter amino acid code (A, C, D, etc.).
        term_spec
            TermSpec filter ('N-term', 'C-term', 'none').
        case_sensitive
            Whether to perform case-sensitive search for name/synonym.
        take_first
            When multiple matches found: If True, return first match, if False, raise ValueError.
        fallback
            If True, return unmodified amino acid SMILES if no modification found.

        Returns
        -------
        str
            SMILES string for the resolved modification.

        Raises
        ------
        ResidueNotFoundError
            If no matching residue found and fallback is False.
        SMILESNotFoundError
            If no matching residue with SMILES found and fallback is False.
        MultipleResiduesMatchedError
            If multiple matching residues with SMILES found and take_first is False.

        Examples
        --------
        Resolve O-phospho-L-serine by PSI-MOD accession:

        >>> lookup = PsiModResolver()
        >>> smiles = lookup.resolve_smiles('MOD:00046', 'S', 'none')
        >>> print(smiles)
        '*N[C@@H](COP(=O)(O)O)C(*)=O'

        Resolve by synonym:

        >>> smiles = lookup.resolve_smiles('Phospho', 'S', 'none')
        >>> print(smiles)
        '*N[C@@H](COP(O)(O)=O)C(*)=O'

        Resolve by UNIMOD ID:

        >>> smiles = lookup.resolve_smiles('UNIMOD:21', 'S', 'none')
        >>> print(smiles)
        '*N[C@@H](COP(O)(O)=O)C(*)=O'

        Use fallback to get unmodified residue if modification not found:

        >>> smiles = lookup.resolve_smiles('UnknownMod', 'S', 'none', fallback=True)
        >>> print(smiles)
        'OCC(N-*)C(-*)=O'

        Handle N-terminal modifications:

        >>> smiles = lookup.resolve_smiles('Acetyl', 'A', 'N-term')
        >>> print(smiles)
        'C[C@H](NC(C)=O)C(-*)=O'

        Allow approximate matching when multiple specific forms exist:

        >>> smiles = lookup.resolve_smiles('Oxidation', 'M', 'none', take_first=True)
        >>> print(smiles)
        '*N[C@@H](CCSC)C(*)=O'

        Accept direct SMILES input as tag:

        >>> smiles = lookup.resolve_smiles('SMILES:*N[C@@H](CCSC)C(*)=O', 'M', 'none')
        >>> print(smiles)
        '*N[C@@H](CCSC)C(*)=O'

        """
        # Direct SMILES input
        if tag.startswith("SMILES:"):
            return tag[7:]

        # Find matching terms
        found_terms = self._find(
            tag,
            residue=residue,
            term_spec=term_spec,
            case_sensitive=case_sensitive,
        )

        # Filter terms with SMILES
        terms_with_smiles = [term for term in found_terms if _get_smiles(term) is not None]

        # No matches with SMILES
        if not terms_with_smiles:
            if not fallback:
                if len(found_terms) == 0:
                    raise ResidueNotFoundError(
                        f"No matching residue found for tag '{tag}', residue '{residue}', "
                        f"term_spec '{term_spec}'"
                    )
                else:
                    raise SMILESNotFoundError(
                        f"No matching residue with SMILES found for tag '{tag}', residue "
                        f"'{residue}', term_spec '{term_spec}'"
                    )
            else:
                # Return unmodified amino acid SMILES
                return self.natural_residue_smiles[residue]

        # Single match
        if len(terms_with_smiles) == 1:
            return _get_smiles(terms_with_smiles[0])  # type: ignore[return-value] # already checked

        # Multiple matches
        elif take_first:
            # Return first match with SMILES
            return _get_smiles(terms_with_smiles[0])  # type: ignore[return-value] # already checked
        else:
            raise MultipleResiduesMatchedError(
                f"Multiple matching residues with SMILES found for tag '{tag}', residue "
                f"'{residue}', term_spec '{term_spec}': {[term.id for term in found_terms]}. Further specify "
                "your query or set take_first=True to take the first match with a smiles structure."
            )

    def _load_ontology(self, psimod_path: str | PathLike[str] | None) -> Ontology:
        """Load PSI-MOD ontology from OBO file."""
        if psimod_path is None:
            psimod_path = DOWNLOAD_URL
        return Ontology(psimod_path)

    def _get_natural_residue_smiles(self) -> dict[str, str]:
        """Get SMILES for all natural, standard, encoded residues."""
        natural_term = self._get_term("MOD:01441")  # natural, standard, encoded residue
        smiles_map = {
            _get_origin(term): _get_smiles(term) for term in _get_term_child_leafs(natural_term)
        }
        return {
            residue: smiles
            for residue, smiles in smiles_map.items()
            if smiles is not None and residue is not None
        }

    def _get_term(self, accession: str) -> Term:
        """
        Get term by PSI-MOD accession.

        Parameters
        ----------
        accession
            PSI-MOD accession (e.g., 'MOD:00046').

        Returns
        -------
        Term
            Pronto Term object for the given accession.

        Raises
        ------
        KeyError
            If accession not found in ontology.
        TypeError
            If accession does not correspond to a Term.

        """
        term = self._ontology[accession]
        if not isinstance(term, Term):
            msg = f"{accession} is not a Term"
            raise TypeError(msg)
        return term

    def _find_by_name(self, name: str, case_sensitive: bool = False) -> list[Term]:
        """
        Find terms by name or synonym.

        Searches through term names and synonyms for matches.

        Parameters
        ----------
        name
            Name or synonym to search for.
        case_sensitive
            Whether to perform case-sensitive search.

        Returns
        -------
        list[Term]
            List of matching Terms, or an empty list if none found.

        """
        # Normalize search name
        search_name = name if case_sensitive else name.lower()

        search_results = []

        for term in self._ontology.terms():
            # Check main name
            if term.name:
                term_name = term.name if case_sensitive else term.name.lower()
                if term_name == search_name:
                    search_results.append(term)

            # Check synonyms
            for syn in term.synonyms:
                syn_desc = syn.description if case_sensitive else syn.description.lower()
                if syn_desc == search_name:
                    search_results.append(term)

        return search_results

    def _find_by_unimod(self, unimod_id: str | int) -> list[Term]:
        """
        Find terms by UNIMOD accession.

        Searches for PSI-MOD term that has the given UNIMOD ID in its xrefs.
        Accepts both 'UNIMOD:21', 'U:21', and '21' formats.

        Parameters
        ----------
        unimod_id
            UNIMOD ID (e.g., '21' or 'UNIMOD:21').

        Returns
        -------
        list[Term]
            Matching PSI-MOD Terms, or an empty list if not found.

        """
        # Normalize UNIMOD ID
        match unimod_id:
            case int(x):
                unimod_id = f"unimod:{x}"
            case str(x) if x.isdigit():
                unimod_id = f"unimod:{x}"
            case str(x) if x.lower().startswith("u:"):
                unimod_id = f"unimod:{x[2:]}"
            case str(x) if x.lower().startswith("unimod:"):
                unimod_id = x.lower()
            case _:
                raise ValueError(f"Invalid UNIMOD ID format: {unimod_id}")

        search_results: list[Term] = []

        # Search xrefs
        for term in self._ontology.terms():
            for xref in term.xrefs:
                if xref.id == "Unimod:" and f"unimod:{xref.description}" == unimod_id:
                    search_results.append(term)

        return search_results

    def _find(
        self,
        tag: str,
        residue: str | None = None,
        term_spec: Literal["N-term", "C-term", "none"] | None = None,
        case_sensitive: bool = False,
    ) -> list[Term]:
        """
        Find a terms by various identifiers.

        Searches by accession, name/synonym, or UNIMOD ID.

        Parameters
        ----------
        tag
            Accession (MOD:00046), name/synonym (Phospho), or UNIMOD ID (UNIMOD:21).
        residue
            If provided, filter results to modifications for this amino acid.
        term_spec
            If provided, filter results by TermSpec ('N-term', 'C-term', 'none').
        case_sensitive
            Whether to perform case-sensitive search for name/synonym.

        Returns
        -------
        list[Term]
            Matching PSI-MOD Terms.

        """
        # Try accession lookup first
        if tag.startswith("MOD:"):
            term = self._get_term(tag)
            cv_term_origin = _get_origin(term)
            cv_term_termspec = _get_termspec(term)

            # For terminal modifications, check if residue matches (if Origin is set)
            # Some terminal mods work on any residue and won't have Origin set
            if residue is not None and cv_term_origin is not None and cv_term_origin != residue:
                raise ValueError(f"Term {tag} does not match residue filter {residue}")
            if term_spec is not None and cv_term_termspec != term_spec:
                raise ValueError(f"Term {tag} does not match TermSpec filter {term_spec}")
            return [term]

        elif tag.lower().startswith("unimod:") or tag.lower().startswith("u:"):
            found_terms = self._find_by_unimod(tag)

        else:
            found_terms = self._find_by_name(tag, case_sensitive=case_sensitive)

        # Apply residue and term_spec filters
        found_terms = [
            term
            for term in found_terms
            if (residue is None or _get_origin(term) == residue)
            and (term_spec is None or _get_termspec(term) == term_spec)
        ]

        return found_terms


def _get_term_child_leafs(term: Term) -> list[Term]:
    """Get all child leaf terms of a given term."""
    leaf_terms = [t for t in term.subclasses(with_self=False) if t.is_leaf()]
    return leaf_terms


def _get_xref_value(term: Term, key: str) -> str | None:
    """Extract xref value by key."""
    for xref in term.xrefs:
        if xref.id == key:
            return xref.description
    return None


def _get_smiles(term: Term) -> str | None:
    """Get SMILES from term xrefs."""
    return _get_xref_value(term, "SMILES:")


def _get_origin(term: Term) -> str | None:
    """Get Origin (amino acid) from term xrefs."""
    return _get_xref_value(term, "Origin:")


def _get_termspec(term: Term) -> Literal["N-term", "C-term", "none"] | None:
    """Get TermSpec from term xrefs."""
    value = _get_xref_value(term, "TermSpec:")
    if value in ("N-term", "C-term", "none"):
        return value  # type: ignore[return-value]
    return None
