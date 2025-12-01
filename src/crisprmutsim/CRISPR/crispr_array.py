from dataclasses import asdict, dataclass, field
import sqlite3
from typing import Self
from crisprmutsim.CRISPR.array_stats import ArrayStats
from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray


@dataclass
class CRISPRArray:
    id: str
    cas_type: str
    repeat_stats: ArrayStats = field(default_factory=ArrayStats.empty)

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> "CRISPRArray":
        return cls(
            id=row["id"],
            cas_type=row["cas_type"],
            repeat_stats=ArrayStats.from_db_row(row),
        )

    @classmethod
    def from_raw_array(
        cls,
        id: str,
        cas_type: str,
        raw_array: RawCRISPRArray,
    ) -> Self:
        stats = raw_array.all_stats()
        return cls(
            id=id,
            cas_type=cas_type,
            repeat_stats=stats,
        )

    def as_raw_array(self) -> RawCRISPRArray:
        return RawCRISPRArray.from_array_stats(self.repeat_stats)

    def as_flat_dict(self):
        data = asdict(self)
        del data["repeat_stats"]
        data.update(asdict(self.repeat_stats))
        return data
