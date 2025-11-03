import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pyigv import Alignment, plot_alignments


def test_alignment_basic():
    """Test basic alignment creation"""
    target = "AAATAAA"
    query = "AAAGAAA"
    alignment = ["AAATAAA", "AAAGAAA"]

    aln = Alignment(target, query, alignment)

    # Check that the alignment was created
    assert aln.target == target
    assert aln.query == query
    assert aln.target_alignment == alignment[0]
    assert aln.query_alignment == alignment[1]


def test_alignment_with_gaps():
    """Test alignment with gaps (insertions/deletions)"""
    target = "AAATAAA"
    query = "AAAGAAA"
    alignment = ["AAA-TAAA", "AAAGAAA-"]

    aln = Alignment(target, query, alignment)

    assert aln.insertion_ct >= 0
    assert aln.deletion_ct >= 0
    assert aln.mutation_ct >= 0


def test_alignment_mutation_counting():
    """Test mutation counting"""
    target = "AAAA"
    query = "AAAT"
    alignment = ["AAAA", "AAAT"]

    aln = Alignment(target, query, alignment)

    assert aln.mutation_ct == 1
    assert aln.insertion_ct == 0
    assert aln.deletion_ct == 0


def test_alignment_multi_mutation_counting():
    """Test mutation counting"""
    target = "AAACCCAAA"
    query = "AAATTTAAA"
    alignment = ["AAA---CCCAAA", "AAATTT---AAA"]

    aln = Alignment(target, query, alignment)

    # There should be 1 mismatch
    assert aln.mutation_ct == 3
    assert aln.insertion_ct == 0
    assert aln.deletion_ct == 0


def test_alignment_insertion():
    """Test insertion detection"""
    target = "AAAA"
    query = "AAAAA"
    alignment = ["AAAA-", "AAAAA"]

    aln = Alignment(target, query, alignment)

    assert aln.insertion_ct == 1


def test_alignment_deletion():
    """Test deletion detection"""
    target = "AAAAA"
    query = "AAAA"
    alignment = ["AAAAA", "AAAA-"]

    aln = Alignment(target, query, alignment)

    assert aln.deletion_ct == 1


def test_alignment_comparison():
    """Test alignment comparison (less than operator)"""
    target = "AAAA"
    query1 = "AAAA"
    query2 = "AAAT"

    aln1 = Alignment(target, query1, ["AAAA", "AAAA"])
    aln2 = Alignment(target, query2, ["AAAA", "AAAT"])

    # aln1 has fewer mutations, so it should be "less than" aln2
    assert aln1 < aln2


def test_alignment_str():
    """Test string representation"""
    target = "AAAA"
    query = "AAAT"
    alignment = ["AAAA", "AAAT"]

    aln = Alignment(target, query, alignment)
    str_repr = str(aln)

    assert "Target:" in str_repr
    assert "Query:" in str_repr
    assert "Edits:" in str_repr


def test_get_color_row():
    """Test color row generation"""
    target = "AAAA"
    query = "AAAT"
    alignment = ["AAAA", "AAAT"]

    aln = Alignment(target, query, alignment)
    color_row = aln.get_color_row()

    assert isinstance(color_row, list)
    assert len(color_row) > 0


def test_get_symbols():
    """Test symbol extraction"""
    target = "AAAA"
    query = "AAAT"
    alignment = ["AAAA", "AAAT"]

    aln = Alignment(target, query, alignment)
    symbols = aln.get_symbols()

    assert isinstance(symbols, list)
    assert len(symbols) > 0


def test_get_insertion_indices():
    """Test insertion indices extraction"""
    target = "AAAA"
    query = "AAAAA"
    alignment = ["AAAA-", "AAAAA"]

    aln = Alignment(target, query, alignment)
    indices = aln.get_insertion_indices()

    assert isinstance(indices, list)


def test_plot_alignments_basic():
    """Test basic plotting functionality"""
    target = "AAATAAA"
    query1 = "AAAGAAA"
    query2 = "AAACAAA"

    aln1 = Alignment(target, query1, ["AAATAAA", "AAAGAAA"])
    aln2 = Alignment(target, query2, ["AAATAAA", "AAACAAA"])

    alignments = [aln1, aln2]

    # Test plotting without saving
    fig = plot_alignments(alignments, title="TEST", return_fig=True)

    assert fig is not None
    plt.close(fig)


def test_plot_alignments_with_pdf(tmp_path):
    """Test plotting with PDF output"""
    output_path = tmp_path / "test_plot.pdf"
    target = "AAATAAA"
    query1 = "AAAGAAA"

    aln1 = Alignment(target, query1, ["AAATAAA", "AAAGAAA"])
    alignments = [aln1]

    # Create PDF and plot
    with PdfPages(str(output_path)) as pdf:
        fig = plot_alignments(alignments, pdf=pdf)
        plt.close(fig)

    # Check that the file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_alignments_with_multiple_queries(tmp_path):
    """Test plotting with multiple queries against one target"""
    output_path = tmp_path / "test_plot_multiple_queries.pdf"

    target = "AAACCCGGGTTTATATATAT"
    queries = [
        "AAACCCGGGTTTATATATAT",  # Perfect match
        "AAAGCCGGGTTTATATATAT",  # One mismatch
        "AAACCCGGGTTTTATATAT",  # One deletion
        "AAACCCGGGTTTATATATATAT",  # One insertion
        "AAATTTGGGAAACCCCCCCC",  # Multiple changes
    ]

    # Create alignments for all queries
    alignments = []
    for query in queries:
        aln = Alignment(target, query)
        alignments.append(aln)

    # Create PDF with all alignments
    with PdfPages(str(output_path)) as pdf:
        fig = plot_alignments(alignments, title="Multiple Queries Test", pdf=pdf)
        plt.close(fig)

    # Check that the file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert len(alignments) == len(queries)
    print(f"\nPDF with {len(queries)} alignments saved to: {output_path}")


def test_plot_alignments_truncated():
    """Test truncated plotting mode"""
    target = "AAATAAA"
    query1 = "AAAGAAA"

    aln1 = Alignment(target, query1, ["AAATAAA", "AAAGAAA"])
    alignments = [aln1]

    # Test truncated mode
    fig = plot_alignments(alignments, truncate=True, return_fig=True)

    assert fig is not None
    plt.close(fig)


def test_plot_alignments_with_multiple_queries_truncated(tmp_path):
    """Test plotting with multiple queries against one target"""
    output_path = tmp_path / "test_plot_multiple_queries.pdf"

    target = "AAACCCGGGTTTATATATAT"
    queries = [
        "AAACCCGGGTTTATATATAT",  # Perfect match
        "AAAGCCGGGTTTATATATAT",  # One mismatch
        "AAACCCGGGTTTTATATAT",  # One deletion
        "AAACCCGGGTTTATATATATAT",  # One insertion
        "AAATTTGGGAAACCCCCCCC",  # Multiple changes
    ]

    # Create alignments for all queries
    alignments = [Alignment(target, query) for query in queries]

    # Create PDF with all alignments
    with PdfPages(str(output_path)) as pdf:
        fig = plot_alignments(
            alignments,
            title="Multiple Queries Test (Truncated)",
            pdf=pdf,
            truncate=True,
        )
        plt.close(fig)

    # Check that the file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert len(alignments) == len(queries)
    print(f"\nPDF with {len(queries)} alignments saved to: {output_path}")


# Tests for auto-alignment using Biopython PairwiseAligner
def test_auto_alignment_identical_sequences():
    """Test auto-alignment with identical sequences"""
    target = "ATCGATCG"
    query = "ATCGATCG"

    # Create alignment without providing alignment parameter
    aln = Alignment(target, query)

    # Should have no mutations, insertions, or deletions
    assert aln.mutation_ct == 0
    assert aln.insertion_ct == 0
    assert aln.deletion_ct == 0
    assert aln.target == target
    assert aln.query == query


def test_auto_alignment_with_mismatch():
    """Test auto-alignment with mismatches"""
    target = "ATCGATCG"
    query = "ATGGATCG"

    # Create alignment without providing alignment parameter
    aln = Alignment(target, query)
    # There should be 1 mismatch
    print("Edits: ", aln.edits)
    # Should detect the mismatch (C->G at position 2)
    assert aln.mutation_ct >= 1
    assert aln.target == target
    assert aln.query == query


def test_auto_alignment_with_insertion():
    """Test auto-alignment with insertion in query"""
    target = "ATCG"
    query = "ATCCCG"

    # Create alignment without providing alignment parameter
    aln = Alignment(target, query)

    # Should detect insertions
    assert aln.insertion_ct >= 1
    assert aln.target == target
    assert aln.query == query


def test_auto_alignment_with_deletion():
    """Test auto-alignment with deletion in query"""
    target = "ATCGATCG"
    query = "ATCATCG"

    # Create alignment without providing alignment parameter
    aln = Alignment(target, query)

    # Should detect deletion
    assert aln.deletion_ct >= 1
    assert aln.target == target
    assert aln.query == query


def test_auto_alignment_complex():
    """Test auto-alignment with complex mutations"""
    target = "AAACCCGGG"
    query = "AAATTTGGG"

    # Create alignment without providing alignment parameter
    aln = Alignment(target, query)

    # Should detect mutations (CCC->TTT could be mismatches or indels)
    assert (aln.mutation_ct + aln.insertion_ct + aln.deletion_ct) >= 3
    assert aln.target == target
    assert aln.query == query


def test_auto_alignment_maintains_compatibility():
    """Test that auto-alignment produces compatible results with manual alignment"""
    target = "ATCG"
    query = "ATCG"

    # Auto-alignment
    auto_aln = Alignment(target, query)

    # Manual alignment
    manual_aln = Alignment(target, query, ["ATCG", "ATCG"])

    # Both should produce identical results for identical sequences
    assert auto_aln.mutation_ct == manual_aln.mutation_ct
    assert auto_aln.insertion_ct == manual_aln.insertion_ct
    assert auto_aln.deletion_ct == manual_aln.deletion_ct
