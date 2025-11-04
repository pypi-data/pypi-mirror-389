from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram.enums.parse_mode import ParseMode
from aiogram_dialog import Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Select, SwitchTo, Group
from aiogram_dialog.widgets.input import MessageInput

from aioadmin.adapter import Adapter
from aioadmin.aiogram.handlers.states import Menu
from aioadmin.exceptions import TargetAlreadyExistsError


async def start_update(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager):
    await dialog_manager.switch_to(Menu.select_record_to_update)

async def select_record_to_update(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data["update_record_pk"] = item_id
    
    adapter = dialog_manager.middleware_data["adapter"]
    current_table = dialog_manager.dialog_data["current_table"]
    tables = adapter.get_tables()
    columns = list(tables[current_table])
    
    dialog_manager.dialog_data["update_columns"] = columns
    await dialog_manager.switch_to(Menu.select_column_to_update)

async def select_column_to_update(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data["update_column"] = item_id
    await dialog_manager.switch_to(Menu.update_field_value)

async def process_update_field_input(message: Message, widget: Any, dialog_manager: DialogManager, **kwargs):
    adapter = dialog_manager.middleware_data["adapter"]
    current_table = dialog_manager.dialog_data["current_table"]
    record_pk_str = dialog_manager.dialog_data.get("update_record_pk")
    column_name = dialog_manager.dialog_data.get("update_column")
    new_value = message.text
    
    try:
        pk_value = int(record_pk_str)
    except ValueError:
        pk_value = record_pk_str
    
    update_data = {column_name: new_value}
    try:
        await adapter.update_record(pk_value, update_data, current_table)
    except TargetAlreadyExistsError:
        await message.answer("Record already exists")
        await dialog_manager.switch_to(Menu.update_field_value)
    
    dialog_manager.dialog_data.pop("update_record_pk", None)
    dialog_manager.dialog_data.pop("update_column", None)
    dialog_manager.dialog_data.pop("update_columns", None)
    
    await dialog_manager.switch_to(Menu.get_table)

async def get_update_records(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    current_table = dialog_manager.dialog_data["current_table"]
    record = await adapter.get_table(current_table)
    
    records_data = []
    for idx, row in enumerate(record.rows):
        pk_value = row[0]
        pk_str = str(pk_value)
        
        row_display = " | ".join(str(val)[:20] for val in row[:3])
        
        records_data.append({
            "pk": pk_str,
            "display": row_display,
        })
    
    return {
        "records": records_data,
    }

async def get_update_columns(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    columns = dialog_manager.dialog_data.get("update_columns", [])
    
    columns_data = []
    for column in columns:
        columns_data.append({
            "name": column,
            "display": column,
        })
    
    return {
        "columns": columns_data,
    }

async def get_update_field_value(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    column_name = dialog_manager.dialog_data.get("update_column", "")
    
    adapter_instance = dialog_manager.middleware_data["adapter"]
    current_table = dialog_manager.dialog_data["current_table"]
    record_pk_str = dialog_manager.dialog_data.get("update_record_pk", "")
    
    try:
        pk_value = int(record_pk_str)
    except ValueError:
        pk_value = record_pk_str
    
    record = await adapter_instance.get_record_detail(pk_value, current_table)
    current_value = str(record.rows[0][record.columns.index(column_name)]) if record.rows else ""
    
    return {
        "column_name": column_name,
        "current_value": current_value,
    }

update_select_record_window = Window(
    Const("Select record to update:"),
    Group(
        Select(
            Format("{item[display]}"),
            id="record_select",
            item_id_getter=lambda item: item["pk"],
            items="records",
            on_click=select_record_to_update,
        ),
        width=1,
    ),
    SwitchTo(Const("Back"), id="back", state=Menu.get_table),
    getter=get_update_records,
    state=Menu.select_record_to_update,
)

update_select_column_window = Window(
    Const("Select column to update:"),
    Group(
        Select(
            Format("{item[display]}"),
            id="column_select",
            item_id_getter=lambda item: item["name"],
            items="columns",
            on_click=select_column_to_update,
        ),
        width=1,
    ),
    SwitchTo(Const("Back"), id="back", state=Menu.get_table),
    getter=get_update_columns,
    state=Menu.select_column_to_update,
)

update_field_value_window = Window(
    Format("Updating field: *{column_name}*"),
    Format("Current value: {current_value}"),
    Format("Enter new value:"),
    MessageInput(process_update_field_input),
    SwitchTo(Const("Cancel"), id="cancel", state=Menu.get_table),
    getter=get_update_field_value,
    state=Menu.update_field_value,
    parse_mode=ParseMode.MARKDOWN,
)

