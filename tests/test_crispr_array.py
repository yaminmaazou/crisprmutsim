import unittest

from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.dna_sequence import DNASequence


class TestCrisprArray(unittest.TestCase):
    def test_declare(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertEqual(a.repeat_sequences, [DNASequence("ACGT"), DNASequence("TGCA")])
        b: RawCRISPRArray = RawCRISPRArray(
            [DNASequence("A"), DNASequence("C"), DNASequence("G")]
        )
        self.assertEqual(
            b.repeat_sequences, [DNASequence("A"), DNASequence("C"), DNASequence("G")]
        )
        self.assertEqual(a, RawCRISPRArray(a))

        self.assertEqual(
            RawCRISPRArray(["ACGT", "TGCA"]),
            RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")]),
        )
        self.assertEqual(
            RawCRISPRArray(["ACGT"]), RawCRISPRArray([DNASequence("ACGT")])
        )
        self.assertEqual(
            RawCRISPRArray(DNASequence("ACGT")), RawCRISPRArray([DNASequence("ACGT")])
        )
        self.assertEqual(RawCRISPRArray("ACGT"), RawCRISPRArray([DNASequence("ACGT")]))

        # Ambiguous! List of single characters will be converted to two single-base repeats, which may not be intended.
        with self.assertWarns(Warning):
            self.assertEqual(
                RawCRISPRArray(["A", "C", "G"]),
                RawCRISPRArray([DNASequence("A"), DNASequence("C"), DNASequence("G")]),
            )

    def test_getitem(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertEqual(a[0], DNASequence("ACGT"))
        self.assertEqual(a[-1], DNASequence("TGCA"))
        self.assertEqual(a[0:2], [DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertEqual(a[1:3], a[1:3])

        with self.assertRaises(IndexError):
            a[7]

    def test_setitem(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        a[0] = DNASequence("T")
        self.assertEqual(a, [DNASequence("T"), DNASequence("TGCA")])
        a[0:2] = [DNASequence("A"), DNASequence("T")]
        self.assertEqual(a, [DNASequence("A"), DNASequence("T")])

    def test_delitem(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["ACGT", "TGCA", "G", "A"])
        del a[0]
        self.assertEqual(a, ["TGCA", "G", "A"])
        del a[1:3]
        self.assertEqual(a, ["TGCA"])

        with self.assertRaises(IndexError):
            del a[1]

    def test_equality(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        b: RawCRISPRArray = RawCRISPRArray([DNASequence("ACG")])
        c: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertFalse(a == b)
        self.assertTrue(a == a)
        self.assertTrue(a == c)

        self.assertTrue(a == [DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertTrue(a == ["ACGT", "TGCA"])
        self.assertFalse(a == [DNASequence("ACG")])
        self.assertFalse(a == 1)

    def test_contains(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertTrue(DNASequence("ACGT") in a)
        self.assertFalse(DNASequence("A") in a)
        self.assertTrue("ACGT" in a)
        self.assertTrue(["T", "G", "C", "A"] in a)

        with self.assertRaises(TypeError):
            self.assertTrue(1 in a)

    def test_insert(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        a.insert(1, DNASequence("G"))
        self.assertEqual(
            a, [DNASequence("ACGT"), DNASequence("G"), DNASequence("TGCA")]
        )
        a.insert(0, DNASequence("A"))
        self.assertEqual(
            a,
            [
                DNASequence("A"),
                DNASequence("ACGT"),
                DNASequence("G"),
                DNASequence("TGCA"),
            ],
        )

    def test_index(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray([DNASequence("ACGT"), DNASequence("TGCA")])
        self.assertEqual(a.index(DNASequence("ACGT")), 0)
        self.assertEqual(a.index(DNASequence("TGCA")), 1)

        with self.assertRaises(ValueError):
            a.index(DNASequence("A"))

    def test_count(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(
            [DNASequence("ACGT"), DNASequence("TGCA"), DNASequence("ACGT")]
        )
        self.assertEqual(a.count(DNASequence("ACGT")), 2)
        self.assertEqual(a.count(DNASequence("TGCA")), 1)

        self.assertEqual(a.count(DNASequence("A")), 0)

    def test_add(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["ACGT", "TGCA"])
        b: RawCRISPRArray = RawCRISPRArray(["GG", "TT"])
        self.assertEqual(a + "A", RawCRISPRArray(["ACGT", "TGCA", "A"]))
        self.assertEqual(a + "AAA", RawCRISPRArray(["ACGT", "TGCA", "AAA"]))
        self.assertEqual(a + DNASequence("A"), RawCRISPRArray(["ACGT", "TGCA", "A"]))
        self.assertEqual(a + b, RawCRISPRArray(["ACGT", "TGCA", "GG", "TT"]))
        self.assertEqual(
            a + ["TTT", "CCC"], RawCRISPRArray(["ACGT", "TGCA", "TTT", "CCC"])
        )

        with self.assertRaises(ValueError):
            self.assertEqual(a + "X", RawCRISPRArray(["ACGT", "TGCA", "X"]))

        # Ambiguous! List of single characters will be converted to two single-base repeats, which may not be intended.
        with self.assertWarns(Warning):
            self.assertEqual(a + ["T", "A"], RawCRISPRArray(["ACGT", "TGCA", "T", "A"]))

    def test_iadd(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["ACGT", "TGCA"])
        b: RawCRISPRArray = RawCRISPRArray(["GG", "TT"])
        a += "A"
        self.assertEqual(a, RawCRISPRArray(["ACGT", "TGCA", "A"]))
        a += DNASequence("AAA")
        self.assertEqual(a, RawCRISPRArray(["ACGT", "TGCA", "A", "AAA"]))
        a += "ACG"
        self.assertEqual(a, RawCRISPRArray(["ACGT", "TGCA", "A", "AAA", "ACG"]))
        a += b
        self.assertEqual(
            a, RawCRISPRArray(["ACGT", "TGCA", "A", "AAA", "ACG", "GG", "TT"])
        )
        a += ["TTT", "CCC"]
        self.assertEqual(
            a,
            RawCRISPRArray(
                ["ACGT", "TGCA", "A", "AAA", "ACG", "GG", "TT", "TTT", "CCC"]
            ),
        )

        with self.assertRaises(ValueError):
            a += "X"

        # Ambiguous! List of single characters will be converted to two single-base repeats, which may not be intended.
        with self.assertWarns(Warning):
            a += ["T", "A"]
            self.assertEqual(
                a,
                RawCRISPRArray(
                    [
                        "ACGT",
                        "TGCA",
                        "A",
                        "AAA",
                        "ACG",
                        "GG",
                        "TT",
                        "TTT",
                        "CCC",
                        "T",
                        "A",
                    ]
                ),
            )

    def test_radd(self) -> None:
        a: RawCRISPRArray = RawCRISPRArray(["ACGT", "TGCA"])
        self.assertEqual("A" + a, RawCRISPRArray(["A", "ACGT", "TGCA"]))
        self.assertEqual("AAA" + a, RawCRISPRArray(["AAA", "ACGT", "TGCA"]))
        self.assertEqual(
            DNASequence("A") + a,
            RawCRISPRArray(
                [DNASequence("A"), DNASequence("ACGT"), DNASequence("TGCA")]
            ),
        )
        self.assertEqual(
            [DNASequence("GG")] + a, RawCRISPRArray(["GG", "ACGT", "TGCA"])
        )
        self.assertEqual(
            ["TTT", "CCC"] + a, RawCRISPRArray(["TTT", "CCC", "ACGT", "TGCA"])
        )
        self.assertEqual(
            RawCRISPRArray(["GG", "TT"]) + a,
            RawCRISPRArray(["GG", "TT", "ACGT", "TGCA"]),
        )

        with self.assertRaises(ValueError):
            self.assertEqual("X" + a, RawCRISPRArray(["X", "ACGT", "TGCA"]))

        # Ambiguous! List of single characters will be converted to two single-base repeats, which may not be intended.
        with self.assertWarns(Warning):
            self.assertEqual(["T", "A"] + a, RawCRISPRArray(["T", "A", "ACGT", "TGCA"]))


if __name__ == "__main__":
    unittest.main()
