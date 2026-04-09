import os
import asyncio
import discord
from .filters import BLACKLIST, DEATH_MESSAGES


async def read_log(client):
    await client.wait_until_ready()

    console_channel = client.get_channel(int(os.getenv("CONSOLE_CHANNEL_ID")))
    events_channel = client.get_channel(int(os.getenv("EVENTS_CHANNEL_ID")))

    webhooks = await events_channel.webhooks()
    webhook = discord.utils.get(webhooks, name="CobbleBot Chat")
    if not webhook:
        webhook = await events_channel.create_webhook(name="CobbleBot Chat")

    log_path = os.getenv("LOG_PATH")
    while True:
        try:
            log = open(log_path,"r", encoding="utf-8")
            break
        except Exception as e:
            print(f"Log file not found: {e}")
            await asyncio.sleep(5)   
    
    log.seek(0, 2)

    while True:
        if os.path.getsize(log_path) < log.tell():
            log.close()
            try:
                log = open(log_path,"r", encoding="utf-8")
            except Exception as e:
                print(f"Log file not found: {e}")
                await asyncio.sleep(5)
                continue
            

        new_lines = log.read().splitlines()
        console_lines = []
        batch_length = 0
        for line in new_lines:

            if "]: " not in line:
                continue

            if any(phrase in line for phrase in BLACKLIST):
                continue

            if batch_length + len(line) + 1 > 2000:
                await console_channel.send("\n".join(console_lines))
                console_lines = [line]
                batch_length = len(line) + 1
            else:
                console_lines.append(line)
                batch_length += len(line) + 1

            line = line.split("]: ", 1)[1]

            if any(phrase in line for phrase in DEATH_MESSAGES):
                await events_channel.send(f":skull: {line}.")
            elif "For help, type" in line:
                await events_channel.send(f":white_check_mark: The server has started!")
            elif "Stopping the server" in line:
                await events_channel.send(f":x: The server has stopped.")
            elif "joined the game" in line:
                await events_channel.send(f":arrow_right: {line}.")
            elif "left the game" in line:
                await events_channel.send(f":arrow_left: {line}.")
            elif "has made the advancement" in line:
                await events_channel.send(f":trophy: {line}.")
            elif "has completed the challenge" in line:
                await events_channel.send(f":medal: {line}.")
            elif "has reached the goal" in line:
                await events_channel.send(f":medal: {line}.")
            
            elif line.count("<") and line.count(">"):
                message = line.split(">", 1)[1].strip()
                name = line.split("<")[1].split(">")[0]
                head = f"https://mc-heads.net/avatar/{name}"
                await webhook.send(
                    content=message,
                    username=name,
                    avatar_url=head,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            
        if console_lines:
            await console_channel.send("\n".join(console_lines))

        await asyncio.sleep(1)
