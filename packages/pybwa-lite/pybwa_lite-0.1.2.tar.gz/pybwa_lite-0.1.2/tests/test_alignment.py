# test_alignment.py

# tests/test_alignment.py
import pytest
from pybwa import index, align

@pytest.fixture(scope="module")
def reference_text():
    # Simple reference genome
    return "ACGTACGTACGT$"

@pytest.fixture(scope="module")
def fm_index_obj(reference_text, tmp_path_factory):
    fm = index.build_index(reference_text)
    path = tmp_path_factory.mktemp("data") / "ref.pyi"
    fm.save(path)
    return index.load_index(path)

def test_single_read_alignment(fm_index_obj):
    read = "ACGTAC"
    results = align.align_reads(
        reads_path=create_temp_fasta([("read1", read)]),
        fm_index=fm_index_obj,
        threads=2
    )
    assert len(results) == 1
    rec = results[0]
    assert rec.flag in (0, 4)
    assert isinstance(rec.cigar, str)
    assert rec.seq == read

def test_fastq_alignment_with_qualities(fm_index_obj):
    read_seq = "ACGTAC"
    read_qual = "IIIIII"
    reads_path = create_temp_fastq([("read2", read_seq, read_qual)])
    results = align.align_reads(reads_path, fm_index_obj, threads=2)
    assert len(results) == 1
    rec = results[0]
    assert rec.qual == read_qual
    assert rec.seq == read_seq
    assert isinstance(rec.to_sam_line(), str)

def test_multithreaded_alignment_consistency(fm_index_obj):
    reads = [("r1", "ACGTAC", "IIIIII"), ("r2", "GTACGT", "IIIIII")]
    reads_path = create_temp_fastq(reads)
    results = align.align_reads(reads_path, fm_index_obj, threads=4)
    assert len(results) == 2
    # Ensure results stable and deterministic
    qnames = [r.qname for r in results]
    assert qnames == ["r1", "r2"]

# -------------------------------------------------------
# Helper functions for temporary read file creation
# -------------------------------------------------------
import tempfile
from pathlib import Path

def create_temp_fasta(reads):
    """Create temporary FASTA file"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".fa")
    for name, seq in reads:
        tmp.write(f">{name}\n{seq}\n".encode())
    tmp.close()
    return tmp.name

def create_temp_fastq(reads):
    """Create temporary FASTQ file"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".fq")
    for name, seq, qual in reads:
        tmp.write(f"@{name}\n{seq}\n+\n{qual}\n".encode())
    tmp.close()
    return tmp.name
