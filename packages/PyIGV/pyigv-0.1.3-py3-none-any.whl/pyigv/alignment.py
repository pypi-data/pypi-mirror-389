import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap
from typing import Sequence, Optional
from Bio import Align

mismatch_colors = {"A": "green", "T": "red", "G": "gold", "C": "blue"}


class Alignment:
    def block_indices(self, edits):
        if not edits:
            return

        start = 0
        current_type = edits[0]

        for i, t in enumerate(edits):
            if t != current_type:
                # Yield the current block [start, i) and its type.
                yield start, i, current_type
                # Reset the block.
                start = i
                current_type = t
            # Yield the final block.
        yield start, len(edits), current_type

    # input alignment is an array-like object with two strings of the form "(Σ∪{-})*"
    # if alignment is None, uses Biopython PairwiseAligner to generate alignment
    def __init__(
        self,
        target: str,
        query: str,
        alignment: Optional[Sequence[str]] = None,
    ):
        # If alignment is None, generate alignment using Biopython PairwiseAligner
        if alignment is None:
            aligner = Align.PairwiseAligner()
            # Set gap penalties to encourage keeping insertions/deletions adjacent
            # Gap opening is more costly than gap extension
            alignments = aligner.align(target, query)
            # Get the first (best) alignment
            alignment = alignments[0]

        self.target_alignment = alignment[0]
        self.query_alignment = alignment[1]
        self.query = query
        self.target = target

        # target and query base
        symbols = []
        edits = []
        for target_base, query_base in zip(alignment[0], alignment[1]):
            if target_base == query_base:
                symbols.append(target_base)
                edits.append(" ")  # match
            elif target_base == "-":
                symbols.append(query_base)
                edits.append("I")
            elif query_base == "-":
                symbols.append(" ")
                edits.append("D")
            else:
                # Mismatch (substitution)
                symbols.append(query_base)
                edits.append("M")

        # merge adjacent insertions and deletions

        # create generator of type block indices
        writeIdx = 0
        prev_start = 0
        prev_end = 0
        prev_type = "C"
        for start, end, type in self.block_indices(edits):
            if (type == "I" and prev_type == "D") or (type == "D" and prev_type == "I"):
                prev_length = prev_end - prev_start
                curr_length = end - start
                merge_length = min(prev_length, curr_length)
                for j in range(prev_start, prev_end - merge_length):
                    symbols[writeIdx] = symbols[j]
                    edits[writeIdx] = edits[j]
                    writeIdx += 1

                if prev_type == "I":
                    for j in range(prev_end - merge_length, prev_end):
                        symbols[writeIdx] = symbols[j]
                        edits[writeIdx] = "M"
                        writeIdx += 1
                else:
                    for k in range(merge_length):
                        symbols[writeIdx] = symbols[start + k]
                        edits[writeIdx] = "M"
                        writeIdx += 1

                prev_start = start + merge_length
                prev_end = end
                prev_type = type

            else:
                for j in range(prev_start, prev_end):
                    symbols[writeIdx] = symbols[j]
                    edits[writeIdx] = edits[j]
                    writeIdx += 1
                prev_start = start
                prev_end = end
                prev_type = type

        for j in range(prev_start, prev_end):
            symbols[writeIdx] = symbols[j]
            edits[writeIdx] = edits[j]
            writeIdx += 1

        self.symbols = symbols[:writeIdx]
        self.edits = edits[:writeIdx]

        # find edits/errors
        self.insertion_ct = sum(1 for c in self.edits if c == "I")
        self.deletion_ct = sum(1 for c in self.edits if c == "D")
        self.mutation_ct = sum(1 for c in self.edits if c == "M")

    def __str__(self):
        return (
            "Target: "
            + self.target
            + "\n"
            + " Query: "
            + "".join(self.symbols)
            + "\n"
            + " Edits: "
            + "".join(self.edits)
        )

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return [self.insertion_ct, self.mutation_ct, self.deletion_ct] < [
            other.insertion_ct,
            other.mutation_ct,
            other.deletion_ct,
        ]

    def get_color_row(self, truncate: bool = False):
        if truncate:
            return [
                (
                    mismatch_colors.get(symbol, "gray")
                    if edit == "M"
                    else ("gray" if edit == " " else "white")
                )
                for symbol, edit in zip(self.symbols, self.edits)
                if edit != "I"
            ]

        return [
            (
                mismatch_colors.get(symbol, "gray")
                if (edit == "I" or edit == "M")
                else ("gray" if edit == " " else "white")
            )
            for symbol, edit in zip(self.symbols, self.edits)
        ]

    def get_symbols(self, truncate: bool = False):
        if truncate:
            return [
                symbol for symbol, edit in zip(self.symbols, self.edits) if edit != "I"
            ]
        return self.symbols

    # returns start index of all insertion regions
    def get_insertion_indices(self):
        curr_insert_ct = 0
        indices = []
        for start, end, edit in self.block_indices(self.edits):
            if edit == "I":
                indices.append([start - curr_insert_ct, end - start])
                curr_insert_ct += end - start
        return indices


# alignments should be of type alignment
def plot_alignments(
    alignments,
    title: Optional[str] = None,
    pdf: Optional[str] = None,
    truncate: bool = True,
    return_fig: bool = False,
) -> Optional[plt.Figure]:
    alignments.sort()

    expected_ref = alignments[0].target
    expected_len = len(expected_ref)

    n_rows = len(alignments)
    alignment_length = (
        len(expected_ref)
        if truncate
        else max((len(aln.symbols) for aln in alignments), default=0)
    )

    color_rows = []
    text_rows = []

    # Create expected reference row (top row)
    top_color_row = [mismatch_colors.get(base, "gray") for base in expected_ref] + [
        "white"
    ] * (alignment_length - expected_len)
    top_text_row = list(expected_ref) + [" "] * (alignment_length - expected_len)

    # Standardize row length
    def pad_row(row, length, fill="white"):
        return row + [fill] * (length - len(row))

    color_rows = [pad_row(top_color_row, alignment_length)] + [
        pad_row(aln.get_color_row(truncate), alignment_length) for aln in alignments
    ]
    text_rows = [pad_row(top_text_row, alignment_length, " ")] + [
        pad_row(aln.get_symbols(truncate), alignment_length, " ") for aln in alignments
    ]

    # Convert colors to numeric indices for matshow
    colors_list = ["green", "red", "gold", "blue", "gray", "white"]
    color_to_index = {color: idx for idx, color in enumerate(colors_list)}
    color_matrix = np.array(
        [[color_to_index.get(color, 0) for color in row] for row in color_rows]
    )
    text_matrix = text_rows  # already a list of lists

    # print("Color_matrix\n", color_matrix)
    # print("text_matrix\n", text_matrix)
    # Plot
    fig_width = max(10, alignment_length * 0.3)
    fig_height = max(2, (n_rows + 1) * 0.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.matshow(color_matrix, cmap=ListedColormap(colors_list))

    # Add text
    for i in range(len(text_matrix)):
        if i > 0 and truncate:
            insert_indices = alignments[i - 1].get_insertion_indices()
            for j, insert_length in insert_indices:
                ax.text(
                    j - 0.5,
                    i,
                    f"{insert_length}",
                    va="center",
                    ha="center",
                    fontsize=8,
                    color="white",
                    bbox=dict(
                        facecolor="purple", edgecolor="none", boxstyle="round,pad=0.2"
                    ),
                )
        for j in range(alignment_length):
            c = text_matrix[i][j]
            if c:
                ax.text(j, i, c, va="center", ha="center", fontsize=8)

    ax.set_xticks([])
    ax.set_yticks([])

    # Add title

    if title:
        plot_title = f"{title} | Alignments: {n_rows}"
    else:
        plot_title = f"Alignments: {n_rows}"

    ax.set_title(
        plot_title,
        fontsize=14,
        pad=10,
    )
    plt.tight_layout()

    if pdf:
        pdf.savefig()
    else:
        plt.show()

    if return_fig:
        return fig
    
    return None
