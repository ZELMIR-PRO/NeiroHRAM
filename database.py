import aiosqlite
import time

DB_PATH = "neyrohram.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                plan TEXT DEFAULT 'free',
                messages_used INTEGER DEFAULT 0,
                messages_limit INTEGER DEFAULT 20,
                plan_expires INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                return dict(row)
            # New user — create with free plan
            now = int(time.time())
            expires = now + 30 * 24 * 3600  # 30 days
            await db.execute(
                "INSERT INTO users (user_id, plan, messages_used, messages_limit, plan_expires, created_at) VALUES (?,?,?,?,?,?)",
                (user_id, "free", 0, 20, expires, now)
            )
            await db.commit()
            return {"user_id": user_id, "plan": "free", "messages_used": 0, "messages_limit": 20, "plan_expires": expires}

async def can_send_message(user_id: int) -> tuple[bool, dict]:
    user = await get_user(user_id)
    now = int(time.time())

    # Check if plan expired — reset to free
    if user["plan_expires"] > 0 and now > user["plan_expires"]:
        async with aiosqlite.connect(DB_PATH) as db:
            new_expires = now + 30 * 24 * 3600
            await db.execute(
                "UPDATE users SET plan='free', messages_used=0, messages_limit=20, plan_expires=? WHERE user_id=?",
                (new_expires, user_id)
            )
            await db.commit()
        user = await get_user(user_id)

    allowed = user["messages_used"] < user["messages_limit"]
    return allowed, user

async def increment_messages(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET messages_used = messages_used + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def upgrade_plan(user_id: int, plan: str, limit: int):
    now = int(time.time())
    expires = now + 30 * 24 * 3600
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET plan=?, messages_limit=?, messages_used=0, plan_expires=? WHERE user_id=?",
            (plan, limit, expires, user_id)
        )
        await db.commit()
