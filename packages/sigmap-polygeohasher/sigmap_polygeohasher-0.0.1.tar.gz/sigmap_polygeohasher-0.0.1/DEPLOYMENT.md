# Deploying sigmap-polygeohasher as a pip package

This guide explains how to deploy `sigmap-polygeohasher` as a pip-installable package.

## Current Status

The package is currently set up for **local/editable installation** and ready for **distribution to PyPI** or other package indexes.

## Local Installation (Development)

For development or local testing, install the package in editable mode:

```bash
cd sigmap-polygeohasher/
pip install -e .
```

This allows you to make changes to the code and have them immediately available without reinstalling.

## Preparing for PyPI Distribution

### 1. Update Version

Before releasing, update the version in `pyproject.toml`:

```toml
version = "0.0.2"  # Increment as needed
```

### 2. Build Distribution Packages

To create distributable packages:

```bash
# Install build tools if not already installed
pip install build twine

# Build source and wheel distributions
cd sigmap-polygeohasher/
python -m build
```

This creates:
- `dist/sigmap_polygeohasher-0.0.1.tar.gz` (source distribution)
- `dist/sigmap_polygeohasher-0.0.1-py3-none-any.whl` (wheel)

### 3. Test the Build Locally

Before uploading to PyPI, test the built package:

```bash
# Install the built wheel
pip install dist/sigmap_polygeohasher-0.0.1-py3-none-any.whl

# Test it
python -c "import polygeohasher; print(polygeohasher.__version__)"
```

### 4. Upload to PyPI Test

Test upload to PyPI's test instance:

```bash
python -m twine upload --repository testpypi dist/*
```

Install from test PyPI:

```bash
pip install -i https://test.pypi.org/simple/ sigmap-polygeohasher
```

### 5. Upload to PyPI

Once tested, upload to real PyPI:

```bash
python -m twine upload dist/*
```

This requires PyPI credentials. You can:
1. Use your PyPI account login
2. Use API tokens (recommended for CI/CD)

Set up API tokens at: https://pypi.org/manage/account/token/

## Installation from PyPI

After uploading, users can install the package:

```bash
pip install sigmap-polygeohasher
```

Or from a specific repository:

```bash
pip install -i https://test.pypi.org/simple/ sigmap-polygeohasher
```

## Continuous Integration

You can automate releases using GitHub Actions or similar CI/CD. Example workflow:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Next Steps

1. **Add a LICENSE file** if you haven't already (MIT license referenced in pyproject.toml)
2. **Update README.md** with installation instructions and examples
3. **Add project URLs** in pyproject.toml (Homepage, Issues, etc.)
4. **Create a .gitignore** to exclude build artifacts
5. **Document API** in the README or separate docs
6. **Add tests** to the package if not already included

## Package Structure

The package follows Python packaging best practices:

```
sigmap-polygeohasher/
├── pyproject.toml          # Build configuration
├── README.md               # Package description
├── src/
│   └── polygeohasher/      # Main package
│       ├── __init__.py     # Public API
│       ├── logger.py       # Logging utilities
│       ├── adaptative_geohash_coverage.py
│       ├── plot_geohash_coverage.py
│       └── utils/
│           ├── algorithms.py
│           ├── gadm_download.py
│           ├── geohash.py
│           └── polygons.py
└── tests/                  # Test suite
```

## Troubleshooting

### Import Errors After Installation

If you get import errors, ensure:
1. All relative imports are correct
2. The package structure matches what's in `pyproject.toml`
3. You've installed dependencies: `pip install -r requirements.txt`

### Build Errors

Common issues:
- Missing dependencies in `pyproject.toml`
- Incorrect package paths in build configuration
- Version conflicts with existing packages

Check build logs for specific error messages.

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPA Packaging Guide](https://py-pkgs.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Hatchling Documentation](https://hatch.pypa.io/)
