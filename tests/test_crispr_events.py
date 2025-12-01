import unittest

from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.deletion import Deletion
from crisprmutsim.CRISPR.simulation.events.insertion import Insertion
from crisprmutsim.CRISPR.simulation.events.insertion_deletion import InsertionDeletion
from crisprmutsim.CRISPR.simulation.events.mutation import Mutation


class TestCrisprEvents(unittest.TestCase):
    def test_insertion(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["ACGT", "TGCA", "AAAA"])

        a.apply_events([Insertion(0.0, {"position": 0})])
        self.assertEqual(a, ["ACGT", "ACGT", "TGCA", "AAAA"])

        a.apply_events([Insertion(0.0, {"position": 3})])
        self.assertEqual(a, ["ACGT", "ACGT", "TGCA", "ACGT", "AAAA"])

        a.apply_events([Insertion(0.0, {"position": 5})])
        self.assertEqual(a, ["ACGT", "ACGT", "TGCA", "ACGT", "AAAA", "ACGT"])

        with self.assertRaises(IndexError):
            a.apply_events([Insertion(0.0, {"position": 10})])

        with self.assertRaises(IndexError):
            a.apply_events([Insertion(0.0, {"position": -1})])

    def test_mutation(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["AAAAA", "AAAAA", "AAAAA"])

        # first repeat, first base
        a.apply_events(
            [Mutation(0.0, {"repeat_index": 0, "base_index": 0, "new_base": "T"})]
        )
        self.assertEqual(a, ["TAAAA", "AAAAA", "AAAAA"])

        # middle repeat, middle base
        a.apply_events(
            [Mutation(0.0, {"repeat_index": 1, "base_index": 2, "new_base": "G"})]
        )
        self.assertEqual(a, ["TAAAA", "AAGAA", "AAAAA"])

        # last repeat, last base
        a.apply_events(
            [Mutation(0.0, {"repeat_index": 2, "base_index": 4, "new_base": "C"})]
        )
        self.assertEqual(a, ["TAAAA", "AAGAA", "AAAAC"])

        with self.assertRaises(IndexError):
            a.apply_events(
                [Mutation(0.0, {"repeat_index": 10, "base_index": 0, "new_base": "A"})]
            )

        with self.assertRaises(IndexError):
            a.apply_events(
                [Mutation(0.0, {"repeat_index": -1, "base_index": 0, "new_base": "A"})]
            )

        with self.assertRaises(IndexError):
            a.apply_events(
                [Mutation(0.0, {"repeat_index": 0, "base_index": 10, "new_base": "A"})]
            )

        with self.assertRaises(IndexError):
            a.apply_events(
                [Mutation(0.0, {"repeat_index": 0, "base_index": -1, "new_base": "A"})]
            )

    def test_deletion(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([Deletion(0.0, {"repeat_index": 0, "split_index": -1})])
        self.assertEqual(a, ["TTTT", "GGGG", "CCCC"])

        a.apply_events([Deletion(0.0, {"repeat_index": 2, "split_index": -1})])
        self.assertEqual(a, ["TTTT", "GGGG"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC", "ATCG"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 1, "split_index": -1, "block_deletion_length": 2},
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "CCCC", "ATCG"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 0, "split_index": -1, "block_deletion_length": 2},
                )
            ]
        )
        self.assertEqual(a, ["GGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 2, "split_index": -1, "block_deletion_length": 2},
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "TTTT"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([Deletion(0.0, {"repeat_index": 1, "split_index": 2})])
        self.assertEqual(a, ["AAAA", "TTGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([Deletion(0.0, {"repeat_index": 1, "split_index": 1})])
        self.assertEqual(a, ["AAAA", "TGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([Deletion(0.0, {"repeat_index": 1, "split_index": 0})])
        self.assertEqual(a, ["AAAA", "GGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([Deletion(0.0, {"repeat_index": 1, "split_index": 4})])
        self.assertEqual(a, ["AAAA", "TTTT", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC", "ATCG"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 1, "split_index": 2, "block_deletion_length": 2},
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "TTCC", "ATCG"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 0, "split_index": -1, "block_deletion_length": 4},
                )
            ]
        )
        self.assertEqual(a, [])

        a = RawCRISPRArray(["AAAA"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 0, "split_index": -1, "block_deletion_length": 1},
                )
            ]
        )
        self.assertEqual(a, [])

        a = RawCRISPRArray([])
        with self.assertRaises(ValueError):
            a.apply_events([Deletion(0.0, {"repeat_index": 0})])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events([Deletion(0.0, {"repeat_index": -1})])

        # no splits on last repeat
        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events([Deletion(0.0, {"repeat_index": 2, "split_index": 2})])

        a = RawCRISPRArray(["AAAA"])
        with self.assertRaises(IndexError):
            a.apply_events([Deletion(0.0, {"repeat_index": 0, "split_index": 1})])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events([Deletion(0.0, {"repeat_index": 1, "split_index": 10})])

        # block deletion length too large
        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(ValueError):
            a.apply_events(
                [Deletion(0.0, {"repeat_index": 1, "block_deletion_length": 3})]
            )

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        a.apply_events(
            [
                Deletion(
                    0.0,
                    {"repeat_index": 1, "split_index": -1, "block_deletion_length": 2},
                )
            ]
        )
        self.assertEqual(a, ["AAAA"])

        # block deletion length too large for split
        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events(
                [
                    Deletion(
                        0.0,
                        {
                            "repeat_index": 1,
                            "split_index": 2,
                            "block_deletion_length": 2,
                        },
                    )
                ]
            )

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(ValueError):
            a.apply_events(
                [
                    Deletion(
                        0.0,
                        {
                            "repeat_index": 0,
                            "split_index": -1,
                            "block_deletion_length": 4,
                        },
                    )
                ]
            )

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(ValueError):
            a.apply_events(
                [Deletion(0.0, {"repeat_index": 1, "block_deletion_length": 0})]
            )

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(ValueError):
            a.apply_events(
                [Deletion(0.0, {"repeat_index": 1, "block_deletion_length": -1})]
            )

    def test_insertion_deletion(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 0, "deletion_repeat_index": 2}
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "AAAA", "TTTT", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 0, "deletion_repeat_index": 0}
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "TTTT", "GGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 2, "deletion_repeat_index": 0}
                )
            ]
        )
        self.assertEqual(a, ["TTTT", "AAAA", "GGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 2, "deletion_repeat_index": 2}
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "TTTT", "AAAA", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 4, "deletion_repeat_index": 1}
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "GGGG", "CCCC", "AAAA"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0,
                    {
                        "insertion_position": 0,
                        "deletion_repeat_index": 1,
                        "deletion_split_index": 2,
                    },
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "AAAA", "TTGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0,
                    {
                        "insertion_position": 0,
                        "deletion_repeat_index": 0,
                        "deletion_split_index": 2,
                    },
                )
            ]
        )
        self.assertEqual(a, ["AAAA", "AATT", "GGGG", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events([InsertionDeletion(0.0, {"deletion_repeat_index": 3})])
        self.assertEqual(a, ["AAAA", "AAAA", "TTTT", "GGGG"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        a.apply_events(
            [
                InsertionDeletion(
                    0.0, {"insertion_position": 3, "deletion_repeat_index": 0}
                )
            ]
        )
        self.assertEqual(a, ["TTTT", "GGGG", "AAAA", "CCCC"])

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events(
                [
                    InsertionDeletion(
                        0.0, {"insertion_position": 0, "deletion_repeat_index": 10}
                    )
                ]
            )

        a = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        with self.assertRaises(IndexError):
            a.apply_events(
                [
                    InsertionDeletion(
                        0.0, {"insertion_position": 10, "deletion_repeat_index": 0}
                    )
                ]
            )


if __name__ == "__main__":
    unittest.main()
