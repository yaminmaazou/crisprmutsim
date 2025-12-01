from random import Random
from typing import Literal, NotRequired, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    CRISPREvent,
    CRISPREventGenerator,
)


class InsertionParameters(TypedDict):
    anchor: Literal["proximal", "distal"]
    randomize: Literal["none", "uniform", "exponential"]
    exp_lambda_factor: NotRequired[float]  # defaults to 0.1


class InsertionActions(TypedDict):
    copy_index: int
    insertion_index: int


class Insertion(CRISPREvent[InsertionActions]): ...


class InsertionGenerator(CRISPREventGenerator[InsertionParameters, Insertion]):
    def generate(
        self, rng: Random, current_time: float, obj: "RawCRISPRArray"
    ) -> Insertion:
        anchor = self.parameters.get("anchor", "proximal")
        randomize = self.parameters.get("randomize", "none")
        exp_lambda_factor = self.parameters.get("exp_lambda_factor", 0.1)

        if randomize == "none":
            if anchor == "proximal":
                insertion_index = 0
            else:  # distal
                insertion_index = len(obj)
        elif randomize == "uniform":
            if anchor == "proximal":
                insertion_index = rng.randint(0, len(obj) - 1)
            else:  # distal
                insertion_index = rng.randint(0, len(obj))
        else:  # exponential
            distance = int(rng.expovariate(exp_lambda_factor * len(obj)))

            if anchor == "proximal":
                insertion_index = min(distance, len(obj) - 1)
            else:  # distal
                insertion_index = max(0, len(obj) - distance)

        copy_index = insertion_index if anchor == "proximal" else insertion_index - 1

        return Insertion(
            current_time, {"copy_index": copy_index, "insertion_index": insertion_index}
        )
