# Installation Guide

## Quick Start (Recommended)

### 1. Install required dependencies with specific versions

The package requires specific versions of dependencies for compatibility. Use these commands in order:

```bash
# Using uv (faster, recommended)
uv pip install dbinfer-bench
uv pip install torchdata==0.9.0
uv pip uninstall dgl  # Remove any existing DGL installation
uv pip install dgl -f https://data.dgl.ai/wheels/torch-2.4/cu124/repo.html

# Or using pip
pip install dbinfer-bench
pip install torchdata==0.9.0
pip uninstall dgl  # Remove any existing DGL installation
pip install dgl -f https://data.dgl.ai/wheels/torch-2.4/cu124/repo.html
```

**Note**: DGL requires a specific wheel from the DGL repository for compatibility with PyTorch 2.4 and CUDA 12.4. The standard PyPI version may not work correctly.

### 2. Install this package in development mode

From the project root directory:

```bash
pip install -e .
# or
uv pip install -e .
```

This will install the package in "editable" mode, meaning changes to the source code will be immediately reflected without reinstalling.

### 3. Verify installation

```bash
python -c "from dbinfer_relbench_adapter import load_dbinfer_data; print('✓ Package installed successfully!')"
```

### 4. Run the example

```bash
python example.py
```

## Installation Options

### Development installation (with dev dependencies)

```bash
pip install -e ".[dev]"
```

This includes testing and linting tools:
- pytest
- pytest-cov
- black
- isort
- flake8
- mypy

### Regular installation (from source)

```bash
pip install .
```

### Building a distribution

To build wheel and source distributions:

```bash
pip install build
python -m build
```

This creates distributions in the `dist/` directory that can be:
- Uploaded to PyPI: `twine upload dist/*`
- Installed locally: `pip install dist/dbinfer_relbench_adapter-0.1.0-py3-none-any.whl`
- Shared with others

## Publishing to PyPI

### 1. Create accounts
- Create account on [PyPI](https://pypi.org) for production
- Create account on [TestPyPI](https://test.pypi.org) for testing

### 2. Install twine

```bash
pip install twine
```

### 3. Build the package

```bash
python -m build
```

### 4. Upload to TestPyPI (recommended first)

```bash
twine upload --repository testpypi dist/*
```

### 5. Test installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ dbinfer-relbench-adapter
```

### 6. Upload to PyPI (production)

```bash
twine upload dist/*
```

After publishing, anyone can install with:
```bash
pip install dbinfer-relbench-adapter
```

## Updating Package Metadata

Before publishing, update the following in `pyproject.toml`:
- Version number (for updates)

## Uninstallation

```bash
pip uninstall dbinfer-relbench-adapter
```

## Troubleshooting

### Import errors
Make sure dependencies are installed:
```bash
pip install dbinfer_bench relbench pandas numpy scikit-learn
```

### Permission errors during installation
Use `--user` flag:
```bash
pip install --user -e .
```

### Cache issues
Clear the cache:
```bash
python -c "from dbinfer_relbench_adapter import clear_cache; clear_cache()"
```
