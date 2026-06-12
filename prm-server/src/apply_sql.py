import asyncio
import os
import asyncpg

async def apply():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgresql+asyncpg", "postgresql"))
    with open('/tmp/migration.sql', 'r') as f:
        sql = f.read()
    await conn.execute(sql)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(apply())
