# NEMO-hydra

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/NEMO-hydra?label=python)](https://www.python.org/downloads/release/python-3110/)
[![PyPI](https://img.shields.io/pypi/v/nemo-hydra?label=pypi%20version)](https://pypi.org/project/NEMO-hydra/)
[![Changelog](https://img.shields.io/gitlab/v/release/nemo-community/atlantis-labs/nemo-hydra?include_prereleases&label=changelog)](https://gitlab.com/nemo-community/atlantis-labs/nemo-hydra/nemo-community/atlantis-labs/nemo-hydra/-/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://gitlab.com/nemo-community/atlantis-labs/nemo-hydra/nemo-community/atlantis-labs/nemo-hydra/blob/main/LICENSE)

Plugin to facilitate NEMO integration within Hydra

## Installation

```bash
python -m install nemo-hydra
```

in `settings.py` add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    '...',
    'NEMO_hydra',
    '...'
]
```

## Usage

Usage instructions go here.

# Tests

To run the tests:
```bash
python run_tests.py
```
