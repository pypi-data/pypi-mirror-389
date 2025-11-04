from typing import Any

from aioadmin.adapter import Adapter
from aioadmin.record import Record

class PermissionDeniedError(Exception):
    pass


class PermissionPolicy(Adapter):
    def __init__(
        self,
        adapter: Adapter,
        can_view: bool = True,
        can_create: bool = True,
        can_delete: bool = True,
        can_edit: bool = True,
    ):
        self.adapter = adapter
        self.can_view = can_view
        self.can_create = can_create
        self.can_delete = can_delete
        self.can_edit = can_edit
    
    async def get_tables(self):
        if not self.can_view:
            raise PermissionDeniedError("Cannot get information of tables")
        return await self.adapter.get_tables()

    async def get_table(self, table_name: str):
        if not self.can_view:
            raise PermissionDeniedError("Cannot get information from a table")
        return await self.adapter.get_table(table_name=table_name)
    
    async def get_record_detail(self, pk_value: Any, table_name: str):
        if not self.can_view:
            raise PermissionDeniedError("Cannot get detail information of a record")
        return await self.adapter.get_record_detail(pk_value=pk_value, table_name=table_name)

    async def create_record(self, data: dict[str, Any], table_name: str) -> Record:
        if not self.can_create:
            raise PermissionDeniedError("Cannot create a record")
        return await self.adapter.create_record(data=data, table_name=table_name)

    async def update_record(self, pk_value: Any, data: dict[str, Any], table_name: str) -> Record:
        if not self.can_edit:
            raise PermissionDeniedError("Cannot update a record")
        return await self.adapter.update_record(pk_value=pk_value, data=data, table_name=table_name)

    async def delete_record(self, pk_value: Any, table_name: str) -> Record:
        if not self.can_delete:
            raise PermissionDeniedError("Cannot delete a record")
        return await self.adapter.delete_record(pk_value=pk_value, table_name=table_name)
