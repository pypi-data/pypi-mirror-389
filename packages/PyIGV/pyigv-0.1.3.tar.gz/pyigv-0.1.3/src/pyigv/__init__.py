__version__ = "0.1.3"  # bump this whenever you release a new version

# import the two main exports from alignment.py
from .alignment import Alignment, plot_alignments

# make sure that `from pyigv import *` also pulls them in
__all__ = [
    "Alignment",
    "plot_alignments",
]
