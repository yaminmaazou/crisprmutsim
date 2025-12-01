from dataclasses import dataclass
import json
import sqlite3

from crisprmutsim.CRISPR.simulation.events.mutation import MutationActions


@dataclass
class ArrayStats:
    consensus_repeat: str  # raw string for faster pickling (multithreading)
    array_length: int
    repeat_length: int
    mutation_count_consensus: int
    mutation_count_proximal: int
    mutation_count_distal: int
    mutation_diff_consensus: list[MutationActions]
    mutation_diff_proximal: list[MutationActions]
    mutation_diff_distal: list[MutationActions]
    patterns: set[int]

    @classmethod
    def empty(cls) -> "ArrayStats":
        return cls(
            consensus_repeat="",
            array_length=0,
            repeat_length=0,
            mutation_count_consensus=0,
            mutation_count_proximal=0,
            mutation_count_distal=0,
            mutation_diff_consensus=[],
            mutation_diff_proximal=[],
            mutation_diff_distal=[],
            patterns=set(),
        )

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> "ArrayStats":
        return cls(
            consensus_repeat=row["consensus_repeat"],
            array_length=row["array_length"],
            repeat_length=row["repeat_length"],
            mutation_count_consensus=row["mutation_count_consensus"],
            mutation_count_proximal=row["mutation_count_proximal"],
            mutation_count_distal=row["mutation_count_distal"],
            mutation_diff_consensus=json.loads(row["mutation_diff_consensus"]),
            mutation_diff_proximal=json.loads(row["mutation_diff_proximal"]),
            mutation_diff_distal=json.loads(row["mutation_diff_distal"]),
            patterns=set(json.loads(row["patterns"])),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ArrayStats":
        data = json.loads(json_str)
        return cls(
            consensus_repeat=data["consensus_repeat"],
            array_length=data["array_length"],
            repeat_length=data["repeat_length"],
            mutation_count_consensus=data["mutation_count_consensus"],
            mutation_count_proximal=data["mutation_count_proximal"],
            mutation_count_distal=data["mutation_count_distal"],
            mutation_diff_consensus=data["mutation_diff_consensus"],
            mutation_diff_proximal=data["mutation_diff_proximal"],
            mutation_diff_distal=data["mutation_diff_distal"],
            patterns=set(data["patterns"]),
        )
