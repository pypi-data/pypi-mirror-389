# samtools.py

# pybwa/samtools.py
from dataclasses import dataclass

@dataclass
class SAMRecord:
    qname: str
    flag: int
    rname: str
    pos: int
    mapq: int
    cigar: str
    seq: str
    qual: str

    def to_sam_line(self):
        return f"{self.qname}\t{self.flag}\t{self.rname}\t{self.pos}\t{self.mapq}\t{self.cigar}\t*\t0\t0\t{self.seq}\t{self.qual}"

def write_sam_header(ref_name="ref"):
    header = [
        "@HD\tVN:1.6\tSO:unsorted",
        f"@SQ\tSN:{ref_name}\tLN:0"
    ]
    return "\n".join(header)
