try:
    from epigeec._version import version as __version__
except ImportError:
    # Fallback for development installs without setuptools-scm
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("epigeec")
    except PackageNotFoundError:
        __version__ = "unknown"
