"""Open any supported file from one function."""

from . import chromeleon_csv
from . import masslynx


format_handling_submodules = [chromeleon_csv, masslynx]


def read(path, *args, **kwargs):
    """Open a data file containing a chromatogram.

    Parameters
    ----------
    path : str
        The path of the file to open.
    *args, **kwargs
        The positional and keyword arguments to pass to the

    Returns
    -------
    chromatograpy.Chromatogram or list of
        The chromatogram(s) read in the given file.
    """
    for module in format_handling_submodules:
        if module.can_read(path):
            return module.read(path, *args, **kwargs)

    raise ValueError("The given file's format is not supported.") from None
