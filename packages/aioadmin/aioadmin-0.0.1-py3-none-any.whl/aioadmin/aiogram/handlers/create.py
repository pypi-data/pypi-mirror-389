from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram.enums.parse_mode import ParseMode
from aiogram_dialog import Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import SwitchTo
from aiogram_dialog.widgets.input import MessageInput

from aioadmin.adapter import Adapter
from aioadmin.aiogram.handlers.states import Menu
from aioadmin.exceptions import TargetAlreadyExistsError


async def start_create(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager):
    adapter = dialog_manager.middleware_data["adapter"]
    current_table = dialog_manager.dialog_data["current_table"]
    tables = adapter.get_tables()
    columns = list(tables[current_table])
    
    dialog_manager.dialog_data["create_columns"] = columns
    dialog_manager.dialog_data["create_current_index"] = 0
    dialog_manager.dialog_data["create_data"] = {}
    
    await dialog_manager.switch_to(Menu.create_record)

async def process_field_input(message: Message, widget: Any, dialog_manager: DialogManager, **kwargs):
    current_index = dialog_manager.dialog_data.get("create_current_index", 0)
    columns = dialog_manager.dialog_data.get("create_columns", [])
    create_data = dialog_manager.dialog_data.get("create_data", {})
    
    if current_index < len(columns):
        field_name = columns[current_index]
        field_value = message.text
        
        create_data[field_name] = field_value
        dialog_manager.dialog_data["create_data"] = create_data
        
        next_index = current_index + 1
        dialog_manager.dialog_data["create_current_index"] = next_index
        
        if next_index >= len(columns):
            adapter = dialog_manager.middleware_data["adapter"]
            current_table = dialog_manager.dialog_data["current_table"]
            try:
                await adapter.create_record(create_data, current_table)
            except TargetAlreadyExistsError:
                await message.answer("Record already exists")
                await dialog_manager.switch_to(Menu.create_record)
            
            dialog_manager.dialog_data.pop("create_columns", None)
            dialog_manager.dialog_data.pop("create_current_index", None)
            dialog_manager.dialog_data.pop("create_data", None)
            await dialog_manager.switch_to(Menu.get_table)
        else:
            await dialog_manager.switch_to(Menu.create_record)

async def get_create_record(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    current_index = dialog_manager.dialog_data.get("create_current_index", 0)
    columns = dialog_manager.dialog_data.get("create_columns", [])
    
    if current_index < len(columns):
        current_field = columns[current_index]
        total_fields = len(columns)
        return {
            "field_name": current_field,
            "field_number": current_index + 1,
            "total_fields": total_fields,
        }
    
    return {
        "field_name": "",
        "field_number": 0,
        "total_fields": 0,
    }

create_window = Window(
    Format("Creating record: {field_number}/{total_fields}"),
    Format("Enter value for field: *{field_name}*"),
    MessageInput(process_field_input),
    SwitchTo(Const("Cancel"), id="cancel", state=Menu.get_table),
    getter=get_create_record,
    state=Menu.create_record,
    parse_mode=ParseMode.MARKDOWN,
)