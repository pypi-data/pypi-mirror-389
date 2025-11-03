from importlib import metadata

__version__ = metadata.version(__name__)

__all__ = ["__version__"]

# do not include in namespace
del metadata
