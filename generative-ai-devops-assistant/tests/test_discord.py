import os
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("=" * 50)
    print("DISCORD TEST SUCCESS")
    print(f"Bot: {client.user}")
    print(f"Bot ID: {client.user.id}")
    print(f"Guilds: {len(client.guilds)}")
    for guild in client.guilds:
        print(f"  - {guild.name} ({guild.id})")
    print("=" * 50)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    print(f"Message received: {message.author}: {message.content}")


client.run(TOKEN)