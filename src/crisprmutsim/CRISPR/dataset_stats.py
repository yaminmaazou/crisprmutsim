from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal, Self

from crisprmutsim.CRISPR.crispr_array import CRISPRArray


@dataclass
class DatasetStats:
    reference: Literal["consensus", "proximal", "distal"] = "consensus"
    max_array_length: int = 0
    max_repeat_length: int = 0
    total_arrays: int = 0

    # normalized
    array_length_distribution: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    repeat_length_distribution: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    mutation_count_distribution: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    cas_type_distribution: dict[str, float] = field(default_factory=dict[str, float])

    # absolute
    array_length_distribution_abs: dict[int, int] = field(
        default_factory=dict[int, int]
    )
    repeat_length_distribution_abs: dict[int, int] = field(
        default_factory=dict[int, int]
    )
    mutation_count_distribution_abs: dict[int, int] = field(
        default_factory=dict[int, int]
    )
    cas_type_distribution_abs: dict[str, int] = field(default_factory=dict[str, int])

    # means
    mean_array_length: float = 0.0
    mean_repeat_length: float = 0.0
    mean_mutations_per_array: float = 0.0

    pattern_counts: dict[int, float] = field(
        default_factory=lambda: {i: 0.0 for i in range(7)}
    )  # [0] = none, [1-6] = patterns 1-6
    pattern_counts_by_cas_type: dict[str, dict[int, float]] = field(
        default_factory=dict[str, dict[int, float]]
    )

    # [repeat][base]
    mutation_matrix: list[list[float]] = field(default_factory=list[list[float]])
    mutation_matrix_from_distal: list[list[float]] = field(
        default_factory=list[list[float]]
    )

    # accumulated
    mutations_per_repeat_position: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    # "normalized" here means normalized by number of arrays that have that repeat position
    mutations_per_repeat_normalized: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    mutations_per_base_position: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    mutations_per_repeat_position_from_distal: dict[int, float] = field(
        default_factory=dict[int, float]
    )
    mutations_per_base_position_from_distal: dict[int, float] = field(
        default_factory=dict[int, float]
    )

    @classmethod
    def from_arrays(
        cls,
        arrays: list[CRISPRArray],
        reference: Literal["consensus", "proximal", "distal"] = "consensus",
        mut_per_base_range: tuple[int, int] = (0, 0),
        mut_per_base_distal_range: tuple[int, int] = (0, 0),
    ) -> Self:
        if not arrays:
            return cls(reference=reference)

        max_array_length = max(arr.repeat_stats.array_length for arr in arrays)
        max_repeat_length = max(arr.repeat_stats.repeat_length for arr in arrays)
        total_arrays = len(arrays)

        array_length_dist: dict[int, int] = defaultdict(int)
        repeat_length_dist: dict[int, int] = defaultdict(int)
        mutation_count_dist: dict[int, int] = defaultdict(int)
        cas_type_dist: dict[str, int] = defaultdict(int)

        pattern_counts = {i: 0 for i in range(7)}
        pattern_counts_by_cas_type: dict[str, dict[int, int]] = {}

        mutation_matrix = [
            [0.0 for _ in range(max_repeat_length)] for _ in range(max_array_length)
        ]
        mutation_matrix_from_distal = [
            [0.0 for _ in range(max_repeat_length)] for _ in range(max_array_length)
        ]

        mutations_per_repeat: dict[int, int] = defaultdict(int)
        mutations_per_repeat_normalized: dict[int, float] = defaultdict(float)
        mutations_per_base: dict[int, int] = defaultdict(int)
        mutations_per_repeat_from_distal: dict[int, int] = defaultdict(int)
        mutations_per_base_from_distal: dict[int, int] = defaultdict(int)

        for array in arrays:
            stats = array.repeat_stats

            if reference == "consensus":
                mutation_diff = stats.mutation_diff_consensus
                mutation_count = stats.mutation_count_consensus
            elif reference == "proximal":
                mutation_diff = stats.mutation_diff_proximal
                mutation_count = stats.mutation_count_proximal
            else:
                mutation_diff = stats.mutation_diff_distal
                mutation_count = stats.mutation_count_distal

            array_length_dist[stats.array_length] += 1
            repeat_length_dist[stats.repeat_length] += 1
            mutation_count_dist[mutation_count] += 1
            cas_type_dist[array.cas_type] += 1

            if array.cas_type not in pattern_counts_by_cas_type.keys():
                pattern_counts_by_cas_type[array.cas_type] = {i: 0 for i in range(7)}
            for i in stats.patterns:
                pattern_counts[i] += 1
                pattern_counts_by_cas_type[array.cas_type][i] += 1
            if len(stats.patterns) == 0:
                pattern_counts[0] += 1
                pattern_counts_by_cas_type[array.cas_type][0] += 1

            for mutation in mutation_diff:
                repeat_idx = mutation["repeat_index"]
                base_idx = mutation["base_index"]
                repeat_idx_from_distal = stats.array_length - 1 - repeat_idx
                base_idx_from_distal = stats.repeat_length - 1 - base_idx

                mutation_matrix[repeat_idx][base_idx] += 1
                mutation_matrix_from_distal[repeat_idx_from_distal][
                    base_idx_from_distal
                ] += 1

                mutations_per_repeat[repeat_idx] += 1
                mutations_per_repeat_from_distal[repeat_idx_from_distal] += 1
                if mut_per_base_range[0] <= repeat_idx <= mut_per_base_range[1]:
                    mutations_per_base[base_idx] += 1
                if (
                    mut_per_base_distal_range[0]
                    <= repeat_idx_from_distal
                    <= mut_per_base_distal_range[1]
                ):
                    mutations_per_base_from_distal[base_idx_from_distal] += 1

        mutations_per_repeat_normalized = {
            repeat_idx: mutations_per_repeat[repeat_idx]
            / sum(
                count
                for length, count in array_length_dist.items()
                if length > repeat_idx
            )
            for repeat_idx in mutations_per_repeat
        }

        # means
        mean_array_length = (
            sum(length * count for length, count in array_length_dist.items())
            / total_arrays
        )
        mean_repeat_length = (
            sum(length * count for length, count in repeat_length_dist.items())
            / total_arrays
        )
        mean_mutations_per_array = (
            sum(mutations * count for mutations, count in mutation_count_dist.items())
            / total_arrays
        )

        # normalize all
        array_length_dist_norm = {
            k: v / total_arrays for k, v in array_length_dist.items()
        }
        repeat_length_dist_norm = {
            k: v / total_arrays for k, v in repeat_length_dist.items()
        }
        mutation_count_dist_norm = {
            k: v / total_arrays for k, v in mutation_count_dist.items()
        }
        cas_type_dist_norm = {k: v / total_arrays for k, v in cas_type_dist.items()}

        pattern_counts_norm = {k: v / total_arrays for k, v in pattern_counts.items()}
        pattern_counts_by_cas_type_norm = {
            cas_type: {k: v / total_arrays for k, v in counts.items()}
            for cas_type, counts in pattern_counts_by_cas_type.items()
        }

        mutation_matrix_norm = [
            [count / total_arrays for count in row] for row in mutation_matrix
        ]
        mutation_matrix_from_distal_norm = [
            [count / total_arrays for count in row]
            for row in mutation_matrix_from_distal
        ]

        mutations_per_repeat_norm = {
            k: v / total_arrays for k, v in mutations_per_repeat.items()
        }
        mutations_per_base_norm = {
            k: v / total_arrays for k, v in mutations_per_base.items()
        }
        mutations_per_repeat_from_distal_norm = {
            k: v / total_arrays for k, v in mutations_per_repeat_from_distal.items()
        }
        mutations_per_base_from_distal_norm = {
            k: v / total_arrays for k, v in mutations_per_base_from_distal.items()
        }

        return cls(
            reference=reference,
            max_array_length=max_array_length,
            max_repeat_length=max_repeat_length,
            total_arrays=total_arrays,
            array_length_distribution=array_length_dist_norm,
            repeat_length_distribution=repeat_length_dist_norm,
            mutation_count_distribution=mutation_count_dist_norm,
            cas_type_distribution=cas_type_dist_norm,
            array_length_distribution_abs=dict(array_length_dist),
            repeat_length_distribution_abs=dict(repeat_length_dist),
            mutation_count_distribution_abs=dict(mutation_count_dist),
            cas_type_distribution_abs=dict(cas_type_dist),
            mean_array_length=mean_array_length,
            mean_repeat_length=mean_repeat_length,
            mean_mutations_per_array=mean_mutations_per_array,
            pattern_counts=pattern_counts_norm,
            pattern_counts_by_cas_type=pattern_counts_by_cas_type_norm,
            mutation_matrix=mutation_matrix_norm,
            mutation_matrix_from_distal=mutation_matrix_from_distal_norm,
            mutations_per_repeat_position=mutations_per_repeat_norm,
            mutations_per_repeat_normalized=mutations_per_repeat_normalized,
            mutations_per_base_position=mutations_per_base_norm,
            mutations_per_repeat_position_from_distal=mutations_per_repeat_from_distal_norm,
            mutations_per_base_position_from_distal=mutations_per_base_from_distal_norm,
        )
