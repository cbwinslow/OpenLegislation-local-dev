# OpenLegislation Dependency Management

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python dependency management and packaging.

## Quick Start

1. **Install dependencies:**
   ```bash
   ./uv-manage.sh install
   ```

2. **Install with development tools:**
   ```bash
   ./uv-manage.sh install-dev
   ```

3. **Run commands in the uv environment:**
   ```bash
   ./uv-manage.sh run python -m pytest
   ./uv-manage.sh run python tools/master_ingestion.py
   ```

## Key Files

- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions (1.1MB, 287 packages)
- `.python-version` - Python version specification (3.12)
- `uv-manage.sh` - Convenience script for common uv operations

## Dependency Groups

- **Main dependencies**: Core functionality (CrewAI, database, ML libraries)
- **Dev dependencies**: Code formatting, linting, type checking
- **Test dependencies**: Testing frameworks and utilities
- **Docs dependencies**: Documentation generation

## Common Commands

```bash
# Install dependencies
./uv-manage.sh install          # Production only
./uv-manage.sh install-dev      # With dev tools
./uv-manage.sh install-test     # With test tools
./uv-manage.sh install-all      # Everything

# Add dependencies
./uv-manage.sh add requests 2.31.0    # Production dependency
./uv-manage.sh add-dev black          # Dev dependency

# Update dependencies
./uv-manage.sh update                  # All packages
./uv-manage.sh update-package crewai   # Specific package

# Run commands
./uv-manage.sh run python -c "import crewai; print('OK')"
./uv-manage.sh run pytest tests/

# Other utilities
./uv-manage.sh status     # Show dependency status
./uv-manage.sh clean      # Clean cache and virtual env
./uv-manage.sh help       # Show all commands
```

## Benefits of uv

- ⚡ **Fast**: 10-100x faster than pip
- 🔒 **Reproducible**: Lock file ensures consistent installs
- 🐍 **Python version aware**: Handles multiple Python versions
- 📦 **Modern**: Supports modern Python packaging standards
- 🔄 **Incremental**: Only installs changed dependencies

## Migration from requirements.txt

The old `requirements.txt` has been replaced with `pyproject.toml` for better dependency management. The lock file (`uv.lock`) ensures reproducible builds across different environments.

## Troubleshooting

If you encounter issues:

1. **Clean and reinstall:**
   ```bash
   ./uv-manage.sh clean
   ./uv-manage.sh install
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.10-3.13
   ```

3. **Update uv:**
   ```bash
   pip install --upgrade uv
   ```

For more information, see the [uv documentation](https://docs.astral.sh/uv/).