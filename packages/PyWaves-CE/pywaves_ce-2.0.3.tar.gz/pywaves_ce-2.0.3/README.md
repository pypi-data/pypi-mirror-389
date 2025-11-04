# PyWaves – Community Edition

[![PyPI version](https://img.shields.io/pypi/v/pywaves-ce.svg)](https://pypi.org/project/pywaves-ce/)

**[PyWaves-CE](https://pypi.org/project/pywaves-ce/)** is a community-maintained fork of the original **[PyWaves](https://pypi.org/project/pywaves/)** library for the Waves blockchain.
It is a *drop-in replacement* that keeps the import path `pywaves` intact, so existing code keeps working without edits.

```bash
pip install pywaves-ce
```

## Basic Example
```python
import pywaves as pw

# Create addresses from seeds
firstAddress = pw.Address(seed = 'this is just a simple test seed 1')
secondAddress = pw.Address(seed = 'this is just a simple test seed 2')

# Send Waves from one address to another
tx = firstAddress.sendWaves(secondAddress, 100000)
assert 'id' in tx

# Wait for transaction to complete and verify status
tx = pw.waitFor(tx['id'])
assert tx['applicationStatus'] == 'succeeded'
```

## Purpose & Rationale of Community Edition

- **Unmaintained upstream** – the original [PyWaves](https://pypi.org/project/pywaves/) no longer receives updates.
- **Drop-in replacement** – legacy code keeps using `import pywaves as pw` unchanged.
- **Active maintenance** – security fixes and new Waves features are delivered regularly.
- **Repository layout** – **[PyWaves-CE](https://pypi.org/project/pywaves-ce/)** hosts the pristine [1.0.5 upstream snapshot](https://github.com/PyWaves-CE/PyWaves-CE/tree/PyWaves-1.0.5).
- **PyPI distribution** – published as **pywaves-ce** while the internal package name remains `pywaves`.
- **Versioning roadmap**
  - **1.x** – strict legacy API compatibility with upstream 1.0.5.
  - **2.x** – modernization and intentional breaking changes.

## Documentation
- Wiki: https://github.com/PyWaves-CE/PyWaves-CE/wiki

## License
Code released under the [MIT License](https://github.com/PyWaves-CE/PyWaves-CE/blob/main/LICENSE).

## Development and Packaging

PyWaves uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

### Installation for Development

1. Install Poetry (if not already installed)
```bash
pip install poetry
```

2. Install dependencies
```bash
poetry install
```

3. Activate the virtual environment
```bash
poetry shell
```

### Building the Package

```bash
poetry build
```

This will create both wheel and source distributions in the `dist/` directory.

### Testing Across Python Versions

PyWaves includes a workflow testing system that can test across multiple Python versions:

```bash
python workflow_venvs.py
python workflow_tests.py
```

This will test the library with all Python versions specified in PYTHON_VERSIONS.py.