import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [r[0] for r in result]
        print("TABLES IN DB:", tables)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
