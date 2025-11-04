"""About vcf2bedgraph."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vcf2bedgraph")
except PackageNotFoundError:
    __version__ = "0.1.0"  # fallback version
