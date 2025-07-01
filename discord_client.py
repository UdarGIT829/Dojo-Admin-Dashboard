import asyncio
import discord
from discord_utils import iterate_over_guild   # your existing helper
from pathlib import Path

TOKEN_FILE = Path(__file__).with_name("BOT_TOKEN.txt")

# ---- public, importable state ---------------------------------------------
STUDENT_THREADS: dict[str, list[str]] = {}   # {student_name_lower: [msg str, …]}
PULL_IN_PROGRESS = False                     # simple flag the UI can poll
# ---------------------------------------------------------------------------

_intents = discord.Intents.default()
_intents.guilds = True
_intents.messages = True
_intents.message_content = True

_client = discord.Client(intents=_intents)

@_client.event
async def on_ready():
    await pull_threads_once()               # initial load then stay connected

async def _fetch_threads():
    global STUDENT_THREADS
    student_threads = await iterate_over_guild(_client.guilds)
    STUDENT_THREADS = student_threads       # replace atomically

async def pull_threads_once():
    """Refresh STUDENT_THREADS one time; safe to await from outside."""
    global PULL_IN_PROGRESS
    if PULL_IN_PROGRESS:
        print("PULL Already running!")
        return                              # already running
    PULL_IN_PROGRESS = True
    try:
        await _fetch_threads()
    finally:
        PULL_IN_PROGRESS = False
        print(f"Pulled {len(list(STUDENT_THREADS.keys()))} threads.")

def start_background_client():
    """
    Fire-and-forget: starts Discord in a dedicated asyncio thread so your
    PyQt app can import this module and immediately see live thread data.
    """
    if _client.is_ready():
        return

    async def _runner():
        token = TOKEN_FILE.read_text().strip()
        await _client.start(token)

    loop = asyncio.new_event_loop()

    import threading
    threading.Thread(target=loop.run_until_complete,
                     args=(_runner(),),
                     daemon=True).start()

def trigger_refresh() -> asyncio.Future:
    """
    Schedule a refresh on the *client* loop and return the Future so callers
    can add callbacks if they want.
    """
    return asyncio.run_coroutine_threadsafe(pull_threads_once(), _client.loop)