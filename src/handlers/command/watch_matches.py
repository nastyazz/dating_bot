import msgpack
from aiogram import Router
from aio_pika import ExchangeType
from src.storage.rabbit import channel_pool
from src.handlers.state.like_profile import LikedProfilesFlow
from src.handlers.command.menu import menu
from src.handlers.command.router import router
from aiogram.fsm.context import FSMContext
from config.settings import settings
import aio_pika
import msgpack
from aio_pika import ExchangeType
import asyncio
from aiogram import F
from src.handlers.state.show_next_user import show_next_liked_user
from aiogram.types import CallbackQuery, Message

@router.callback_query(F.data == "my_matches")
async def my_matches_handler(call: CallbackQuery, state: FSMContext, message: Message):
    user_id = message.from_user.id
    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange(
                "user_form", ExchangeType.TOPIC, durable=True
            )
        
        user_queue = await channel.declare_queue("user_messages", durable=True)

        await user_queue.bind(exchange, 'user_messages')
        queue = await channel.declare_queue(
            settings.USER_QUEUE.format(user_id=user_id), durable=True
        )

        body = {
            "id": call.from_user.id,
            "action": "get_my_matches",
        }

        await exchange.publish(aio_pika.Message(msgpack.packb(body)), routing_key="user_messages")

        await call.message.answer("Проверяю ваши мэтчи...")

        retries = 3
        for _ in range(retries):
            try:
                res = await queue.get(timeout=5)
                await res.ack()
                data = msgpack.unpackb(res.body)

                matches = data.get("matches", [])
                if matches:
                    await state.set_state(LikedProfilesFlow.viewing)
                    await state.set_data({"likes": matches, "current_index": 0})
                    await show_next_liked_user(call, state)
                    return
                else:
                    await call.message.answer("У вас нет взаимных лайков.")
                    return
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)

        await call.message.answer("Не удалось получить ваши мэтчи. Попробуйте позже.")

