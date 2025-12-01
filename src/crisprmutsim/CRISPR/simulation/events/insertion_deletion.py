from random import Random
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    CRISPREvent,
    CRISPREventGenerator,
)


class InsertionDeletionParameters(TypedDict):
    insertion_anchor: Literal["proximal", "distal"]
    insertion_randomize: Literal["none", "uniform", "exponential"]
    insertion_exp_lambda_factor: NotRequired[float]  # defaults to 0.1
    leader_offset: NotRequired[int]  # repeats protected from deletion
    distal_offset: NotRequired[int]  # .
    split_offset: NotRequired[int]  # < 0 means no splits, default -1


class InsertionDeletionActions(TypedDict):
    copy_index: int
    insertion_index: int
    deletion_repeat_index: int
    deletion_split_index: NotRequired[int]  # default -1


class InsertionDeletion(CRISPREvent[InsertionDeletionActions]): ...


class InsertionDeletionGenerator(
    CRISPREventGenerator[InsertionDeletionParameters, InsertionDeletion]
):

    def _verify_parameters(self) -> None:
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)
        split_offset = self.parameters.get("split_offset", -1)

        if leader_offset < 0:
            raise ValueError(f"leader_offset must be >= 0, got {leader_offset}")
        if distal_offset < 0:
            raise ValueError(f"distal_offset must be >= 0, got {distal_offset}")
        if split_offset < -1:
            raise ValueError(f"split_offset must be >= -1, got {split_offset}")

    def rate(self, current_time: float, obj: "RawCRISPRArray") -> float:
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)

        if leader_offset + distal_offset >= len(obj):
            return 0.0

        return super().rate(current_time, obj)

    def generate(
        self, rng: Random, current_time: float, obj: "RawCRISPRArray"
    ) -> InsertionDeletion:
        array_len = len(obj)
        insertion_anchor = self.parameters.get("insertion_anchor", "proximal")
        insertion_randomize = self.parameters.get("insertion_randomize", "none")
        insertion_exp_lambda_factor = self.parameters.get(
            "insertion_exp_lambda_factor", 0.1
        )
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)
        split_offset = self.parameters.get("split_offset", -1)

        if insertion_randomize == "none":
            if insertion_anchor == "proximal":
                insertion_index = 0
            else:  # distal
                insertion_index = len(obj)
        elif insertion_randomize == "uniform":
            if insertion_anchor == "proximal":
                insertion_index = rng.randint(0, len(obj) - 1)
            else:  # distal
                insertion_index = rng.randint(1, len(obj))
        else:  # exponential
            distance = int(rng.expovariate(insertion_exp_lambda_factor * len(obj)))

            if insertion_anchor == "proximal":
                insertion_index = min(distance, len(obj) - 1)
            else:  # distal
                insertion_index = max(1, len(obj) - distance)

        copy_index = (
            insertion_index if insertion_anchor == "proximal" else insertion_index - 1
        )

        repeat_idx = rng.randint(leader_offset, array_len - distal_offset - 2)

        split_idx = -1
        if split_offset >= 0:
            repeat_len = len(obj[repeat_idx])
            if split_offset <= repeat_len - 1:
                split_idx = rng.randint(split_offset, repeat_len - 1)

        return InsertionDeletion(
            current_time,
            {
                "insertion_index": insertion_index,
                "copy_index": copy_index,
                "deletion_repeat_index": repeat_idx,
                "deletion_split_index": split_idx,
            },
        )


# picklable callable, for multithreading
class InsertionDeletionRateConverter:
    def __init__(self, indel_rate_per_repeat: float):
        self.indel_rate_per_repeat = indel_rate_per_repeat

    def __call__(self, current_time: float, obj: "RawCRISPRArray") -> float:
        if not obj or len(obj) < 1:
            return 0.0
        return self.indel_rate_per_repeat * len(obj)
