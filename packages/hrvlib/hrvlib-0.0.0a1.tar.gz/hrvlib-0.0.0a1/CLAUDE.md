# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hrvlib** is a Python library with C++ extensions built using pybind11 and scikit-build-core. The project creates Python bindings for C++ code, exposing C++ functionality through a Python interface.

## Architecture

### Hybrid Python/C++ Structure

The project follows a dual-language architecture:

- **C++ Core** (`src/main.cpp`): Contains the native C++ implementations that are exposed to Python via pybind11. The C++ module is compiled as `_core` and contains the low-level functionality.

- **Python Interface** (`src/hrvlib/__init__.py`): Provides the Python-facing API that wraps the compiled C++ module (`_core`). This layer can add pure Python utilities or convenience functions around the C++ bindings.

### Build System

The project uses **scikit-build-core** as the build backend, which bridges CMake (for C++ compilation) with Python packaging:

1. CMake (`CMakeLists.txt`) defines how to build the C++ extension using pybind11
2. scikit-build-core orchestrates the build process
3. The compiled C++ module (`_core`) is installed alongside the Python package
4. Cache invalidation is configured for source files (`.h`, `.c`, `.hpp`, `.cpp`), `CMakeLists.txt`, and `pyproject.toml`

## Development Commands

### Building the Package

```bash
# Install in development mode with editable install
uv pip install -e .

# Build the package (creates wheel in dist/)
uv pip install build && python -m build
```

### Testing

```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=hrvlib --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_core.py

# Run specific test function
uv run pytest tests/test_core.py::test_hello
```

### Python Development

```bash
# Requires Python >=3.12 as specified in pyproject.toml
python --version

# The package can be imported after installation
python -c "from hrvlib import hello; print(hello())"
```

### Working with C++ Extensions

When modifying C++ code (`src/main.cpp`):

1. Changes require rebuilding the package: `uv pip install -e . --force-reinstall --no-deps`
2. The pybind11 module definition is in `PYBIND11_MODULE(_core, m)` - this is where C++ functions are exposed to Python
3. New C++ functions must be added to both the C++ implementation and the pybind11 module binding

## Project Structure

```
src/
├── main.cpp              # C++ implementation with pybind11 bindings
└── hrvlib/
    └── __init__.py       # Python package interface
```

The package name matches the project name (`hrvlib`) and the compiled extension is `_core`, imported as `hrvlib._core`.

## Key Build Dependencies

- **pybind11**: C++/Python binding library (found via CMake CONFIG mode)
- **scikit-build-core**: Modern Python build backend for CMake projects
- **CMake**: Required minimum version 3.15

## Development Notes

- The build directory pattern uses `build/{wheel_tag}` for multi-platform builds
- Cache keys ensure rebuild when source files, CMake config, or pyproject.toml change
- The CMake configuration uses `SKBUILD_PROJECT_NAME` variable from scikit-build-core
- Python 3.12+ is required as specified in `requires-python`
