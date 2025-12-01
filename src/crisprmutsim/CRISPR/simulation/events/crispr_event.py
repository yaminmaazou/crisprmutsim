from collections.abc import Callable
from random import Random
from typing import TYPE_CHECKING, Literal, Protocol

from crisprmutsim.simulation.event import (
    Event,
    EventActionsType,
    EventParametersType,
    IEvent,
    IEventGenerator,
)

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
    from crisprmutsim.CRISPR.simulation.events.mutation import Mutation
    from crisprmutsim.CRISPR.simulation.events.insertion import Insertion
    from crisprmutsim.CRISPR.simulation.events.deletion import Deletion
    from crisprmutsim.CRISPR.simulation.events.insertion_deletion import (
        InsertionDeletion,
    )


class ICRISPREvent(IEvent, Protocol):
    __crispr_event__: Literal[True]  # phantom type


# thin implementation for inheritance
class CRISPREvent[TEventActions: EventActionsType](Event[TEventActions]):
    __crispr_event__: Literal[True]


class ICRISPREventGenerator[
    TEventParameters: EventParametersType, TIEvent: ICRISPREvent
](IEventGenerator[TEventParameters, TIEvent, "RawCRISPRArray"], Protocol): ...


# thin implementation for inheritance
class CRISPREventGenerator[
    TEventParameters: EventParametersType, TIEvent: ICRISPREvent
]:
    def rate(self, current_time: float, obj: "RawCRISPRArray") -> float:
        if callable(self._rate):
            return self._rate(current_time, obj)
        return self._rate

    def generate(
        self, rng: Random, current_time: float, obj: "RawCRISPRArray"
    ) -> TIEvent: ...

    def __init__(
        self,
        parameters: TEventParameters,
        rate: float | Callable[[float, "RawCRISPRArray"], float],
    ) -> None:
        self.parameters = parameters
        self._rate = rate
        self._verify_parameters()

    def _verify_parameters(self) -> None: ...


def crispr_event_from_tuple(
    data: tuple[str, int, str, float, str],
) -> CRISPREvent[EventActionsType]:
    args = (data[3], data[4])

    match data[2]:
        case "Insertion":
            return Insertion.from_tuple(args)
        case "Mutation":
            return Mutation.from_tuple(args)
        case "Deletion":
            return Deletion.from_tuple(args)
        case "InsertionDeletion":
            return InsertionDeletion.from_tuple(args)
        case _:
            raise ValueError(f"Unknown CRISPR event type in tuple: {data[1]}")
