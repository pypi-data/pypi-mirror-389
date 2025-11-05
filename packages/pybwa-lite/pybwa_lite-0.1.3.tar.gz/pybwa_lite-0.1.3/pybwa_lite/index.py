# pybwa/index.py
from .fmidx import FMIndex
from pathlib import Path
import os

def build_index(ref_path, out_path=None):
    """
    Build FM-index for a given reference.
    - If `ref_path` is a path to a FASTA file → reads from file.
    - If it's a raw sequence string (like 'ACGTACGTACGT$') → uses it directly.
    Returns an FMIndex object.
    """
    #  Case 1: input is a file path
    if os.path.exists(ref_path):
        with open(ref_path) as f:
            seqs = []
            for line in f:
                if not line.startswith(">"):
                    seqs.append(line.strip())
            text = "".join(seqs)
    else:
        #  Case 2: input is a raw sequence string
        text = ref_path.strip()

    #  Ensure sentinel symbol
    if not text.endswith("$"):
        text += "$"

    #  Build FMIndex
    fm = FMIndex(text)

    #  Optionally save serialized version
    if out_path:
        out_path = Path(out_path)
        fm.save(out_path)

    return fm


def load_index(path):
    """Load serialized FMIndex object from disk."""
    return FMIndex.load(path)
