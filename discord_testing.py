import discord
import asyncio
from time import sleep

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

# Open the output file
log_file = open("discord_threads_log.txt", "w", encoding="utf-8")
name_file = open("discord_thread_names.txt", "w")

@client.event
async def on_ready():
    log_file.write(f"\n✅ Logged in as {client.user} ({client.user.id})\n\n")

    for guild in client.guilds:
        log_file.write(f"📂 Guild: {guild.name} ({guild.id})\n")
        if guild.id != 1387917204175192244:
            continue

        for channel in guild.text_channels:
            log_file.write(f"  📁 Channel: #{channel.name} ({channel.id})\n")
            if channel.name not in ["ninjas", "upper-belt", "jrs"]:
                continue

            try:
                # Active threads
                active_threads = channel.threads
                for thread in active_threads:
                    await log_thread_info(thread)
                    sleep(1)

                # Public archived threads
                archived_threads = await channel.archived_threads().flatten()
                for thread in archived_threads:
                    await log_thread_info(thread)

            except Exception as e:
                log_file.write(f"    ⚠️ Error accessing threads: {e}\n")

        log_file.write("\n")

    log_file.close()
    name_file.close()
    await client.close()


async def log_thread_info(thread):
    log_file.write(f"    🧵 Thread: {thread.name} ({thread.id}) [Archived: {thread.archived}]\n")
    name_file.write(f"{thread.name}\n")
    try:
        async for msg in thread.history(limit=10):
            log_file.write(f"      🗨️ Last Msg: {msg.author}: {msg.content}\n")
    except discord.Forbidden:
        log_file.write(f"      ❌ Can't read messages in thread (Forbidden)\n")
    except Exception as e:
        log_file.write(f"      ⚠️ Error reading messages: {e}\n")


# Replace with your bot token
with open("BOT_TOKEN.txt", "r") as fi:
    _tkn = str(fi.read())
    client.run(_tkn)
