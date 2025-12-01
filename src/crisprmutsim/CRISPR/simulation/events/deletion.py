from random import Random
from typing import NotRequired, TypedDict, TYPE_CHECKING

from crisprmutsim.helpers import geometric_mean_alpha

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    CRISPREvent,
    CRISPREventGenerator,
)


class DeletionParameters(TypedDict):
    leader_offset: NotRequired[int]  # repeats protected from deletion
    distal_offset: NotRequired[int]  # .
    split_offset: NotRequired[int]  # default -1 = no splits
    mean_block_deletion_length: NotRequired[float]  # SpacerPlacer "alpha"


class DeletionActions(TypedDict):
    repeat_index: int
    split_index: NotRequired[int]  # default -1
    block_deletion_length: NotRequired[int]  # default 1


class Deletion(CRISPREvent[DeletionActions]): ...


class DeletionGenerator(CRISPREventGenerator[DeletionParameters, Deletion]):

    def _verify_parameters(self) -> None:
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)
        split_offset = self.parameters.get("split_offset", -1)
        mean_block_deletion_length = self.parameters.get(
            "mean_block_deletion_length", 1.0
        )

        if leader_offset < 0:
            raise ValueError(f"leader_offset must be non-negative")
        if distal_offset < 0:
            raise ValueError(f"distal_offset must be non-negative")
        if split_offset < -1:
            raise ValueError(f"split_offset must be >= -1")
        if mean_block_deletion_length < 1.0:
            raise ValueError(f"mean_block_deletion_length must be at least 1.0")

    def rate(self, current_time: float, obj: "RawCRISPRArray") -> float:
        array_len = len(obj)
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)

        if array_len - distal_offset - 2 <= leader_offset:
            return 0.0

        return super().rate(current_time, obj)

    def generate(
        self, rng: Random, current_time: float, obj: "RawCRISPRArray"
    ) -> Deletion:
        array_len = len(obj)
        leader_offset = self.parameters.get("leader_offset", 0)
        distal_offset = self.parameters.get("distal_offset", 0)
        split_offset = self.parameters.get("split_offset", -1)
        mean_block_deletion_length = self.parameters.get(
            "mean_block_deletion_length", 1.0
        )

        repeat_idx = rng.randint(leader_offset, array_len - distal_offset - 2)

        split_idx = -1
        if split_offset >= 0:
            repeat_len = len(obj[repeat_idx])
            if split_offset <= repeat_len - 1:
                split_idx = rng.randint(split_offset, repeat_len - 1)

        if split_idx >= 0:
            max_block_deletion_length = array_len - repeat_idx - distal_offset - 1
        else:
            max_block_deletion_length = array_len - repeat_idx - distal_offset

        block_len = geometric_mean_alpha(rng, mean_block_deletion_length)
        block_len = min(block_len, max_block_deletion_length)

        return Deletion(
            current_time,
            {
                "repeat_index": repeat_idx,
                "split_index": split_idx,
                "block_deletion_length": block_len,
            },
        )


# picklable callable, for multithreading
class DeletionRateConverter:
    def __init__(self, deletion_rate_per_repeat: float):
        self.deletion_rate_per_repeat = deletion_rate_per_repeat

    def __call__(self, current_time: float, obj: "RawCRISPRArray") -> float:
        if not obj or len(obj) < 1:
            return 0.0

        return self.deletion_rate_per_repeat * len(obj)
