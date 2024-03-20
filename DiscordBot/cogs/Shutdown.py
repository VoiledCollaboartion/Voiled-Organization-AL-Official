import asyncio
import sys

from discord.ext import commands

sys.path.append("setup")
from setup import owner_id

# Define your command to shut down the bot


class Shutdown(commands.Cog):

    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @commands.command(hidden=True)
    async def shutdown(self, ctx):
        """
        [Emergency] Shut down the bot.

        Usage: /shutdown

        This command shuts down the bot.
        Only the bot owner can use this command.
        """
        # Check if the user who sent the command is authorized
        # Replace this condition with your own authorization logic
        if ctx.author.id == owner_id:
            msg = await ctx.send("Shutting down...")
            await asyncio.sleep(5)
            await self.bot.close()


async def setup(bot):
    await bot.add_cog(Shutdown(bot))
