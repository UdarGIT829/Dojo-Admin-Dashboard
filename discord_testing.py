import discord
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"\n✅ Logged in as {client.user} ({client.user.id})\n")

    for guild in client.guilds:
        print(f"📂 Guild: {guild.name} ({guild.id})")

        for channel in guild.text_channels:
            print(f"  📁 Channel: #{channel.name} ({channel.id})")

            try:
                # Active threads
                active_threads = channel.threads
                for thread in active_threads:
                    await print_thread_info(thread)

                # Public archived threads
                archived_threads = await channel.archived_threads().flatten()
                for thread in archived_threads:
                    await print_thread_info(thread)

            except Exception as e:
                print(f"    ⚠️ Error accessing threads: {e}")

        print()

    await client.close()


async def print_thread_info(thread):
    print(f"    🧵 Thread: {thread.name} ({thread.id}) [Archived: {thread.archived}]")
    try:
        async for msg in thread.history(limit=1):
            print(f"      🗨️ Last Msg: {msg.author}: {msg.content}")
    except discord.Forbidden:
        print(f"      ❌ Can't read messages in thread (Forbidden)")
    except Exception as e:
        print(f"      ⚠️ Error reading messages: {e}")


# Replace with your bot token
with open("BOT_TOKEN.txt","r") as fi:
    _tkn = str(fi.read())
    client.run(_tkn)
