# pybwa/align.py
from .samtools import SAMRecord
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

Alignment = namedtuple("Alignment", ["pos", "score", "cigar"])

# -----------------------------------------
# Default scoring configuration
# -----------------------------------------
MATCH_SCORE = 2
MISMATCH_PENALTY = -2
GAP_OPEN = -3
GAP_EXTEND = -1
BAND_WIDTH = 5  # adjustable band width for local alignment
# -----------------------------------------


# ==========================================================
# Banded Smith–Waterman implementation
# ==========================================================
def banded_smith_waterman(ref, read, start_pos,
                          match=MATCH_SCORE,
                          mismatch=MISMATCH_PENALTY,
                          gap_open=GAP_OPEN,
                          gap_extend=GAP_EXTEND,
                          band=BAND_WIDTH):
    """
    Perform banded Smith–Waterman alignment between read and reference segment
    starting at start_pos. Returns (best_score, best_cigar).
    """
    n = len(read)
    m = min(len(ref) - start_pos, len(read) + band)
    ref_seg = ref[start_pos:start_pos + m]

    H = [[0] * (m + 1) for _ in range(n + 1)]  # scores
    E = [[0] * (m + 1) for _ in range(n + 1)]  # gap in read
    F = [[0] * (m + 1) for _ in range(n + 1)]  # gap in ref
    max_score = 0
    max_pos = (0, 0)

    for i in range(1, n + 1):
        for j in range(max(1, i - band), min(m, i + band) + 1):
            match_score = match if read[i - 1] == ref_seg[j - 1] else mismatch

            E[i][j] = max(E[i][j - 1] + gap_extend, H[i][j - 1] + gap_open)
            F[i][j] = max(F[i - 1][j] + gap_extend, H[i - 1][j] + gap_open)
            H[i][j] = max(0,
                          H[i - 1][j - 1] + match_score,
                          E[i][j],
                          F[i][j])

            if H[i][j] > max_score:
                max_score = H[i][j]
                max_pos = (i, j)

    # Traceback for CIGAR
    i, j = max_pos
    cigar_ops = []
    while i > 0 and j > 0 and H[i][j] > 0:
        if H[i][j] == H[i - 1][j - 1] + (match if read[i - 1] == ref_seg[j - 1] else mismatch):
            cigar_ops.append("M")
            i -= 1
            j -= 1
        elif H[i][j] == E[i][j]:
            cigar_ops.append("I")
            j -= 1
        elif H[i][j] == F[i][j]:
            cigar_ops.append("D")
            i -= 1
        else:
            break

    cigar_ops.reverse()
    cigar = compress_cigar("".join(cigar_ops))
    return max_score, cigar


def compress_cigar(cigar_str):
    """Convert raw operation string to compressed form, e.g. MMMIID -> 3M2I1D"""
    if not cigar_str:
        return "*"
    result = []
    last = cigar_str[0]
    count = 1
    for c in cigar_str[1:]:
        if c == last:
            count += 1
        else:
            result.append(f"{count}{last}")
            last = c
            count = 1
    result.append(f"{count}{last}")
    return "".join(result)


# ==========================================================
# File parsing utilities
# ==========================================================
def read_sequences(path):
    """
    Autodetect and parse FASTA or FASTQ.
    Returns list of tuples: (qname, seq, qual)
    """
    reads = []
    with open(path) as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == ">":  # FASTA
            qname, seq = None, []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if qname:
                        reads.append((qname, "".join(seq), "*"))
                    qname = line[1:]
                    seq = []
                else:
                    seq.append(line)
            if qname:
                reads.append((qname, "".join(seq), "*"))
        elif first_char == "@":  # FASTQ
            while True:
                name = f.readline().strip()
                if not name:
                    break
                seq = f.readline().strip()
                f.readline()  # '+'
                qual = f.readline().strip()
                reads.append((name[1:], seq, qual))
        else:
            raise ValueError("Unrecognized input format (expected FASTA or FASTQ).")
    return reads


# ==========================================================
# Alignment core (single-read)
# ==========================================================
def align_single_read(entry, ref, fm_index, match, mismatch, gap_open, gap_extend, score_threshold):
    """Align a single read using FM-index seeds and banded Smith–Waterman extension."""
    qname, read, qual = entry
    hits = fm_index.backward_search(read[:10])  # seed by first 10-mer
    best_score, best_pos, best_cigar = -9999, None, "*"
    for pos in hits:
        score, cigar = banded_smith_waterman(ref, read, pos, match, mismatch, gap_open, gap_extend)
        if score > best_score:
            best_score, best_pos, best_cigar = score, pos, cigar
    if best_pos is not None and best_score >= score_threshold:
        return SAMRecord(qname=qname, flag=0, rname="ref", pos=best_pos + 1,
                         mapq=60, cigar=best_cigar, seq=read, qual=qual)
    else:
        return SAMRecord(qname=qname, flag=4, rname="*", pos=0,
                         mapq=0, cigar="*", seq=read, qual=qual)


# ==========================================================
# Multithreaded parallel alignment + Progress bar
# ==========================================================
def align_reads(reads_path, fm_index, threads=4,
                match=MATCH_SCORE, mismatch=MISMATCH_PENALTY,
                gap_open=GAP_OPEN, gap_extend=GAP_EXTEND,
                score_threshold=5):
    """
    Parallel alignment of reads using FM-index + banded Smith–Waterman.
    Supports FASTA and FASTQ. Displays progress bar.
    """
    ref = fm_index.text[:-1]
    reads = read_sequences(reads_path)

    results = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(align_single_read, r, ref, fm_index,
                            match, mismatch, gap_open, gap_extend,
                            score_threshold): r for r in reads
        }

        for fut in tqdm(as_completed(futures),
                        total=len(futures),
                        desc="Aligning reads",
                        unit="read"):
            results.append(fut.result())

    # Maintain input order for deterministic output
    read_order = {r[0]: i for i, r in enumerate(reads)}
    results.sort(key=lambda x: read_order.get(x.qname, 0))
    return results
