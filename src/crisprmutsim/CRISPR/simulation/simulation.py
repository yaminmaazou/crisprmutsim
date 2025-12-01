from collections import deque
from collections.abc import Callable, Collection, Iterator
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path
from random import Random

from crisprmutsim.CRISPR.array_stats import ArrayStats
from crisprmutsim.CRISPR.crispr_array import CRISPRArray
from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    ICRISPREvent,
    ICRISPREventGenerator,
)
import crisprmutsim.CRISPR.storage as db
from crisprmutsim.simulation.event import EventParametersType
from crisprmutsim.simulation.simulation import run_poisson_process


def run_crispr_poisson_process(
    rng: Random,
    end_time: float,
    array: RawCRISPRArray,
    event_generators: Collection[
        ICRISPREventGenerator[EventParametersType, ICRISPREvent]
    ],
) -> Iterator[ICRISPREvent]:
    return run_poisson_process(rng, end_time, array, event_generators)


def run_single(
    seed: int,
    end_time: float,
    array_length: int,
    repeat_length: int,
    event_generators: list[ICRISPREventGenerator[EventParametersType, ICRISPREvent]],
) -> tuple[int, ArrayStats]:
    rng = Random(seed)
    array = RawCRISPRArray([["N"] * repeat_length] * array_length, unsafe=True)
    array.apply_events = array.__unsafe_apply_events__

    # fast exhaust
    deque(run_crispr_poisson_process(rng, end_time, array, event_generators), maxlen=0)

    # reduce pickle overhead; array can be reconstructed
    return seed, array.all_stats()


def run_parallel(
    base_seed: int,
    end_time: float,
    array_length: int,
    repeat_length: int,
    event_generators: list[ICRISPREventGenerator[EventParametersType, ICRISPREvent]],
    num_runs: int,
    num_workers: int = 4,
) -> list[Future[tuple[int, ArrayStats]]]:
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = [
        executor.submit(
            run_single,
            base_seed + i,
            end_time,
            array_length,
            repeat_length,
            event_generators,
        )
        for i in range(num_runs)
    ]
    return futures


def run_and_iter_results(
    base_seed: int,
    end_time: float,
    array_length: int,
    repeat_length: int,
    event_generators: list[ICRISPREventGenerator[EventParametersType, ICRISPREvent]],
    num_runs: int,
    num_workers: int = 4,
) -> Iterator[tuple[int, ArrayStats]]:
    print(f"Starting {num_workers} workers")
    futures = run_parallel(
        base_seed,
        end_time,
        array_length,
        repeat_length,
        event_generators,
        num_runs,
        num_workers,
    )

    for future in as_completed(futures):
        yield future.result()


def run_and_store_results(
    filename: str,
    base_seed: int,
    end_time: float,
    array_length: int,
    repeat_length: int,
    event_generators: list[ICRISPREventGenerator[EventParametersType, ICRISPREvent]],
    num_runs: int,
    meta: str = "",
    num_workers: int = 4,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    if Path(filename).exists():
        raise FileExistsError(f"Database file {filename} already exists")

    arrays: list[CRISPRArray] = []
    count = 0
    for seed, stats in run_and_iter_results(
        base_seed,
        end_time,
        array_length,
        repeat_length,
        event_generators,
        num_runs,
        num_workers,
    ):
        arrays.append(
            CRISPRArray(
                id=str(seed - base_seed),
                cas_type="",
                repeat_stats=stats,
            )
        )
        count += 1
        if count % 100 == 0:
            print(f"Completed {count} / {num_runs} runs")
        if progress_callback:
            progress_callback(count, num_runs)

    with db.database(filename) as con:
        db.store_meta(con, "sim")
        db.store_arrays(con, arrays)
        db.store_simulation_info(
            con,
            base_seed,
            end_time,
            array_length,
            repeat_length,
            event_generators,
            num_runs,
            meta,
        )

    print("Simulation complete and db stored")
