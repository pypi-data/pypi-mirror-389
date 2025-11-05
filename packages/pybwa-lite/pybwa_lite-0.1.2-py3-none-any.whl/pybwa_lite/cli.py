# cli.py

# pybwa/cli.py
import argparse
from .index import build_index, load_index
from .align import align_reads
from .samtools import write_sam_header

def main():
    parser = argparse.ArgumentParser(description="pybwa: Lightweight Python BWA-like aligner")
    sub = parser.add_subparsers(dest="cmd")

    p_index = sub.add_parser("index")
    p_index.add_argument("ref", help="Reference FASTA")
    p_index.add_argument("-o", "--out", help="Output index file", default="ref.pyi")

    p_align = sub.add_parser("align")
    p_align.add_argument("-i", "--index", help="Index file", required=True)
    p_align.add_argument("-r", "--reads", help="Reads file (FASTA)", required=True)
    p_align.add_argument("-o", "--out", help="Output SAM file", default="out.sam")

    args = parser.parse_args()

    if args.cmd == "index":
        print(f"Building FM-index for {args.ref}...")
        fm = build_index(args.ref, args.out)
        print(f"Saved index to {args.out}")
    elif args.cmd == "align":
        print(f"Loading index {args.index}...")
        fm = load_index(args.index)
        print(f"Aligning reads from {args.reads}...")
        with open(args.out, "w") as out:
            out.write(write_sam_header() + "\n")
            for rec in align_reads(args.reads, fm):
                out.write(rec.to_sam_line() + "\n")
        print(f"Wrote SAM to {args.out}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
