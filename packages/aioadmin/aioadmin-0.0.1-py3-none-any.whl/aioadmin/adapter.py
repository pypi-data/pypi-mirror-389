from typing import Any
from abc import ABC, abstractmethod

from aioadmin.record import Record


class Adapter(ABC):
    @abstractmethod
    def get_tables(self) -> dict[tuple[str]]:
        raise NotImplementedError

    @abstractmethod
    async def get_table(self, table_name: str) -> Record:
        raise NotImplementedError

    @abstractmethod
    async def get_record_detail(self, pk_value: Any, table_name: str) -> Record:
        raise NotImplementedError

    @abstractmethod
    async def create_record(self, data: dict[str, Any], table_name: str) -> Record:
        raise NotImplementedError

    @abstractmethod
    async def update_record(self, pk_value: Any, data: dict[str, Any], table_name: str) -> Record:
        raise NotImplementedError

    @abstractmethod
    async def delete_record(self, pk_value: Any, table_name: str) -> Record:
        raise NotImplementedError
