import discord
from discord.ext import commands

from discord import (
    Color,
    Embed,
    Interaction,
    TextChannel,
    app_commands,
)


class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Say.py is ready!")

    say = app_commands.Group(name="say", description="Say")

    @say.command(
        name="message", description="Sends message to specified channel. (Admin only)"
    )
    async def message(
        self, interaction: Interaction, channel: discord.TextChannel, message: str
    ):
        # Check if the user has the required permissions to execute this command
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )

        # Send the message to the specified channel
        msg = await channel.send(message)

        # Send response to the user indicating that the message was sent
        await interaction.response.send_message(
            f"Message sent to {channel.mention} successfully! Link: {msg.jump_url}",
            ephemeral=True,
        )

    @say.command(
        name="embed",
        description="Sends embedded message to specified channel. (Admin only)",
    )
    async def embed(
        self,
        interaction: Interaction,
        header: str,
        message: str,
        channel: TextChannel,
        color_name: str = "green",
    ):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )

        # Define a mapping of color names to Color objects
        color_mapping = {
            "red": Color.red(),
            "green": Color.green(),
            "blue": Color.blue(),
            # Add more colors as needed
        }

        # Convert the color name to lowercase for case-insensitive matching
        color_name = color_name.lower()

        # Check if the specified color name is valid
        if color_name not in color_mapping:
            return await interaction.response.send_message(
                "Invalid color name. Please choose from: red, green, blue, etc.",
                ephemeral=True,
            )

        # Get the Color object based on the color name
        color = color_mapping[color_name]

        # Create an Embed object with the specified color and header
        embed = Embed(description=message, color=color)
        if header:
            embed.title = header

        # Send the embedded message to the channel
        msg = await channel.send(embed=embed)

        # Send response to the user
        await interaction.response.send_message(
            f"Message sent to {channel.mention} successfully! Link: {msg.jump_url}",
            ephemeral=True,
        )

    @say.command(
        name="dm",
        description="Sends a direct message or to specified member. (Admin only)",
    )
    async def DM(self, interaction: Interaction, user: discord.Member, message: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )

        # Send the message to the user via direct message
        await user.send(message)

        # Send response to the user indicating that the message was sent
        await interaction.response.send_message(
            f"Message sent to {user.display_name} successfully!", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Say(bot))
