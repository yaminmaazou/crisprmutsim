import unittest
from random import Random

from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.insertion import InsertionGenerator
from crisprmutsim.CRISPR.simulation.events.mutation import MutationGenerator
from crisprmutsim.CRISPR.simulation.events.deletion import DeletionGenerator
from crisprmutsim.CRISPR.simulation.events.insertion_deletion import (
    InsertionDeletionGenerator,
)


class TestEventGenerators(unittest.TestCase):
    def test_insertion_generator(self) -> None:
        gen = InsertionGenerator(parameters={}, rate=1.0)
        rng = Random(42)
        array = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])

        event = gen.generate(rng, 0.0, array)
        self.assertEqual(event.time, 0.0)

        event = gen.generate(rng, 5.5, array)
        self.assertEqual(event.time, 5.5)

        event = gen.generate(rng, 100.0, array)
        self.assertEqual(event.time, 100.0)

        for _ in range(10):
            event = gen.generate(rng, 0.0, array)
            self.assertEqual(event.actions.get("position", 0), 0)
            self.assertEqual(event.time, 0.0)

        gen = InsertionGenerator(parameters={"randomize_position": False}, rate=1.0)
        for _ in range(10):
            event = gen.generate(rng, 0.0, array)
            self.assertEqual(event.actions.get("position", 0), 0)

        gen = InsertionGenerator(parameters={"randomize_position": True}, rate=1.0)
        positions: set[int] = set()
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            pos = event.actions["position"]
            positions.add(pos)
            self.assertGreaterEqual(pos, 0)
            self.assertLessEqual(pos, len(array))
        self.assertEqual(len(positions), 4)

        gen = InsertionGenerator(parameters={}, rate=2.5)
        self.assertEqual(gen.rate(0.0, array), 2.5)
        self.assertEqual(gen.rate(10.0, array), 2.5)
        self.assertEqual(gen.rate(100.0, array), 2.5)

        def dynamic_rate(current_time: float, obj: RawCRISPRArray) -> float:
            return current_time + len(obj)

        gen = InsertionGenerator(parameters={}, rate=dynamic_rate)

        self.assertEqual(gen.rate(0.0, array), 0.0 + 3)
        self.assertEqual(gen.rate(5.0, array), 5.0 + 3)
        self.assertEqual(gen.rate(10.0, array), 10.0 + 3)

        array2 = RawCRISPRArray(["AAAA", "TTTT"])
        self.assertEqual(gen.rate(5.0, array2), 5.0 + 2)

        gen = InsertionGenerator(parameters={"randomize_position": True}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, i, array) for i in range(10)]
        rng2 = Random(42)
        events2 = [gen.generate(rng2, i, array) for i in range(10)]

        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.time, e2.time)
            self.assertEqual(e1.actions, e2.actions)

        gen = InsertionGenerator(parameters={"randomize_position": True}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, 0.0, array) for _ in range(20)]
        rng2 = Random(123)
        events2 = [gen.generate(rng2, 0.0, array) for _ in range(20)]

        diff = sum(1 for e1, e2 in zip(events1, events2) if e1.actions != e2.actions)
        self.assertGreater(diff, 0)

    def test_mutation_generator(self) -> None:
        gen = MutationGenerator(parameters={}, rate=1.0)
        rng = Random(42)
        array = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])

        event = gen.generate(rng, 0.0, array)
        self.assertEqual(event.time, 0.0)

        event = gen.generate(rng, 5.5, array)
        self.assertEqual(event.time, 5.5)

        event = gen.generate(rng, 100.0, array)
        self.assertEqual(event.time, 100.0)

        gen = MutationGenerator(parameters={}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            base_idx = event.actions["base_index"]
            new_base = event.actions["new_base"]

            self.assertGreaterEqual(repeat_idx, 0)
            self.assertLess(repeat_idx, len(array))
            self.assertGreaterEqual(base_idx, 0)
            self.assertLess(base_idx, len(array[repeat_idx]))
            self.assertIn(new_base, "ACGT")

            old_base = array[repeat_idx][base_idx]
            self.assertNotEqual(new_base, old_base)

        gen = MutationGenerator(parameters={"allow_same_base": False}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            base_idx = event.actions["base_index"]
            new_base = event.actions["new_base"]
            old_base = array[repeat_idx][base_idx]
            self.assertNotEqual(new_base, old_base)

        gen = MutationGenerator(parameters={"allow_same_base": True}, rate=1.0)
        same_base_found = False
        for _ in range(1000):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            base_idx = event.actions["base_index"]
            new_base = event.actions["new_base"]
            old_base = array[repeat_idx][base_idx]
            if new_base == old_base:
                same_base_found = True
                break
        self.assertTrue(same_base_found)

        gen = MutationGenerator(parameters={}, rate=1.0)
        repeat_indices: set[int] = set()
        base_indices: set[int] = set()
        new_bases: set[str] = set()
        for _ in range(1000):
            event = gen.generate(rng, 0.0, array)
            repeat_indices.add(event.actions["repeat_index"])
            base_indices.add(event.actions["base_index"])
            new_bases.add(event.actions["new_base"])

        self.assertEqual(repeat_indices, {0, 1, 2})
        self.assertEqual(base_indices, {0, 1, 2, 3})
        self.assertEqual(new_bases, {"A", "C", "G", "T"})

        gen = MutationGenerator(parameters={}, rate=2.5)
        self.assertEqual(gen.rate(0.0, array), 2.5)
        self.assertEqual(gen.rate(10.0, array), 2.5)
        self.assertEqual(gen.rate(100.0, array), 2.5)

        def dynamic_rate(current_time: float, obj: RawCRISPRArray) -> float:
            return current_time * len(obj)

        gen = MutationGenerator(parameters={}, rate=dynamic_rate)

        self.assertEqual(gen.rate(0.0, array), 0.0 * 3)
        self.assertEqual(gen.rate(5.0, array), 5.0 * 3)
        self.assertEqual(gen.rate(10.0, array), 10.0 * 3)

        array2 = RawCRISPRArray(["AAAA", "TTTT"])
        self.assertEqual(gen.rate(5.0, array2), 5.0 * 2)

        gen = MutationGenerator(parameters={}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, i, array) for i in range(10)]
        rng2 = Random(42)
        events2 = [gen.generate(rng2, i, array) for i in range(10)]

        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.time, e2.time)
            self.assertEqual(e1.actions, e2.actions)

        gen = MutationGenerator(parameters={}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, 0.0, array) for _ in range(20)]
        rng2 = Random(123)
        events2 = [gen.generate(rng2, 0.0, array) for _ in range(20)]

        diff = sum(1 for e1, e2 in zip(events1, events2) if e1.actions != e2.actions)
        self.assertGreater(diff, 0)

    def test_deletion_generator(self) -> None:
        gen = DeletionGenerator(parameters={}, rate=1.0)
        rng = Random(42)
        array = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC", "ATCG"])

        event = gen.generate(rng, 0.0, array)
        self.assertEqual(event.time, 0.0)

        event = gen.generate(rng, 5.5, array)
        self.assertEqual(event.time, 5.5)

        event = gen.generate(rng, 100.0, array)
        self.assertEqual(event.time, 100.0)

        gen = DeletionGenerator(parameters={}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            split_idx = event.actions.get("split_index", -1)
            block_len = event.actions.get("block_deletion_length", 1)

            self.assertGreaterEqual(repeat_idx, 0)
            self.assertLess(repeat_idx, len(array))
            self.assertEqual(split_idx, -1)
            self.assertEqual(block_len, 1)

        gen = DeletionGenerator(parameters={"leader_offset": 1}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            self.assertGreaterEqual(repeat_idx, 1)
            self.assertLess(repeat_idx, len(array))

        gen = DeletionGenerator(parameters={"distal_offset": 1}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            self.assertGreaterEqual(repeat_idx, 0)
            self.assertLess(repeat_idx, len(array) - 1)

        gen = DeletionGenerator(
            parameters={"leader_offset": 1, "distal_offset": 1}, rate=1.0
        )
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            repeat_idx = event.actions["repeat_index"]
            self.assertGreaterEqual(repeat_idx, 1)
            self.assertLess(repeat_idx, len(array) - 1)

        gen = DeletionGenerator(parameters={"split_offset": 0}, rate=1.0)
        split_found = False
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            split_idx = event.actions.get("split_index", -1)
            if split_idx >= 0:
                split_found = True
                repeat_idx = event.actions["repeat_index"]
                self.assertGreaterEqual(split_idx, 0)
                self.assertLess(split_idx, len(array[repeat_idx]))
        self.assertTrue(split_found)

        gen = DeletionGenerator(parameters={"split_offset": 2}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            split_idx = event.actions.get("split_index", -1)
            if split_idx >= 0:
                repeat_idx = event.actions["repeat_index"]
                self.assertGreaterEqual(split_idx, 2)
                self.assertLess(split_idx, len(array[repeat_idx]))

        gen = DeletionGenerator(parameters={"max_block_deletion_length": 3}, rate=1.0)
        block_lengths: set[int] = set()
        for _ in range(200):
            event = gen.generate(rng, 0.0, array)
            block_len = event.actions.get("block_deletion_length", 1)
            block_lengths.add(block_len)
            self.assertGreaterEqual(block_len, 1)
            self.assertLessEqual(block_len, 3)
        self.assertGreater(len(block_lengths), 1)

        gen = DeletionGenerator(
            parameters={"split_offset": 1, "max_block_deletion_length": 2}, rate=1.0
        )
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            split_idx = event.actions.get("split_index", -1)
            block_len = event.actions.get("block_deletion_length", 1)
            repeat_idx = event.actions["repeat_index"]
            if split_idx >= 0:
                self.assertLess(repeat_idx + block_len, len(array))

        gen = DeletionGenerator(parameters={}, rate=1.0)
        array_small = RawCRISPRArray(["AA", "TT", "GG"])
        for _ in range(50):
            event = gen.generate(rng, 0.0, array_small)
            split_idx = event.actions.get("split_index", -1)
            self.assertEqual(split_idx, -1)

        gen = DeletionGenerator(parameters={"split_offset": 10}, rate=1.0)
        array_short = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        for _ in range(50):
            event = gen.generate(rng, 0.0, array_short)
            split_idx = event.actions.get("split_index", -1)
            self.assertEqual(split_idx, -1)

        gen = DeletionGenerator(parameters={}, rate=1.0)
        array_tiny = RawCRISPRArray(["A"])
        rate = gen.rate(0.0, array_tiny)
        self.assertEqual(rate, 0.0)

        gen = DeletionGenerator(parameters={"leader_offset": 1}, rate=1.0)
        array_tiny = RawCRISPRArray(["A"])
        rate = gen.rate(0.0, array_tiny)
        self.assertEqual(rate, 0.0)

        gen = DeletionGenerator(
            parameters={"leader_offset": 1, "distal_offset": 1}, rate=2.0
        )
        array_small = RawCRISPRArray(["A", "T"])
        rate = gen.rate(0.0, array_small)
        self.assertEqual(rate, 0.0)

        # gen = DeletionGenerator(
        #     parameters={"leader_offset": 1, "distal_offset": 1}, rate=2.0
        # )
        # array_ok = RawCRISPRArray(["A", "T", "G"])
        # rate = gen.rate(0.0, array_ok)
        # self.assertEqual(rate, 2.0)

        gen = DeletionGenerator(parameters={}, rate=2.5)
        self.assertEqual(gen.rate(0.0, array), 2.5)
        self.assertEqual(gen.rate(10.0, array), 2.5)
        self.assertEqual(gen.rate(100.0, array), 2.5)

        def dynamic_rate(current_time: float, obj: RawCRISPRArray) -> float:
            return current_time + len(obj) * 2

        gen = DeletionGenerator(parameters={}, rate=dynamic_rate)
        self.assertEqual(gen.rate(0.0, array), 0.0 + 5 * 2)
        self.assertEqual(gen.rate(5.0, array), 5.0 + 5 * 2)
        self.assertEqual(gen.rate(10.0, array), 10.0 + 5 * 2)

        array2 = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC"])
        self.assertEqual(gen.rate(5.0, array2), 5.0 + 4 * 2)

        gen = DeletionGenerator(parameters={"split_offset": 1}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, i, array) for i in range(10)]
        rng2 = Random(42)
        events2 = [gen.generate(rng2, i, array) for i in range(10)]

        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.time, e2.time)
            self.assertEqual(e1.actions, e2.actions)

        gen = DeletionGenerator(parameters={"max_block_deletion_length": 2}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, 0.0, array) for _ in range(20)]
        rng2 = Random(123)
        events2 = [gen.generate(rng2, 0.0, array) for _ in range(20)]

        diff = sum(1 for e1, e2 in zip(events1, events2) if e1.actions != e2.actions)
        self.assertGreater(diff, 0)

        with self.assertRaises(ValueError):
            DeletionGenerator(parameters={"leader_offset": -1}, rate=1.0)

        with self.assertRaises(ValueError):
            DeletionGenerator(parameters={"distal_offset": -1}, rate=1.0)

        with self.assertRaises(ValueError):
            DeletionGenerator(parameters={"max_block_deletion_length": 0}, rate=1.0)

        with self.assertRaises(ValueError):
            DeletionGenerator(parameters={"split_offset": -2}, rate=1.0)

    def test_insertion_deletion_generator(self) -> None:
        gen = InsertionDeletionGenerator(parameters={}, rate=1.0)
        rng = Random(42)
        array = RawCRISPRArray(["AAAA", "TTTT", "GGGG", "CCCC", "ATCG"])

        event = gen.generate(rng, 0.0, array)
        self.assertEqual(event.time, 0.0)
        event = gen.generate(rng, 5.5, array)
        self.assertEqual(event.time, 5.5)
        event = gen.generate(rng, 100.0, array)
        self.assertEqual(event.time, 100.0)

        gen = InsertionDeletionGenerator(parameters={}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            insertion_pos = event.actions.get("insertion_position", 0)
            deletion_idx = event.actions["deletion_repeat_index"]
            split_idx = event.actions.get("deletion_split_index", -1)

            self.assertEqual(insertion_pos, 0)
            self.assertGreaterEqual(deletion_idx, 0)
            self.assertLess(deletion_idx, len(array))
            self.assertEqual(split_idx, -1)

        gen = InsertionDeletionGenerator(parameters={"leader_offset": 1}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            deletion_idx = event.actions["deletion_repeat_index"]
            self.assertGreaterEqual(deletion_idx, 1)
            self.assertLess(deletion_idx, len(array))

        gen = InsertionDeletionGenerator(parameters={"distal_offset": 1}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            deletion_idx = event.actions["deletion_repeat_index"]
            self.assertGreaterEqual(deletion_idx, 0)
            self.assertLess(deletion_idx, len(array) - 1)

        gen = InsertionDeletionGenerator(
            parameters={"leader_offset": 1, "distal_offset": 1}, rate=1.0
        )
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            deletion_idx = event.actions["deletion_repeat_index"]
            self.assertGreaterEqual(deletion_idx, 1)
            self.assertLess(deletion_idx, len(array) - 1)

        gen = InsertionDeletionGenerator(parameters={"split_offset": 0}, rate=1.0)
        split_found = False
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            split_idx = event.actions.get("deletion_split_index", -1)
            if split_idx >= 0:
                split_found = True
                deletion_idx = event.actions["deletion_repeat_index"]
                self.assertGreaterEqual(split_idx, 0)
                self.assertLess(split_idx, len(array[deletion_idx]))
        self.assertTrue(split_found)

        gen = InsertionDeletionGenerator(parameters={"split_offset": 2}, rate=1.0)
        for _ in range(100):
            event = gen.generate(rng, 0.0, array)
            split_idx = event.actions.get("deletion_split_index", -1)
            if split_idx >= 0:
                deletion_idx = event.actions["deletion_repeat_index"]
                self.assertGreaterEqual(split_idx, 2)
                self.assertLess(split_idx, len(array[deletion_idx]))

        gen = InsertionDeletionGenerator(parameters={}, rate=1.0)
        array_small = RawCRISPRArray(["AA", "TT", "GG"])
        for _ in range(50):
            event = gen.generate(rng, 0.0, array_small)
            split_idx = event.actions.get("deletion_split_index", -1)
            self.assertEqual(split_idx, -1)

        gen = InsertionDeletionGenerator(parameters={"split_offset": 10}, rate=1.0)
        array_short = RawCRISPRArray(["AAAA", "TTTT", "GGGG"])
        for _ in range(50):
            event = gen.generate(rng, 0.0, array_short)
            split_idx = event.actions.get("deletion_split_index", -1)
            self.assertEqual(split_idx, -1)

        gen = InsertionDeletionGenerator(parameters={}, rate=1.0)
        array_tiny = RawCRISPRArray(["A"])
        rate = gen.rate(0.0, array_tiny)
        self.assertEqual(rate, 1.0)

        gen = InsertionDeletionGenerator(parameters={"leader_offset": 1}, rate=1.0)
        array_tiny = RawCRISPRArray(["A"])
        rate = gen.rate(0.0, array_tiny)
        self.assertEqual(rate, 0.0)

        gen = InsertionDeletionGenerator(
            parameters={"leader_offset": 1, "distal_offset": 1}, rate=2.0
        )
        array_small = RawCRISPRArray(["A", "T"])
        rate = gen.rate(0.0, array_small)
        self.assertEqual(rate, 0.0)

        gen = InsertionDeletionGenerator(
            parameters={"leader_offset": 1, "distal_offset": 1}, rate=2.0
        )
        array_ok = RawCRISPRArray(["A", "T", "G"])
        rate = gen.rate(0.0, array_ok)
        self.assertEqual(rate, 2.0)

        gen = InsertionDeletionGenerator(parameters={}, rate=2.5)
        self.assertEqual(gen.rate(0.0, array), 2.5)
        self.assertEqual(gen.rate(10.0, array), 2.5)
        self.assertEqual(gen.rate(100.0, array), 2.5)

        def dynamic_rate(current_time: float, obj: RawCRISPRArray) -> float:
            return current_time + len(obj) * 3

        gen = InsertionDeletionGenerator(parameters={}, rate=dynamic_rate)
        self.assertEqual(gen.rate(0.0, array), 0.0 + 5 * 3)
        self.assertEqual(gen.rate(5.0, array), 5.0 + 5 * 3)
        self.assertEqual(gen.rate(10.0, array), 10.0 + 5 * 3)

        array2 = RawCRISPRArray(["AAAA", "TTTT"])
        self.assertEqual(gen.rate(5.0, array2), 5.0 + 2 * 3)

        gen = InsertionDeletionGenerator(parameters={"split_offset": 1}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, i, array) for i in range(10)]
        rng2 = Random(42)
        events2 = [gen.generate(rng2, i, array) for i in range(10)]

        for e1, e2 in zip(events1, events2):
            self.assertEqual(e1.time, e2.time)
            self.assertEqual(e1.actions, e2.actions)

        gen = InsertionDeletionGenerator(parameters={}, rate=1.0)
        rng1 = Random(42)
        events1 = [gen.generate(rng1, 0.0, array) for _ in range(20)]
        rng2 = Random(123)
        events2 = [gen.generate(rng2, 0.0, array) for _ in range(20)]

        diff = sum(1 for e1, e2 in zip(events1, events2) if e1.actions != e2.actions)
        self.assertGreater(diff, 0)

        with self.assertRaises(ValueError):
            InsertionDeletionGenerator(parameters={"leader_offset": -1}, rate=1.0)

        with self.assertRaises(ValueError):
            InsertionDeletionGenerator(parameters={"distal_offset": -1}, rate=1.0)

        with self.assertRaises(ValueError):
            InsertionDeletionGenerator(parameters={"split_offset": -2}, rate=1.0)


if __name__ == "__main__":
    unittest.main()
