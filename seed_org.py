import asyncio
from app.core.database import async_session_maker
from app.models.collaboration import Organization

async def create_org():
    async with async_session_maker() as db:
        org = Organization(name="Vibrant Academic Press")
        db.add(org)
        await db.commit()
        print("Organization created successfully!")

if __name__ == "__main__":
    asyncio.run(create_org())
