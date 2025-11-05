import logging
import subprocess
import sys
from enum import Enum
from typing import Annotated

import typer

logger = logging.getLogger(__name__)


DryAnnotation = Annotated[
    bool,
    typer.Option(
        help='Show the command that would be run without running it.',
        show_default=False,
    ),
]


class OS(str, Enum):
    """Operating System."""

    Linux = 'linux'
    MacOS = 'mac'
    Windows = 'win'


def get_os() -> OS:
    """
    Similar to ``sys.platform`` and ``platform.system()``, but less ambiguous by returning an Enum
    instead of a string.

    Doesn't make granular distinctions of linux variants, OS versions, etc.
    """
    if sys.platform == 'darwin':
        return OS.MacOS
    if sys.platform == 'win32':
        return OS.Windows
    return OS.Linux


def run(dry: bool, *args) -> subprocess.CompletedProcess | None:
    logger.info(' '.join(map(str, args)))

    if dry:
        return None

    try:
        return subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(e)
        raise typer.Exit(1)


def is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    import importlib.util

    return importlib.util.find_spec(package_name) is not None


def install_package(package: str, dry: bool = False):
    """Install a Python package if not already installed."""
    if is_package_installed(package):
        logger.debug(f'Package `{package}` is already installed.')
        return

    run(dry, sys.executable, '-m', 'pip', 'install', package)
