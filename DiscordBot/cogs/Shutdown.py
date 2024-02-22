from discord.ext import commands

import asyncio
import discord.ui
from discord import (
    app_commands,
    Embed,
    Interaction,
)
import sys

sys.path.append("setup")
from setup import owner_id

# Define your command to shut down the bot


class Shutdown(commands.Cog):

    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @commands.command()
    async def shutdown(self, ctx):
        # Check if the user who sent the command is authorized
        # Replace this condition with your own authorization logic
        if ctx.author.id == owner_id:
            await ctx.send("Shutting down...")
            await self.bot.close()


async def setup(bot):
    await bot.add_cog(Shutdown(bot))
