import pathlib as _pathlib
from importlib import metadata as _metadata

import toml as _toml

try:
    __version__ = _metadata.version(__package__)
except _metadata.PackageNotFoundError:  # pragma: no-cover
    # If the package is not installed such that it has distribution metadata
    # fallback to loading the version from the pyproject.toml file.
    _package_metadata = _toml.loads(
        _pathlib.Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    )
    try:
        __version__ = _package_metadata["tool"]["poetry"]["version"]
    except KeyError:
        __version__ = _package_metadata["project"]["version"]
