"""Exceptions for the residuum package."""


class ResiduumError(Exception):
    """Base exception for residuum package."""


class ResidueNotFoundError(ResiduumError):
    """
    Residue could not be resolved in PSI-MOD.

    Raised when a residue tag cannot be matched to any PSI-MOD term and fallback mode is not
    enabled.
    """


class SMILESNotFoundError(ResiduumError):
    """
    SMILES for a residue or modification could not be found.

    Raised when a resolved PSI-MOD term does not have an associated SMILES structure.
    """


class MultipleResiduesMatchedError(ResiduumError):
    """
    Tag matched to multiple terms in PSI-MOD.

    Raised when a residue tag matches multiple PSI-MOD terms and take_first is False.
    """


class UnsupportedProFormaError(ResiduumError):
    """
    ProForma feature is unsupported.

    Raised when a ProForma feature is used that is not supported by residuum.
    """
