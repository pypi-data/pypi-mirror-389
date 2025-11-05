# test_fmindex.py

# tests/test_fmindex.py
import pytest
from pybwa import index

@pytest.fixture
def small_text():
    return "ACGCGTACGT$"

@pytest.fixture
def fm_index_obj(small_text):
    return index.build_index(small_text)

def test_suffix_array_sorted(fm_index_obj):
    sa = fm_index_obj.suffix_array
    text = fm_index_obj.text
    suffixes = [text[i:] for i in sa]
    assert suffixes == sorted(suffixes), "Suffix array not sorted correctly"

def test_bwt_last_column(fm_index_obj):
    sa = fm_index_obj.suffix_array
    bwt = fm_index_obj.bwt
    # The BWT last column must have same length as input text
    assert len(bwt) == len(fm_index_obj.text)
    # Check last char of original text is '$'
    assert fm_index_obj.text[-1] == '$'

def test_backward_search_basic(fm_index_obj):
    hits = fm_index_obj.backward_search("ACG")
    # Should find occurrences of 'ACG' in text
    assert isinstance(hits, list)
    assert all(isinstance(i, int) for i in hits)
    assert len(hits) > 0, "Backward search returned no hits"

def test_rank_consistency(fm_index_obj):
    # Check rank is non-decreasing for each character
    text = fm_index_obj.text
    for c in "ACGT$":
        ranks = [fm_index_obj.rank(c, i) for i in range(len(text))]
        assert all(ranks[i] <= ranks[i + 1] for i in range(len(ranks) - 1)), f"Rank not monotonic for {c}"
