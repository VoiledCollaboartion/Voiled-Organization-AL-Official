import discord
from discord.ext import commands
import os
import asyncio


from setup import *

intents = discord.Intents.all()
intents.members = True  # Enable the member update event
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    print("Successfully logged in as " + bot.user.name)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)


asyncio.run(main())


# coded by doyletony
