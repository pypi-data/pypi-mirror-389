from typing import Any

from aiogram.types import CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram_dialog import Window, Dialog, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Select, SwitchTo, Button

from aioadmin.adapter import Adapter
from aioadmin.aiogram.handlers.states import Menu
from aioadmin.aiogram.handlers.create import start_create, create_window
from aioadmin.aiogram.handlers.update import start_update, update_select_record_window, update_select_column_window, update_field_value_window
from aioadmin.aiogram.handlers.delete import start_delete, delete_window


async def set_current_table(callback: CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data["current_table"] = item_id
    await dialog_manager.switch_to(Menu.get_table)

async def get_tables(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    return { "tables": adapter.get_tables().keys() }

async def get_table(adapter: Adapter, dialog_manager: DialogManager, **kwargs):
    current_table = dialog_manager.dialog_data["current_table"]
    record = await adapter.get_table(current_table)

    columns = [str(column) for column in record.columns]
    column_widths = [len(column) for column in columns]
    rendered_rows = []

    for row in record.rows:
        rendered_row = [str(value) for value in row]
        for idx, value in enumerate(rendered_row):
            column_widths[idx] = max(column_widths[idx], len(value))
        rendered_rows.append(rendered_row)

    header_line = " | ".join(column.ljust(column_widths[idx]) for idx, column in enumerate(columns))
    separator_line = "---".join("-" * column_widths[idx] for idx in range(len(columns)))

    formatted_rows = [
        " | ".join(rendered_row[idx].ljust(column_widths[idx]) for idx in range(len(columns)))
        for rendered_row in rendered_rows
    ]

    table_lines = [header_line, separator_line, *formatted_rows] if columns else []
    rendered_table = "```table\n" + "\n".join(table_lines) + "\n```" if table_lines else ""

    return {
        "name": record.name.capitalize(),
        "table": rendered_table,
    }


menu_dialog = Dialog(
    Window(
        Const("Admin panel ⚙️"),
        Const("Tables: "),
        Select(Format("{item}"), id="menu", item_id_getter=lambda item: item, items="tables", on_click=set_current_table),
        getter=get_tables,
        state=Menu.get_tables,
    ),
    Window(
        Format('*{name}*'),
        Format("{table}"),
        Button(Const("Create"), id="create", on_click=start_create),
        Button(Const("Update"), id="update", on_click=start_update),
        Button(Const("Delete"), id="delete", on_click=start_delete),
        SwitchTo(Const("Return to menu"), id="table", state=Menu.get_tables),
        getter=get_table,
        state=Menu.get_table,
        parse_mode=ParseMode.MARKDOWN,
    ),
    create_window,
    delete_window,
    update_select_record_window,
    update_select_column_window,
    update_field_value_window,
)
