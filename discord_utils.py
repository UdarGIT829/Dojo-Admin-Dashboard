import asyncio
import discord

async def iterate_over_guild(guilds, log_file= None):
    student_threads = {}

    if not log_file:
        class mock_log:
            def write(self, _):
                pass
                # print(_)
        log_file = mock_log()

    for guild in guilds:
        log_file.write(f"📂 Guild: {guild.name} ({guild.id})\n")
        if guild.id != 1387917204175192244:
            continue
        for channel in guild.text_channels:
            log_file.write(f"  📁 Channel: #{channel.name} ({channel.id})\n")
            if channel.name not in [
                "ninjas", 
                "upper-belt", 
                "jrs"
                ]:
                continue

            try:
                # Active threads
                active_threads = channel.threads
                for thread in active_threads:
                    student_threads = await log_thread_info(thread, student_threads)
                    await asyncio.sleep(0.1)

                # # Public archived threads
                # archived_threads = await channel.archived_threads().flatten()
                # for thread in archived_threads:
                #     await log_thread_info(thread, student_threads)

            except Exception as e:
                log_file.write(f"    ⚠️ Error accessing threads: {e}\n")

        log_file.write("\n")
    return student_threads

async def log_thread_info(thread, student_threads):
    iterated_thread = []
    try:
        async for msg in thread.history(limit=10, oldest_first=True):
            iterated_thread.append(f"{msg.author}: {msg.content}")
        student_threads[thread.name.lower()] = iterated_thread
        return student_threads
    except discord.Forbidden:
        print("SOMETHING WAS FORBIDDEN")
    except Exception as e:
        print(f"Error: {e}")