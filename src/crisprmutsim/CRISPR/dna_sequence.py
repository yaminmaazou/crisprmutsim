from collections.abc import MutableSequence, Iterable, Iterator
from typing import Self, cast, overload


IUPAC_BASES = "ACGTRYSWKMBDHVN"


class DNASequence(MutableSequence[str]):
    def __init__(self, sequence: Iterable[str] = "", unsafe: bool = False) -> None:
        self.sequence: list[str]
        if unsafe:
            self.sequence: list[str] = cast(list[str], sequence)
        else:
            self.sequence = self._convert_sequence(sequence)

    def _convert_sequence(self, sequence: Iterable[str]) -> list[str]:
        if isinstance(sequence, DNASequence):
            return sequence.sequence.copy()

        sequence = [base.upper() for base in sequence]
        if not all(base in IUPAC_BASES and len(base) == 1 for base in sequence):
            raise ValueError(f"Invalid base in sequence: {sequence}")
        return sequence

    def __unsafe_setitem__(self, index: int, value: str) -> None:
        self.sequence[index] = value

    #############################################################################
    # Dunder methods for MutableSequence interface and additional functionality #
    #############################################################################

    @overload
    def __getitem__(self, index: int) -> str: ...
    @overload
    def __getitem__(self, index: slice) -> list[str]: ...
    def __getitem__(self, index: int | slice) -> str | list[str]:
        return self.sequence[index]

    @overload
    def __setitem__(self, index: int, value: str) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[str]) -> None: ...
    def __setitem__(self, index: int | slice, value: str | Iterable[str]) -> None:
        value = self._convert_sequence(value)
        if isinstance(index, slice):
            self.sequence[index] = value
        else:
            if len(value) != 1:
                raise ValueError(f"Invalid base: {value}.")
            self.sequence[index] = value[0]

    @overload
    def __delitem__(self, index: int) -> None: ...
    @overload
    def __delitem__(self, index: slice) -> None: ...
    def __delitem__(self, index: int | slice) -> None:
        del self.sequence[index]

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, Iterable):
            raise TypeError(f"Invalid type for value: {type(value)}.")
        # explicit cast, since pyright/mypy don't allow explicit checks for each element (yet)
        # see https://github.com/microsoft/pyright/discussions/10472
        value = cast(Iterable[str], value)
        value = self._convert_sequence(value)
        return "".join(value) in "".join(self.sequence)

    def __len__(self) -> int:
        return len(self.sequence)

    def insert(self, index: int, value: str) -> None:
        value = value.upper()
        if len(value) != 1 or value not in IUPAC_BASES:
            raise ValueError(f"Invalid base: {value}.")
        self.sequence.insert(index, value)

    def __iter__(self) -> Iterator[str]:
        return iter(self.sequence)

    def __eq__(self, other: object) -> bool:
        if isinstance(
            other, DNASequence
        ):  # slightly faster than isinstance(other, Iterable)
            return self.sequence == other.sequence
        elif isinstance(other, str):
            return "".join(self.sequence) == other.upper()
        elif isinstance(other, Iterable):
            other = cast(Iterable[str], other)  # see comment in __contains__
            return "".join(self.sequence) == "".join(other).upper()
        return False

    def __str__(self) -> str:
        return "".join(self.sequence)

    def __repr__(self) -> str:
        return self.__str__()

    # Support concat using '+'
    def __add__(self, value: Iterable[str]) -> "DNASequence":
        # ugly try-except
        # necessary, since static type checkers don't fully support the __add__ / __radd__ synergy (yet)
        # technically, we could use value: object instead,
        #   but that would require explicit casting because of Iterable[str] vs str (see comment in __contains__)
        # ideally, pyright/mypy should allow us to use isinstance here
        # see also https://github.com/python/mypy/issues/18945
        try:
            return DNASequence(self.sequence + DNASequence(value).sequence)
        except AttributeError:
            # not an error yet; instructs Python to try value.__radd__ instead
            return NotImplemented

    # Override generated mixin method to account for custom __add__ behavior
    def __iadd__(self, value: Iterable[str]) -> Self:
        try:
            self.sequence += DNASequence(value).sequence
        except AttributeError:
            # prevent value.__radd__ from being called
            raise ValueError(f"Invalid value for concatenation: {value}.")
        return self

    # Support left insertions using '+'
    def __radd__(self, value: Iterable[str]) -> "DNASequence":
        return DNASequence(value) + self.sequence
