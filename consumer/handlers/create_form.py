from typing import Any, Dict

from sqlalchemy import select

from src.model.model import User
from src.storage.db import async_session


async def create_form(body: Dict[str, Any]) -> None:
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == body.get('id')))
        user = result.scalar_one()

        user = User(
            user_id=body.get('id'),
            name=body.get('name'),
            age=body.get('age'),
            gender=body.get('gender'),
            city=body.get('city'),
            interests=body.get('interests'),
            preferred_gender=body.get('preferred_gender'),
            preferred_age_min=body.get('preferred_age_min'),
            preferred_age_max=body.get('preferred_age_max'),
            preferred_city=body.get('preferred_city'),
        )
        
        db.add(user)
        await db.commit()