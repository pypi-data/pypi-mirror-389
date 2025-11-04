from typing import Iterable, Sequence
from sqlalchemy.engine.result import Result


class Record:
    __slots__ = ("_name", "_columns", "_rows")

    def __init__(self, *, name: str, columns: Sequence[str], rows: Iterable[Sequence[object]]):
        self._name = name
        self._columns = tuple(columns)
        self._rows = tuple(tuple(row) for row in rows)

    @property
    def name(self) -> str:
        return self._name

    @property
    def columns(self) -> tuple[str, ...]:
        return self._columns

    @property
    def rows(self) -> tuple[tuple[object, ...], ...]:
        return self._rows

    def __iter__(self) -> Iterable[tuple[object, ...]]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def __repr__(self) -> str:
        return f"Record(name={self._name!r}, columns={self._columns!r}, rows={self._rows!r})"


def sqlalchemy_to_record(name: str, result: Result) -> Record:
    return Record(name=name, columns=result.keys(), rows=result.all())
