import discord
import json
import os
import dotenv
from .rcon_client import RconClient


dotenv.load_dotenv(override=True)
token = os.getenv("DISCORD_TOKEN")
events_channel_id = int(os.getenv("EVENTS_CHANNEL_ID")) #Discord client expects channel ID's as integers
console_channel_id = int(os.getenv("CONSOLE_CHANNEL_ID"))

host = os.getenv("RCON_HOST")
port = int(os.getenv("RCON_PORT")) # RCON client expects port as integer
password = os.getenv("RCON_PASSWORD")
rcon = RconClient(host, port, password)

bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot_intents.members = True
bot_intents.presences = True

client = discord.Client(intents=bot_intents)


@client.event
async def on_ready():
    try:
        if await rcon.connect():
            print("Connected to RCON client.")
        else:
            print("RCON authentication failed - check password.")
    except Exception as e:
        print(f"Failed to connect to RCON Client: {e}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == console_channel_id:
        try:
            response = await rcon.send_command(message.content.lstrip("/"))
        except Exception as e:
            await message.channel.send(f"Failed to send RCON command: {e}")
            return
        
        try:
            await message.channel.send(response)
        except Exception as e:
            print(f"Failed to send message to Discord: {e}")

    if message.channel.id == events_channel_id:

        # Format discord message for Minecraft in-game chat
        tellraw_payload = json.dumps([
            {"text": "[Discord] ", "color": "blue"},
            {"text": f"{message.author.display_name}"},
            {"text": f": {message.content}"}
        ])
        
        try:
            await rcon.send_command(f"tellraw @a {tellraw_payload}")
        except Exception as e:
            await message.channel.send(f"Failed to send message to game: {e}")


if __name__ == "__main__":
    client.run(token)