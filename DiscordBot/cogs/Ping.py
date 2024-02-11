from discord.ext import commands

from discord import (
    app_commands,
    Interaction,
)


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ping.py is ready!")

    @app_commands.command(name="ping", description="Ping the bot")
    async def ping(self, interaction: Interaction):
        bot_latency = round(self.bot.latency * 1000)

        await interaction.response.send_message(f"Ping! {bot_latency} ms.")


async def setup(bot):
    await bot.add_cog(Ping(bot))
