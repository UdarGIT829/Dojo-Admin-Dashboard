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
                "upper belt", 
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

import asyncio
import discord

TARGET_CHANNELS = {"ninjas", "upper belt", "jrs"}

async def set_threads_auto_archive_24h(
    guilds,
    *,
    include_archived: bool = True,
    dry_run: bool = False,
    log_file=None,
    sleep_s: float = 0.1,
) -> dict[str, int]:
    """
    For every guild in `guilds`, set all threads in TARGET_CHANNELS to 24h auto-archive.

    Args:
        guilds: Iterable of guilds.
        include_archived: Whether to also scan archived threads.
        dry_run: If True, only log which threads would be updated.
        log_file: File-like for writing logs.
        sleep_s: Delay between requests.

    Returns:
        {"checked": N, "updated": M, "errors": E}
    """
    if not log_file:
        class _NullLog:
            def write(self, _): ...
        log_file = _NullLog()

    stats = {"checked": 0, "updated": 0, "errors": 0}

    for guild in guilds:
        for channel in getattr(guild, "text_channels", []):
            if channel.name not in TARGET_CHANNELS:
                continue
            print(f"Counting active #{channel.name} threads...")
            total = len(list(channel.threads))
            counter = 1
            print()
            
            # Active threads
            for thread in list(channel.threads):
                print(f"Scanning #{channel.name} threads: {counter}/{total}",end="\r")
                await _ensure_24h(thread, stats, log_file, dry_run=dry_run)
                await asyncio.sleep(sleep_s)
                counter += 1
            print()

            if not include_archived:
                continue

            # Archived threads (public and private)
            try:
                async for thread in channel.archived_threads(private=False, limit=None):
                    await _ensure_24h(thread, stats, log_file, dry_run=dry_run)
                    await asyncio.sleep(sleep_s)
            except Exception as e:
                log_file.write(f"    ⚠️ Error listing public archived in #{channel.name}: {e}\n")

            try:
                async for thread in channel.archived_threads(private=True, limit=None):
                    await _ensure_24h(thread, stats, log_file, dry_run=dry_run)
                    await asyncio.sleep(sleep_s)
            except Exception as e:
                log_file.write(f"    ⚠️ Error listing private archived in #{channel.name}: {e}\n")

    return stats


async def _ensure_24h(thread: discord.Thread, stats: dict, log_file, *, dry_run: bool = False):
    """Idempotently set a single thread to 24h auto-archive, preserving archived state."""
    stats["checked"] += 1
    try:
        if getattr(thread, "auto_archive_duration", None) == 1440:
            return  # already 24h

        was_archived = getattr(thread, "archived", False)

        if dry_run:
            stats["updated"] += 1
            log_file.write(f"    [DRY RUN] Would set 24h: {thread.guild.name} / #{thread.parent.name} / 🧵 {thread.name}\n")
            return

        # If archived, temporarily unarchive to allow edits
        if was_archived:
            await thread.edit(archived=False)

        await thread.edit(auto_archive_duration=1440)
        stats["updated"] += 1
        log_file.write(f"    ✅ Set 24h: {thread.guild.name} / #{thread.parent.name} / 🧵 {thread.name}\n")

        if was_archived:
            await thread.edit(archived=True)

    except discord.Forbidden:
        stats["errors"] += 1
        log_file.write(f"    ⛔ Forbidden editing: {thread.guild.name} / #{thread.parent.name} / 🧵 {thread.name}\n")
    except discord.HTTPException as e:
        stats["errors"] += 1
        log_file.write(f"    ⚠️ HTTP error on {thread.name}: {e}\n")
    except Exception as e:
        stats["errors"] += 1
        log_file.write(f"    ⚠️ Unexpected error on {thread.name}: {e}\n")


async def find_candidate_guilds(client: discord.Client, channels: set[str] = TARGET_CHANNELS):
    """
    Return list of (guild, present, missing) where:
      - present: channel names found in the guild
      - missing: required channel names not found
    Channel name match is case-insensitive.
    """
    results = []
    need = {c.casefold() for c in channels}

    for guild in client.guilds:
        # Collect all text channel names in this guild (case-insensitive)
        have = {ch.name.casefold() for ch in getattr(guild, "text_channels", [])}
        present = {c for c in channels if c.casefold() in have}
        missing = {c for c in channels if c.casefold() not in have}
        results.append((guild, present, missing))
    return results


# if __name__ == "__main__":
#     import asyncio
#     from discord_client import _client, TOKEN_FILE  # reuse the same token path

#     async def _print_candidate_guilds_and_exit():
#         await _client.wait_until_ready()
#         results = await find_candidate_guilds(_client, TARGET_CHANNELS)

#         print("\n=== Candidate Guilds (by required channels) ===")
#         for guild, present, missing in results:
#             print(f"- {guild.name} [{guild.id}]")
#             print(f"    present: {sorted(present)}")
#             print(f"    missing: {sorted(missing)}")
#         print("=== End ===\n")

#         await _client.close()

#     async def _runner():
#         # run the printer once the client is ready, then exit
#         asyncio.create_task(_print_candidate_guilds_and_exit())
#         token = TOKEN_FILE.read_text().strip()
#         await _client.start(token)

#     asyncio.run(_runner())

if __name__ == "__main__":
    import asyncio
    import argparse
    from discord_client import _client, TOKEN_FILE  # reuse the same token path

    parser = argparse.ArgumentParser(description="Set threads in target channels to 24h auto-archive.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry-run). Omit to only show what would change."
    )
    parser.add_argument(
        "--no-archived",
        action="store_true",
        help="Skip scanning archived threads (default scans both active and archived)."
    )
    args = parser.parse_args()

    async def _run_update_and_exit():
        logfile_name = "log.txt"
        with open(logfile_name,"w") as log_fi:
            await _client.wait_until_ready()
            stats = await set_threads_auto_archive_24h(
                _client.guilds,
                include_archived=not args.no_archived,
                dry_run=not args.apply,  # default dry-run unless --apply is passed,
                log_file=log_fi
            )
            print("\n=== set_threads_auto_archive_24h summary ===")
            print(stats)
            print("=== End ===\n")
            print(f"Log saved to {logfile_name}")
            if not args.apply:
                print("This was a dry run, check the log file then rerun this command with '--apply'")
                print("python discord_utils.py --apply")
                print()

            await _client.close()

    async def _runner():
        token = TOKEN_FILE.read_text().strip()
        # Kick off the updater after startup; let client.run lifecycle handle cleanup.
        updater_task = asyncio.create_task(_run_update_and_exit())
        try:
            await _client.start(token)  # returns when client is closed
        finally:
            # Make absolutely sure the aiohttp connector is closed to avoid warnings.
            if not updater_task.done():
                # If the updater is still running for some reason, let it finish/cancel gracefully.
                try:
                    await updater_task
                except asyncio.CancelledError:
                    pass
            await _client.close()

    asyncio.run(_runner())

