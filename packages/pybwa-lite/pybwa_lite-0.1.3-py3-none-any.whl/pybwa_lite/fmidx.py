import pickle
from bisect import bisect_left
from collections import defaultdict

class FMIndex:
    """
    Basic FM-index implementation for DNA strings.
    Supports rank/select operations, backward search, and serialization.
    """

    def __init__(self, text: str):
        if not text.endswith("$"):
            text += "$"

        self.text = text
        self.suffix_array = self._build_suffix_array(text)
        self.bwt = self._build_bwt(text, self.suffix_array)
        self.C, self.occ_table = self._build_occurrence_table(self.bwt)

    # -------------------------------
    # Core FM-index Construction
    # -------------------------------

    def _build_suffix_array(self, text):
        """Naive O(n log n) suffix array construction."""
        return sorted(range(len(text)), key=lambda i: text[i:])

    def _build_bwt(self, text, sa):
        """Build Burrows–Wheeler Transform from suffix array."""
        return "".join(text[i - 1] if i != 0 else "$" for i in sa)

    def _build_occurrence_table(self, bwt):
        """
        Build cumulative count table and occurrence dictionary.
        C: maps character -> number of lexicographically smaller chars
        occ_table: prefix counts for each character at each position
        """
        alphabet = sorted(set(bwt))
        C = {}
        total = 0
        for c in alphabet:
            C[c] = total
            total += bwt.count(c)

        occ_table = defaultdict(list)
        counts = defaultdict(int)
        for ch in bwt:
            counts[ch] += 1
            for c in alphabet:
                occ_table[c].append(counts[c])

        return C, occ_table

    # -------------------------------
    # Rank and Backward Search
    # -------------------------------

    def rank(self, char, pos):
        """Return number of `char` occurrences in BWT up to (and including) pos."""
        if pos < 0:
            return 0
        if pos >= len(self.bwt):
            pos = len(self.bwt) - 1
        return self.occ_table[char][pos]

    def occ(self, char, start, end):
        """Return occurrences of char in BWT[start:end]."""
        return self.rank(char, end - 1) - self.rank(char, start - 1)

    def backward_search(self, pattern):
        """
        Perform backward search over FM-index.
        Returns list of positions in the original text where the pattern occurs.
        """
        l, r = 0, len(self.bwt)
        for char in reversed(pattern):
            if char not in self.C:
                return []
            l = self.C[char] + self.rank(char, l - 1)
            r = self.C[char] + self.rank(char, r - 1)
            if l >= r:
                return []

        # Return matching positions in the suffix array
        return [self.suffix_array[i] for i in range(l, r)]


    # -------------------------------
    # Serialization
    # -------------------------------

    def save(self, path):
        """Save FMIndex to disk using pickle."""
        data = {
            "text": self.text,
            "suffix_array": self.suffix_array,
            "bwt": self.bwt,
            "C": self.C,
            "occ_table": dict(self.occ_table),
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path):
        """Load FMIndex from pickle file."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(data["text"])
        obj.suffix_array = data["suffix_array"]
        obj.bwt = data["bwt"]
        obj.C = data["C"]
        obj.occ_table = defaultdict(list, data["occ_table"])
        return obj
