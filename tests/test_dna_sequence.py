import unittest

from crisprmutsim.CRISPR.dna_sequence import DNASequence


class TestDNASequence(unittest.TestCase):
    def test_declare(self) -> None:
        a: DNASequence = DNASequence("aCGaCgT")
        self.assertEqual(a.sequence, ["A", "C", "G", "A", "C", "G", "T"])
        b: DNASequence = DNASequence(["A", "C", "G"])
        self.assertEqual(b.sequence, ["A", "C", "G"])
        self.assertEqual(a, DNASequence(a))

        with self.assertRaises(ValueError):
            DNASequence("ACGTX")
        with self.assertRaises(ValueError):
            DNASequence(["A", "C", "G", "X"])
        with self.assertRaises(ValueError):
            DNASequence(["A", "C", "G", "AC"])

    def test_getitem(self) -> None:
        a: DNASequence = DNASequence("ACGaCgT")
        self.assertEqual(a[0], "A")
        self.assertEqual(a[-1], "T")
        self.assertEqual(a[1:3], ["C", "G"])
        self.assertEqual(a[1:3], a[1:3])

        with self.assertRaises(IndexError):
            a[7]

    def test_setitem(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        a[0] = "T"
        self.assertEqual(a, "TCGT")
        a[1:3] = ["A", "T"]
        self.assertEqual(a, "TATT")
        a[0:2] = ["A"]
        self.assertEqual(a, "ATT")
        a[0:3] = "ACG"
        self.assertEqual(a, "ACG")

        with self.assertRaises(ValueError):
            a[0] = "X"
        with self.assertRaises(ValueError):
            a[0] = "AC"  # requires slice

    def test_delitem(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        del a[0]
        self.assertEqual(a, "CGT")
        del a[1:3]
        self.assertEqual(a, "C")

        with self.assertRaises(IndexError):
            del a[1]

    def test_equality(self) -> None:
        a: DNASequence = DNASequence("ACGaCgT")
        b: DNASequence = DNASequence("ACG")
        c: DNASequence = DNASequence("ACGACGT")
        self.assertFalse(a == b)
        self.assertTrue(a == a)
        self.assertTrue(a == c)

        self.assertTrue(a == "ACGACGT")
        self.assertTrue(a == ["A", "C", "G", "A", "C", "G", "T"])
        self.assertFalse(a == "ACG")
        self.assertFalse(a == ["A", "C", "G"])
        self.assertFalse(a == 1)

    def test_contains(self) -> None:
        a: DNASequence = DNASequence("ACGaCgT")
        b: DNASequence = DNASequence("ACG")
        c: DNASequence = DNASequence("ACGACGT")
        self.assertTrue(b in a)
        self.assertTrue(c in a)
        self.assertFalse(a in b)

        self.assertTrue(["A", "C"] in a)
        self.assertTrue("AC" in a)
        self.assertFalse("ACT" in a)

        with self.assertRaises(TypeError):
            self.assertTrue(1 in a)

    def test_insert(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        a.insert(0, "A")
        self.assertEqual(a, "AACGT")
        a.insert(1, "C")
        self.assertEqual(a, "ACACGT")

        with self.assertRaises(ValueError):
            a.insert(0, "X")
        with self.assertRaises(ValueError):
            a.insert(0, "AC")

    def test_index(self) -> None:
        a: DNASequence = DNASequence("ACG")
        self.assertEqual(a.index("A"), 0)
        self.assertEqual(a.index("C"), 1)
        self.assertEqual(a.index("G"), 2)
        # self.assertEqual(a.index("AC"), 0) # TODO

        with self.assertRaises(ValueError):
            a.index("T")
        with self.assertRaises(ValueError):
            a.index("X")

    def test_count(self) -> None:
        a: DNASequence = DNASequence("ACGACGT")
        self.assertEqual(a.count("A"), 2)
        self.assertEqual(a.count("C"), 2)
        self.assertEqual(a.count("G"), 2)
        self.assertEqual(a.count("T"), 1)
        # self.assertEqual(a.count("AC"), 2) # TODO

        self.assertEqual(a.count("X"), 0)

    def test_add(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        b: DNASequence = DNASequence("TGCA")
        self.assertEqual(a + b, "ACGTTGCA")
        self.assertEqual(a + "TGCA", "ACGTTGCA")

        with self.assertRaises(ValueError):
            self.assertEqual(a + "x", "ACGTX")

    def test_iadd(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        a += "TGCA"
        self.assertEqual(a, "ACGTTGCA")
        a += ["A", "C"]
        self.assertEqual(a, "ACGTTGCAAC")
        a += DNASequence("GT")
        self.assertEqual(a, "ACGTTGCAACGT")

        with self.assertRaises(ValueError):
            a += "x"
        with self.assertRaises(ValueError):
            a += ["AA", "C"]

    def test_radd(self) -> None:
        a: DNASequence = DNASequence("ACGT")
        self.assertEqual("TGCA" + a, "TGCAACGT")
        self.assertEqual(["A", "C"] + a, DNASequence("ACACGT"))
        self.assertEqual(DNASequence("GT") + a, "GTACGT")
        self.assertEqual(["a"] + a, ["A", "A", "C", "G", "T"])

        with self.assertRaises(ValueError):
            self.assertEqual("x" + a, "bACGT")
        with self.assertRaises(ValueError):
            self.assertEqual(["AA", "C"] + a, ["AA", "C", "A", "C", "G", "T"])


if __name__ == "__main__":
    unittest.main()
