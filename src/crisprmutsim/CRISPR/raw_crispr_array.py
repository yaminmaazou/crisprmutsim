from collections.abc import Iterable, Iterator, MutableSequence
from dataclasses import dataclass
import json
import random
import sqlite3
from typing import Self, cast, overload

from crisprmutsim.CRISPR.array_stats import ArrayStats
from crisprmutsim.CRISPR.dna_sequence import DNASequence, IUPAC_BASES
from crisprmutsim.CRISPR.simulation.events.crispr_event import ICRISPREvent
from crisprmutsim.CRISPR.simulation.events.deletion import Deletion, DeletionActions
from crisprmutsim.CRISPR.simulation.events.insertion import Insertion, InsertionActions
from crisprmutsim.CRISPR.simulation.events.insertion_deletion import (
    InsertionDeletion,
    InsertionDeletionActions,
)
from crisprmutsim.CRISPR.simulation.events.mutation import Mutation, MutationActions


@dataclass
class RawCRISPRArray(MutableSequence[DNASequence]):
    """
    A class to represent repeat sequences in a CRISPR array.
    """

    def __init__(
        self, repeat_sequences: Iterable[Iterable[str]], unsafe: bool = False
    ) -> None:
        if isinstance(repeat_sequences, str) or isinstance(
            repeat_sequences, DNASequence
        ):
            repeat_sequences = [repeat_sequences]
            # elif all((isinstance(seq, str) and len(seq) == 1) for seq in repeat_sequences):
            #   # TODO
            #   warnings.warn(
            #     f"{'\033[93m'}Interpreting {repeat_sequences} as a list of single-base repeats. " +
            #     f"If this is not intended, please use Repeat() or a single string.{'\033[0m'}",
            #     Warning,
            #     stacklevel=3
            #   )

        self.repeat_sequences: list[DNASequence] = [
            DNASequence(seq, unsafe=unsafe) for seq in repeat_sequences
        ]

    @classmethod
    def from_json(cls, json_str: str) -> "RawCRISPRArray":
        repeat_sequences = json.loads(json_str)
        return cls(repeat_sequences)

    @classmethod
    def from_array_stats(cls, stats: ArrayStats) -> "RawCRISPRArray":
        repeat_sequences: list[DNASequence] = [
            DNASequence(stats.consensus_repeat) for _ in range(stats.array_length)
        ]
        for diff in stats.mutation_diff_consensus:
            repeat_sequences[diff["repeat_index"]].__unsafe_setitem__(
                diff["base_index"], diff["new_base"]
            )

        return cls(repeat_sequences)

    def to_json(self) -> str:
        # list of strings
        return json.dumps([str(repeat) for repeat in self])

    def consensus(self) -> DNASequence:
        array_length = len(self)
        if array_length == 0:
            return DNASequence([])
        repeat_length = len(self[0])
        consensus: list[str] = [""] * repeat_length

        for j in range(repeat_length):
            counts: dict[str, int] = {base: 0 for base in IUPAC_BASES}
            for i in range(array_length):
                base = self[i][j]
                counts[base] = counts[base] + 1

            max_count = max(counts.values())

            # all bases with max_count
            most_frequent = [
                base for base, count in counts.items() if count == max_count
            ]

            # random select if tie
            consensus[j] = random.choice(most_frequent)

        return DNASequence(consensus, unsafe=True)

    # combined method for all stats at once, to avoid multiple loops
    def all_stats(
        self, min_line_length: int = 3, max_gap_length: int = 5
    ) -> ArrayStats:
        array_length = len(self)
        if array_length == 0:
            return ArrayStats.empty()
        repeat_length = len(self[0])
        mutation_diff_consensus: list[MutationActions] = []
        mutation_diff_proximal: list[MutationActions] = []
        mutation_diff_distal: list[MutationActions] = []
        mutation_count_consensus = 0
        mutation_count_proximal = 0
        mutation_count_distal = 0
        patterns: set[int] = set()

        consensus = self.consensus()

        for j in range(repeat_length):
            mismatch_lines: list[tuple[int, int]] = []  # (start_index, length)
            i = 0
            while i < array_length:
                while i < array_length and self[i][j] == consensus[j]:
                    if self[i][j] != self[0][j]:
                        mutation_diff_proximal.append(
                            {"repeat_index": i, "base_index": j, "new_base": self[i][j]}
                        )
                        mutation_count_proximal += 1
                    if self[i][j] != self[-1][j]:
                        mutation_diff_distal.append(
                            {"repeat_index": i, "base_index": j, "new_base": self[i][j]}
                        )
                        mutation_count_distal += 1
                    i += 1
                if i == array_length:
                    break
                # count a line
                line_start_idx = i
                while i < array_length and self[i][j] != consensus[j]:
                    mutation_diff_consensus.append(
                        {"repeat_index": i, "base_index": j, "new_base": self[i][j]}
                    )
                    mutation_count_consensus += 1
                    if self[i][j] != self[0][j]:
                        mutation_diff_proximal.append(
                            {"repeat_index": i, "base_index": j, "new_base": self[i][j]}
                        )
                        mutation_count_proximal += 1
                    if self[i][j] != self[-1][j]:
                        mutation_diff_distal.append(
                            {"repeat_index": i, "base_index": j, "new_base": self[i][j]}
                        )
                        mutation_count_distal += 1
                    i += 1
                line_length = i - line_start_idx
                mismatch_lines.append((line_start_idx, line_length))

            # split mismatch_lines into groups separated by large gaps;
            #    each group represents an independent pattern
            groups: list[list[tuple[int, int]]] = []
            if len(mismatch_lines) > 0:
                current_group: list[tuple[int, int]] = [mismatch_lines[0]]

                for k in range(1, len(mismatch_lines)):
                    prev_start, prev_length = current_group[-1]
                    curr_start, _ = mismatch_lines[k]
                    gap = curr_start - (prev_start + prev_length)

                    if gap <= max_gap_length:
                        current_group.append(mismatch_lines[k])
                    else:
                        # gap too large, save current group and start a new one
                        groups.append(current_group)
                        current_group = [mismatch_lines[k]]

                groups.append(current_group)

            # check each group for patterns
            for group in groups:
                if len(group) > 2:  # Dotted pattern (Pattern 4 or 5)
                    if j == 0:
                        patterns.add(5)  # Dotted at first column (Pattern 5)
                    elif j == repeat_length - 1:
                        patterns.add(6)  # Pattern 5 at last column
                    else:
                        patterns.add(4)  # Pattern 4
                elif len(group) == 2:  # Split Line (Pattern 3)
                    # at least one line must be long enough
                    if any(line[1] >= min_line_length for line in group):
                        patterns.add(3)
                elif len(group) == 1:  # one Line
                    start_idx, length = group[0]
                    if length >= min_line_length:
                        end_idx = start_idx + length - 1
                        # Line: line starts at top or bottom (Pattern 1)
                        if start_idx == 0 or end_idx == array_length - 1:
                            patterns.add(1)
                        else:  # Floating line (2 flips) (Pattern 2)
                            patterns.add(2)

        return ArrayStats(
            consensus_repeat=str(consensus),
            array_length=array_length,
            repeat_length=repeat_length,
            mutation_diff_consensus=mutation_diff_consensus,
            mutation_diff_proximal=mutation_diff_proximal,
            mutation_diff_distal=mutation_diff_distal,
            mutation_count_consensus=mutation_count_consensus,
            mutation_count_proximal=mutation_count_proximal,
            mutation_count_distal=mutation_count_distal,
            patterns=patterns,
        )

    def apply_events(self, events: Iterable[ICRISPREvent]) -> None:
        for event in events:
            if isinstance(event, Mutation):
                self.apply_mutation(event.actions)
            elif isinstance(event, Insertion):
                self.apply_insertion(event.actions)
            elif isinstance(event, Deletion):
                self.apply_deletion(event.actions)
            elif isinstance(event, InsertionDeletion):
                self.apply_insertion_deletion(event.actions)
            else:
                raise NotImplementedError(f"Unknown event type: {type(event)}")

    def apply_mutation(self, actions: MutationActions) -> None:
        if actions["repeat_index"] < 0 or actions["repeat_index"] > len(self) - 1:
            raise IndexError("Repeat index out of bounds.")
        if (
            actions["base_index"] < 0
            or actions["base_index"] > len(self[actions["repeat_index"]]) - 1
        ):
            raise IndexError("Base index out of bounds.")
        self.__unsafe_apply_mutation__(
            actions["repeat_index"], actions["base_index"], actions["new_base"]
        )

    def apply_insertion(self, actions: InsertionActions) -> None:
        copy_index = actions["copy_index"]
        insertion_index = actions["insertion_index"]
        if insertion_index < 0 or insertion_index > len(self):
            raise IndexError("Insertion position out of bounds.")
        self.__unsafe_apply_insertion__(copy_index, insertion_index)

    def apply_deletion(self, actions: DeletionActions) -> None:
        repeat_index = actions["repeat_index"]
        split_index = actions.get("split_index", -1)
        block_length = actions.get("block_deletion_length", 1)

        array_length = len(self)

        if array_length < 1:
            raise ValueError("Cannot delete from an empty array.")
        if repeat_index < 0 or repeat_index > array_length - 1:
            raise IndexError("Repeat index out of bounds.")
        if block_length < 1:
            raise ValueError("Block deletion length must be at least 1.")
        if split_index > len(self[repeat_index]):
            raise IndexError("Split index out of bounds.")

        if split_index < 0:
            if repeat_index + block_length > array_length:
                raise ValueError("Block deletion length exceeds array bounds.")
            self.__unsafe_apply_deletion__(repeat_index, block_length)
        else:
            # split deletion: need to access repeat at repeat_index + block_length
            if repeat_index + block_length > array_length - 1:
                raise IndexError(
                    "Cannot perform split deletion: target repeat index out of bounds."
                )
            self.__unsafe_apply_split_deletion__(
                repeat_index, split_index, block_length
            )

    def apply_insertion_deletion(self, actions: InsertionDeletionActions) -> None:
        copy_index = actions["copy_index"]
        insertion_index = actions["insertion_index"]
        deletion_repeat_index = actions["deletion_repeat_index"]

        self.apply_insertion(
            {"copy_index": copy_index, "insertion_index": insertion_index}
        )

        # shift deletion index if insertion happened before or at the deletion point
        adjusted_deletion_index = (
            deletion_repeat_index + 1
            if deletion_repeat_index >= insertion_index
            else deletion_repeat_index
        )

        self.apply_deletion(
            {
                "repeat_index": adjusted_deletion_index,
                "split_index": actions.get("deletion_split_index", -1),
            }
        )

    #####
    # "Unsafe" event versions; assume all actions are valid, reduce branching
    #####

    def __unsafe_apply_events__(self, events: Iterable[ICRISPREvent]) -> None:
        for event in events:
            if isinstance(event, Mutation):
                self.__unsafe_apply_mutation__(
                    event.actions["repeat_index"],
                    event.actions["base_index"],
                    event.actions["new_base"],
                )
            elif isinstance(event, Insertion):
                self.__unsafe_apply_insertion__(
                    event.actions["copy_index"], event.actions["insertion_index"]
                )
            elif isinstance(event, Deletion):
                repeat_index = event.actions["repeat_index"]
                split_index = event.actions.get("split_index", -1)
                block_length = event.actions.get("block_deletion_length", 1)

                if split_index < 0:
                    self.__unsafe_apply_deletion__(repeat_index, block_length)
                else:
                    self.__unsafe_apply_split_deletion__(
                        repeat_index, split_index, block_length
                    )
            elif isinstance(event, InsertionDeletion):
                copy_index = event.actions["copy_index"]
                insertion_index = event.actions["insertion_index"]
                deletion_repeat_index = event.actions["deletion_repeat_index"]
                deletion_split_index = event.actions.get("deletion_split_index", -1)

                self.__unsafe_apply_insertion__(copy_index, insertion_index)
                # shift deletion index if insertion happened before or at the deletion point
                adjusted_deletion_index = (
                    deletion_repeat_index + 1
                    if deletion_repeat_index >= insertion_index
                    else deletion_repeat_index
                )

                if deletion_split_index >= 0:
                    self.__unsafe_apply_split_deletion__(
                        adjusted_deletion_index, deletion_split_index, 1
                    )
                else:
                    self.__unsafe_apply_deletion__(adjusted_deletion_index, 1)
            else:
                raise NotImplementedError(f"Unknown event type: {type(event)}")

    def __unsafe_apply_mutation__(
        self, repeat_index: int, base_index: int, new_base: str
    ) -> None:
        self.repeat_sequences[repeat_index].__unsafe_setitem__(base_index, new_base)

    def __unsafe_apply_insertion__(self, copy_index: int, insertion_index: int) -> None:
        self.repeat_sequences.insert(insertion_index, DNASequence(self[copy_index]))

    def __unsafe_apply_deletion__(self, repeat_index: int, block_length: int) -> None:
        del self[repeat_index : repeat_index + block_length]

    def __unsafe_apply_split_deletion__(
        self, repeat_index: int, split_index: int, block_length: int
    ) -> None:
        self[repeat_index] = DNASequence(
            self[repeat_index][:split_index]
            + self[repeat_index + block_length][split_index:],
            unsafe=True,
        )
        del self[repeat_index + 1 : repeat_index + block_length + 1]

    # UNUSED
    # def __unsafe_apply_insertion_split_deletion__(
    #     self,
    #     insertion_position: int,
    #     deletion_repeat_index: int,
    #     deletion_split_index: int,
    # ) -> None:
    #     self.__unsafe_apply_insertion__(insertion_position)

    #     # shift deletion index if insertion happened before or at the deletion point
    #     adjusted_deletion_index = (
    #         deletion_repeat_index + 1
    #         if deletion_repeat_index >= insertion_position
    #         else deletion_repeat_index
    #     )

    #     self.__unsafe_apply_split_deletion__(
    #         adjusted_deletion_index, deletion_split_index, 1
    #     )

    # UNUSED
    # branchless
    # def __unsafe_apply_proximal_insertion_split_deletion__(
    #     self,
    #     deletion_repeat_index: int,
    #     deletion_split_index: int,
    # ) -> None:
    #     self.__unsafe_apply_insertion__(0)

    #     self.__unsafe_apply_split_deletion__(
    #         deletion_repeat_index, deletion_split_index, 1
    #     )

    #############################################################################
    # Dunder methods for MutableSequence interface and additional functionality #
    #############################################################################

    @overload
    def __getitem__(self, index: int) -> DNASequence: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[DNASequence]: ...

    def __getitem__(
        self, index: int | slice
    ) -> DNASequence | MutableSequence[DNASequence]:
        return self.repeat_sequences[index]

    @overload
    def __setitem__(self, index: int, value: DNASequence) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[DNASequence]) -> None: ...

    def __setitem__(
        self, index: int | slice, value: DNASequence | Iterable[DNASequence]
    ) -> None:
        if isinstance(value, DNASequence):
            if isinstance(index, slice):
                self.repeat_sequences[index] = [value]
            else:
                self.repeat_sequences[index] = value
        else:
            if isinstance(index, int):
                raise TypeError("Index must be a slice when setting multiple values.")
            else:
                self.repeat_sequences[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: int | slice) -> None:
        del self.repeat_sequences[index]

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, DNASequence):
            if isinstance(value, Iterable):
                value = cast(Iterable[str], value)
                value = DNASequence(value)
            else:
                raise TypeError(f"Invalid type for value: {type(value)}.")
        return value in self.repeat_sequences

    def __len__(self) -> int:
        return len(self.repeat_sequences)

    def insert(self, index: int, value: DNASequence) -> None:
        self.repeat_sequences.insert(index, value)

    def __iter__(self) -> Iterator[DNASequence]:
        return iter(self.repeat_sequences)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RawCRISPRArray):
            if isinstance(other, Iterable):
                other = cast(Iterable[Iterable[str]], other)
                other = RawCRISPRArray(other)
            else:
                return False
        if len(self) != len(other):
            return False
        return all(
            self_seq == other_seq
            for self_seq, other_seq in zip(
                self.repeat_sequences, other.repeat_sequences
            )
        )

    def __hash__(self) -> int:
        return hash(tuple(str(seq) for seq in self.repeat_sequences))

    def __str__(self) -> str:
        return f"{list(map(str, self.repeat_sequences))}"

    def __repr__(self) -> str:
        return self.__str__()

    # Support append and concat using '+'
    def __add__(self, value: Iterable[Iterable[str]]) -> "RawCRISPRArray":
        return RawCRISPRArray(
            self.repeat_sequences + RawCRISPRArray(value).repeat_sequences
        )

    # Override generated mixin method to account for custom __add__ behavior (e.g. strings)
    def __iadd__(self, value: Iterable[Iterable[str]]) -> Self:
        self.repeat_sequences = (self + value).repeat_sequences
        return self

    # Support left insertions using '+'
    def __radd__(self, value: Iterable[Iterable[str]]) -> "RawCRISPRArray":
        return RawCRISPRArray(value) + self

    # sqlite adapter protocol
    def __conform__(self, protocol: type) -> object:
        if protocol is sqlite3.PrepareProtocol:
            return self.to_json()
