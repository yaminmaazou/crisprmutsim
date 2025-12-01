from random import Random
from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    CRISPREvent,
    CRISPREventGenerator,
)


class MutationParameters(TypedDict):
    allow_same_base: NotRequired[bool]  # default false


class MutationActions(TypedDict):
    repeat_index: int
    base_index: int
    new_base: str


class Mutation(CRISPREvent[MutationActions]): ...


class MutationGenerator(CRISPREventGenerator[MutationParameters, Mutation]):
    def generate(
        self, rng: Random, current_time: float, obj: "RawCRISPRArray"
    ) -> Mutation:
        allow_same_base = self.parameters.get("allow_same_base", False)

        repeat_idx = rng.randint(0, len(obj) - 1)
        repeat = obj[repeat_idx]
        base_idx = rng.randint(0, len(repeat) - 1)
        choice = "ACGT" if allow_same_base else "ACGT".replace(repeat[base_idx], "")
        base = rng.choice(choice)
        return Mutation(
            current_time,
            {"repeat_index": repeat_idx, "base_index": base_idx, "new_base": base},
        )


# picklable callable, for multithreading
class MutationRateConverter:

    def __init__(self, mutation_rate_per_base: float):
        self.mutation_rate_per_base = mutation_rate_per_base

    def __call__(self, current_time: float, obj: "RawCRISPRArray") -> float:
        if not obj or not obj[0]:
            return 0.0
        return self.mutation_rate_per_base * len(obj) * len(obj[0])
