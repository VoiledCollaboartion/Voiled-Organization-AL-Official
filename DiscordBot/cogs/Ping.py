from discord import Interaction, app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ping.py is ready!")

    @app_commands.command(name="ping", description="Check bot's latency")
    # @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: Interaction):
        bot_latency = round(self.bot.latency * 1000)

        await interaction.response.send_message(f"Ping! {bot_latency} ms.")

    # @ping.error
    # async def ping_error(self, interaction: Interaction, error):
    #     await interaction.response.send_message("Not allowed!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ping(bot))
