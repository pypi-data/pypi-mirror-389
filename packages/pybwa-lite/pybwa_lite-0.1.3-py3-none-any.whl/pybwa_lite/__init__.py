# pybwa/__init__.py

"""
pybwa: Educational Burrows–Wheeler Aligner in Python
----------------------------------------------------
A lightweight implementation of BWT + FM-index–based read alignment.

Modules:
    index      : Builds suffix array, BWT, and FM-index for a reference.
    fmidx      : Core FM-index structure (rank/select, backward search).
    align      : Seeding, extension, and scoring of reads.
    samtools   : Minimal SAM/BAM record writer (wrapper around pysam).
    cli        : Command-line interface (index, align).
"""

from .index import build_index, load_index
from .align import align_reads
from .samtools import SAMRecord, write_sam_header

__version__ = "0.1.3"
__author__ = "Soumyapriya Goswami"
__all__ = [
    "build_index",
    "load_index",
    "align_reads",
    "SAMRecord",
    "write_sam_header",
]
import sys
sys.modules['pybwa'] = sys.modules[__name__]
