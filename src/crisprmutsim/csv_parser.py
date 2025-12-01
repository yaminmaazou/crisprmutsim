from collections.abc import Iterator
from pathlib import Path
import csv

from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.crispr_array import CRISPRArray
import crisprmutsim.CRISPR.storage as db


def iter_csv_rows(file_path: str) -> Iterator[dict[str, str]]:
    p = Path(file_path)
    with p.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)  # uses the first row as header
        for row in reader:
            yield row


def iter_arrays(
    file_path: str,
    id_column: str,
    repeats_column: str,
    consensus_column: str,
    cas_type_column: str,
) -> Iterator[tuple[str, list[str], str, str]]:
    for row in iter_csv_rows(file_path):
        name = row[id_column]
        repeats = [repeat.upper() for repeat in row[repeats_column].split()]
        consensus = row[consensus_column].upper()
        cas_type = row.get(cas_type_column, "").replace("CAS-", "")
        yield name, repeats, consensus, cas_type


def drop_mismatched_lengths(
    repeats: list[str],
    consensus: str,
) -> list[str]:
    L = len(consensus)
    kept = [r for r in repeats if len(r) == L]
    return kept


def load_csv(
    csv_file_path: str,
    db_file_path: str,
    id_column: str = "array_name",
    repeats_column: str = "repeat_sequences",
    consensus_column: str = "consensus_repeat",
    cas_type_column: str = "cas_type",
    drop_consensus_duplicates: bool = True,
    drop_full_duplicates: bool = True,
) -> None:
    if Path(db_file_path).exists():
        raise FileExistsError(f"Database file {db_file_path} already exists")

    total_arrays = 0
    empty_after_cleanup = 0
    total_repeats = 0
    total_dropped_repeats = 0
    duplicates_dropped = 0
    duplicates_dropped_consensus = 0

    arrays: list[CRISPRArray] = []
    unique_arrays: set[RawCRISPRArray] = set()
    unique_consensus_cas: set[tuple[str, str]] = set()

    print(f"Loading CSV data from {csv_file_path}")

    for name, repeats, consensus, cas_type in iter_arrays(
        csv_file_path,
        id_column,
        repeats_column,
        consensus_column,
        cas_type_column,
    ):
        if drop_consensus_duplicates:
            if (consensus, cas_type) in unique_consensus_cas:
                duplicates_dropped_consensus += 1
                continue
            unique_consensus_cas.add((consensus, cas_type))
        clean_array = drop_mismatched_lengths(repeats, consensus)
        total_arrays += 1
        total_repeats += len(repeats)
        total_dropped_repeats += len(repeats) - len(clean_array)

        if total_arrays % 1000 == 0:
            print(f"Created {total_arrays} objects")

        if clean_array and len(clean_array) > 2:
            _arr = RawCRISPRArray(clean_array)

            if drop_full_duplicates:
                if _arr in unique_arrays:
                    duplicates_dropped += 1
                    continue
                unique_arrays.add(_arr)

            obj = CRISPRArray.from_raw_array(
                id=name,
                cas_type=cas_type,
                raw_array=_arr,
            )

            arrays.append(obj)

        else:
            empty_after_cleanup += 1

    print(
        f"Created {total_arrays} arrays, skipped {empty_after_cleanup} arrays with fewer than 3 repeats"
    )
    print(
        f"Dropped {total_dropped_repeats} repeats out of {total_repeats} total repeats"
    )
    if drop_full_duplicates:
        print(f"Dropped {duplicates_dropped} duplicate arrays")
    if drop_consensus_duplicates:
        print(
            f"Dropped {duplicates_dropped_consensus} duplicate arrays based on consensus"
        )
    print(f"Storing {len(arrays)}")

    with db.database(db_file_path) as con:
        db.store_meta(
            con,
            "file",
        )
        db.store_arrays(con, arrays)

    print(f"Saved to {db_file_path}")
