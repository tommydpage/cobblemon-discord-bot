import discord
import json
import os
import dotenv
import asyncio
from .rcon_client import RconClient
from .log_parser import read_log


dotenv.load_dotenv(override=True)
token = os.getenv("DISCORD_TOKEN")
events_channel_id = int(os.getenv("EVENTS_CHANNEL_ID"))
console_channel_id = int(os.getenv("CONSOLE_CHANNEL_ID"))

host = os.getenv("RCON_HOST")
port = int(os.getenv("RCON_PORT"))
password = os.getenv("RCON_PASSWORD")
rcon = RconClient(host, port, password)

bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot_intents.members = True
bot_intents.presences = True

client = discord.Client(intents=bot_intents)

log_reader = False
player_counter = False

# Player list is received in the format "There are X of a max of Y players online: [players]"
def parse_list(response):
    players_online, players_max = int(response.split()[2]), int(response.split()[7])
    return players_online, players_max

async def update_player_count():
    while True: 
        try:
            players_online, players_max = parse_list(await rcon.send_command("list"))
        except Exception as e:
            print(f"RCON connection no longer active: {e}")
            await connect_rcon()
            await asyncio.sleep(30)
            continue
        
        try:
            await client.change_presence(activity=discord.Game(f"{players_online}/{players_max} Players on the server."))
        except Exception as e:
            print(f"Unable to update Bot Status: {e}")

        await asyncio.sleep(10)

async def connect_rcon():
    while True:
        try:
            if await rcon.connect():
                print("Connected to RCON client.")
                status = True
                break
            else:
                print("RCON authentication failed - check password.")
                status = False
                break
        except Exception as e:
            print(f"Waiting for RCON Client: {e}")
            await asyncio.sleep(10)
    return status

async def setup_hook():
    asyncio.create_task(read_log(client))
    asyncio.create_task(update_player_count())
client.setup_hook = setup_hook

@client.event
async def on_ready():
    while True:
        if await connect_rcon():
            break
        else:
            await asyncio.sleep(10)

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == console_channel_id:
        try:
            response = await rcon.send_command(message.content.lstrip("/"))
        except Exception as e:
            await message.channel.send("Failed to send RCON command, restoring connection...")
            if await connect_rcon():
                await message.channel.send("RCON connection restored. Try your command again.")
            else:
                await message.channel.send("RCON Connection failed: check password.")
            return
        
        try:
            await message.channel.send(response)
        except Exception as e:
            print(f"Failed to send message to Discord: {e}")

    elif message.channel.id == events_channel_id:
        # Format discord message for Minecraft in-game chat
        tellraw_payload = json.dumps([
            {"text": "[Discord] ", "color": "blue"},
            {"text": f"{message.author.display_name}"},
            {"text": f": {message.content}"}
        ])
        
        try:
            await rcon.send_command(f"tellraw @a {tellraw_payload}")
        except Exception as e:
            await message.channel.send("Message failed. Restoring connection to game chat...")
            if await connect_rcon():
                await message.channel.send("Game chat connection restored. Try your message again.")
            else:
                await message.channel.send("Game chat connection failed. Tell an admin!")
            return


if __name__ == "__main__":
    client.run(token)