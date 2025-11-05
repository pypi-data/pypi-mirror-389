# Residuum

Converting peptidoforms to residue SMILES using the PSI-MOD CV

## Overview

Residuum converts peptide sequences in ProForma notation to a list of residue-level SMILES
representations. It resolves modifications through the PSI-MOD ontology, supporting multiple
modification formats.

## Features

- **ProForma parsing**: Leverage Pyteomics for full ProForma v2 support
- **PSI-MOD resolving**: Query modifications by accession, name, or synonym
- **Multiple formats**: Support MOD:XXXXX, UNIMOD:XXX, modification names, custom SMILES
- **Smart matching**: Exact, approximate (parent terms), and fallback strategies
- **Terminal handling**: Automatic N-term/C-term SMILES reformatting to add H2N- and -COOH groups

## Installation

```bash
pip install residuum
```
