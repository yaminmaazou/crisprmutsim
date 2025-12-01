from collections.abc import Collection, Iterator
from random import Random
from typing import Any

from crisprmutsim.simulation.event import (
    EventParametersType,
    IAcceptsEvents,
    IEvent,
    IEventGenerator,
)


# same issue with IAcceptsEvents as in event.py; workaround using Any
def run_poisson_process[
    TEventParameters: EventParametersType,
    TIEvent: IEvent,
    TIAcceptsEvents: IAcceptsEvents[Any],
](
    rng: Random,
    end_time: float,
    obj: TIAcceptsEvents,
    event_generators: Collection[
        IEventGenerator[TEventParameters, TIEvent, TIAcceptsEvents]
    ],
) -> Iterator[TIEvent]:
    if len(event_generators) == 0:
        raise ValueError("No event generators provided for simulation.")
    if end_time <= 0:
        raise ValueError("End time must be greater than 0.")

    current_time: float = 0.0

    while current_time < end_time:
        min_delta: float = float("inf")
        earliest_event_gen: (
            IEventGenerator[TEventParameters, TIEvent, TIAcceptsEvents] | None
        ) = None

        for event_gen in event_generators:
            rate = event_gen.rate(current_time, obj)
            delta = rng.expovariate(rate) if rate > 0 else float("inf")

            if delta < min_delta:
                min_delta = delta
                earliest_event_gen = event_gen

        # no events fired
        if earliest_event_gen is None:
            break

        current_time += min_delta

        if current_time > end_time:
            break

        event = earliest_event_gen.generate(rng, current_time, obj)
        obj.apply_events([event])
        yield event
