import pytest
from unittest.mock import create_autospec

from aioadmin.adapter import Adapter
from aioadmin.permissions import PermissionPolicy, PermissionDeniedError


async def test_default():
    mock_adapter = create_autospec(Adapter)
    permission_policy = PermissionPolicy(adapter=mock_adapter)

    await permission_policy.get_tables()
    await permission_policy.get_table("")
    await permission_policy.get_record_detail("", "")
    await permission_policy.create_record({}, "")
    await permission_policy.update_record("", {}, "")
    await permission_policy.delete_record("", "")

    mock_adapter.get_tables.assert_awaited_once()
    mock_adapter.get_table.assert_awaited_once()
    mock_adapter.get_record_detail.assert_awaited_once()
    mock_adapter.create_record.assert_awaited_once()
    mock_adapter.update_record.assert_awaited_once()
    mock_adapter.delete_record.assert_awaited_once()


async def test_can_view():
    mock_adapter = create_autospec(Adapter)
    permission_policy = PermissionPolicy(adapter=mock_adapter, can_view=False, can_create=True, can_delete=True, can_edit=True)

    with pytest.raises(PermissionDeniedError):
        await permission_policy.get_tables()
    with pytest.raises(PermissionDeniedError):
        await permission_policy.get_table("")
    with pytest.raises(PermissionDeniedError):
        await permission_policy.get_record_detail("", "")

    mock_adapter.get_tables.assert_not_awaited()
    mock_adapter.get_table.assert_not_awaited()
    mock_adapter.get_record_detail.assert_not_awaited()


async def test_can_create():
    mock_adapter = create_autospec(Adapter)
    permission_policy = PermissionPolicy(adapter=mock_adapter, can_create=False, can_view=True, can_delete=True, can_edit=True)

    with pytest.raises(PermissionDeniedError):
        await permission_policy.create_record({}, "")

    mock_adapter.create_record.assert_not_awaited()


async def test_can_edit():
    mock_adapter = create_autospec(Adapter)
    permission_policy = PermissionPolicy(adapter=mock_adapter, can_edit=False, can_view=True, can_create=True, can_delete=True)

    with pytest.raises(PermissionDeniedError):
        await permission_policy.update_record("", {}, "")

    mock_adapter.update_record.assert_not_awaited()


async def test_can_delete():
    mock_adapter = create_autospec(Adapter)
    permission_policy = PermissionPolicy(adapter=mock_adapter, can_delete=False, can_view=True, can_create=True, can_edit=True)

    with pytest.raises(PermissionDeniedError):
        await permission_policy.delete_record("", "")

    mock_adapter.delete_record.assert_not_awaited()
