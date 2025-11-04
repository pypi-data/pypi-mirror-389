from aiogram.types import Message

from aiogram_dialog import DialogManager, StartMode
from aioadmin.aiogram.handlers.states import Menu


async def start_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=Menu.get_tables, mode=StartMode.RESET_STACK)