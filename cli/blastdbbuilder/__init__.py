# blastdbbuilder/__init__.py

"""
blastdbbuilder

Lightweight CLI to download genomes, concatenate them, and build BLAST databases.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("blastdbbuilder")
except PackageNotFoundError:
    __version__ = "unknown"
