from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

class AdaperMiddleware(BaseMiddleware):
    def __init__(self, adapter):
        self.adapter = adapter

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        data['adapter'] = self.adapter
        return await handler(event, data)