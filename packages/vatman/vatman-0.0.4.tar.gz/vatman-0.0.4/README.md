# Vatman

## Prerequisites

### Poetry
This project uses [Poetry](https://python-poetry.org/) dependency manager.

Install Poetry following these [instructions](https://python-poetry.org/docs/#installation).

## Development

This project uses [pre-commit](https://pre-commit.com) to check files before they are committed to git.

*Pre-commit* is a multi-language package manager for pre-commit git hooks. You specify a list of hooks you want and pre-commit manages the installation and execution of any hook written in any language before every commit.

### How to set up pre-commit

Pre-commit itself is installed via Poetry as a *development* dependency. The hooks are configured in `.pre-commit-config.yaml`.

After cloning this repo and installing the dependencies via Poetry, **install the git hook scripts**:

```shell script
# Option 1
source .venv/bin/activate
pre-commit install

# Option 2
poetry run pre-commit install
```

**NOTE:** After installing the git hook scripts, there is no need to activate the virtual environment before each commit.

### Run pre-commit manually

The whole point of pre-commit hooks is that they run automatically before every commit.
However, it is also possible to run pre-commit manually:

```shell script
# Option 1 (with the virtual environment activated)
pre-commit run --all-files

# Option 2 (via Poetry)
poetry run pre-commit run --all-files
```
