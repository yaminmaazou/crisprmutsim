from collections.abc import Callable, Iterable, Mapping, Sequence
import json
from random import Random
from typing import Any, Protocol, Self


EventParametersType = Mapping[str, object]
EventActionsType = Mapping[str, object]


class IEvent(Protocol):
    time: float

    @property
    def actions(self) -> EventActionsType: ...

    # @classmethod
    # def from_db_row(cls, cursor: sqlite3.Cursor, row: sqlite3.Row) -> Self: ...


# in theory, TIEvent should be bound by a generic IEvent. sadly, python doesn't support HKTs yet
#  (in this case, generics over a generic type)
# see https://github.com/python/typing/issues/548
class IAcceptsEvents[TIEvent: IEvent](Protocol):
    def apply_events(self, events: Iterable[TIEvent]) -> None: ...


# same issue. without expensive runtime checks, we have to "trust" that the param type PT_co
#   is compatible with the event type TIEvent. I don't want to avoid the param redundancy,
#   so python can maintain a single dict in memory, per event type.
# in practice, none of this matters of course. nobody cares about my type safety rants.
# TAcceptsEvents = TypeVar("TAcceptsEvents", bound=IAcceptsEvents[IEvent[EventParametersType, EventActionsType]], contravariant=True)

# class IEventGenerator[TEventParameters: EventParametersType, TIEvent: IEvent, TIAcceptsEvents: IAcceptsEvents[IEvent]](Protocol)
# does not work, because TIAcceptsEvents is contravariant. Trying to inherit (e.g. ICRISPREventGenerator) and trying to narrow it down to IAcceptsEvents[ICRISPREvent] fails. It would only work if its upper bound was IAcceptsEvents[TIEvent], using the typevar TIEvent, but that's a HKT.
# for now, we use Any...


class IEventGenerator[
    TEventParameters: EventParametersType,
    TIEvent: IEvent,
    TIAcceptsEvents: IAcceptsEvents[Any],
](Protocol):
    _rate: float | Callable[[float, TIAcceptsEvents], float]

    @property
    def parameters(self) -> TEventParameters: ...

    # rate can return a simple float, or perform a more complex calculation
    #   based on the current time and/or the state of the object it's generating events for
    def rate(self, current_time: float, obj: TIAcceptsEvents) -> float: ...

    def generate(
        self, rng: Random, current_time: float, obj: TIAcceptsEvents
    ) -> TIEvent: ...


# implementation for inheritance
class Event[TEventActions: EventActionsType]:
    @property
    def actions(self) -> TEventActions:
        return self._actions

    def __init__(self, time: float, actions: TEventActions) -> None:
        self.time = time
        self._actions = actions

    @classmethod
    def from_tuple(cls, data: tuple[float, str]) -> Self:
        return cls(
            time=data[0],
            actions=json.loads(data[1]),
        )

    @classmethod
    def to_string(cls, e: Self) -> str:
        return f"{e.time}: {e.__class__.__name__}({e.actions})"

    @classmethod
    def list_to_dict(cls, events: Sequence[IEvent]) -> dict[str, object]:
        event_ids: list[str] = []
        times: list[float] = []
        actions: list[EventActionsType] = []
        for event in events:
            event_ids.append(event.__class__.__name__)
            times.append(event.time)
            actions.append(event.actions)
        event_dict: dict[str, object] = {
            "index": list(
                range(len(events))
            ),  # necessary for Dash, since the order of events is not maintained for different event types
            "event_id": event_ids,
            "time": times,
            "actions": actions,
        }
        return event_dict

    def __str__(self) -> str:
        return self.to_string(self)

    # for auto string conversion (e.g. list prints)
    def __repr__(self) -> str:
        return self.__str__()


def event_to_tuple(e: IEvent) -> tuple[str, float, str]:
    return (
        e.__class__.__name__,
        e.time,
        json.dumps(e.actions),
    )


def event_generators_to_json(
    gens: Sequence[IEventGenerator[EventParametersType, IEvent, Any]],
) -> str:
    return json.dumps(
        [
            {
                "type": gen.__class__.__name__,
                "parameters": gen.parameters,
                "rate": (gen._rate if not callable(gen._rate) else "callable"),
            }
            for gen in gens
        ]
    )
