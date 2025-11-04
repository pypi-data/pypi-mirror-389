from faker import Faker

from aioadmin.record import Record


def test_record_empty():
    record = Record(name="", columns=(), rows=())

    assert record.name == ""
    assert record.columns == ()
    assert record.rows == ()


def test_record_table(faker: Faker):
    name = faker.word()
    columns = tuple(faker.word() for _ in range(3))
    rows = tuple(tuple(faker.word() for _ in range(3)) for _ in range(3))
    record = Record(
        name=name,
        columns=columns,
        rows=rows,
    )

    assert record.name == name
    assert record.columns == columns
    assert record.rows == rows