from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Select, SwitchTo, Button, Group

from aioadmin.adapter import Adapter
from aioadmin.aiogram.handlers.states import Menu
from aioadmin.exceptions import ForeignKeyConstraintError


async def start_delete(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager):
    dialog_manager.dialog_data["selected_records"] = set()
    await dialog_manager.switch_to(Menu.delete_records)

async def toggle_record_selection(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    selected = dialog_manager.dialog_data.get("selected_records", set())
    if item_id in selected:
        selected.remove(item_id)
    else:
        selected.add(item_id)
    dialog_manager.dialog_data["selected_records"] = selected
    await dialog_manager.switch_to(Menu.delete_records)

async def delete_selected_handler(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager):
    adapter = dialog_manager.middleware_data["adapter"]
    current_table = dialog_manager.dialog_data["current_table"]
    selected = dialog_manager.dialog_data.get("selected_records", set())
    
    try:
        for pk_value_str in selected:
            try:
                pk_value = int(pk_value_str)
            except ValueError:
                pk_value = pk_value_str
            await adapter.delete_record(pk_value, current_table)
    except ForeignKeyConstraintError:
        await callback.message.answer(
            "Cannot delete: record is referenced by other records."
        )
    
    dialog_manager.dialog_data["selected_records"] = set()
    await dialog_manager.switch_to(Menu.get_table)

async def get_delete_records(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    current_table = dialog_manager.dialog_data["current_table"]
    record = await adapter.get_table(current_table)
    selected = dialog_manager.dialog_data.get("selected_records", set())
    
    records_data = []
    for idx, row in enumerate(record.rows):
        pk_value = row[0]   
        pk_str = str(pk_value)  
        is_selected = pk_str in selected
        
        row_display = " | ".join(str(val)[:20] for val in row[:3])  
        display_text = f"✓ {row_display}" if is_selected else row_display
        
        records_data.append({
            "pk": pk_str,
            "display": display_text,
            "is_selected": is_selected,
        })
    
    return {
        "records": records_data,
    }

delete_window = Window(
    Const("Select records to delete:"),
    Group(
        Select(
            Format("{item[display]}"),
            id="record_select",
            item_id_getter=lambda item: item["pk"],
            items="records",
            on_click=toggle_record_selection,
        ),
        width=1,
    ),
    Button(Const("Delete selected"), id="delete_selected", on_click=delete_selected_handler),
    SwitchTo(Const("Back"), id="back", state=Menu.get_table),
    getter=get_delete_records,
    state=Menu.delete_records,
)

