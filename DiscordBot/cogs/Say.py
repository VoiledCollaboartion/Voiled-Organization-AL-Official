import discord
from discord import Color, Embed, Interaction, Member, TextChannel, app_commands
from discord.ext import commands


@app_commands.guild_only()
class Say(commands.GroupCog, group_name="say"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Say.py is ready!")

    @app_commands.command(
        name="message", description="Sends message to specified channel. (Admin only)"
    )
    @app_commands.describe(
        channel="What channel should I send this message to?",
        message="Input message content.",
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

    @app_commands.command(
        name="embed",
        description="Sends embedded message to specified channel. (Admin only)",
    )
    @app_commands.choices(
        color=[
            app_commands.Choice(name="🟥 Red", value="red"),
            app_commands.Choice(name="🟩 Green", value="green"),
            app_commands.Choice(name="🟦 Blue", value="blue"),
            app_commands.Choice(name="🟨 Yellow", value="yellow"),
        ]
    )
    @app_commands.describe(
        channel="What channel should I send this embedded message to?",
        header="Input header content.",
        message="Input message content.",
        color="Select colour. (Default: Green)",
    )
    async def embed(
        self,
        interaction: Interaction,
        channel: TextChannel,
        message: str,
        header: str = None,
        color: str = "green",
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
            "yellow": Color.yellow(),
            # Add more colors as needed
        }

        # Get the Color object based on the color name
        color_ = color_mapping[color]

        # Create an Embed object with the specified color and header
        embed = Embed(description=message, color=color_)
        if header:
            embed.title = header

        # Send the embedded message to the channel
        msg = await channel.send(embed=embed)

        # Send response to the user
        await interaction.response.send_message(
            f"Message sent to {channel.mention} successfully! Link: {msg.jump_url}",
            ephemeral=True,
        )

    @app_commands.command(
        name="dm",
        description="Sends a direct message to specified member. (Admin only)",
    )
    @app_commands.describe(
        member="Which member should I send direct message to?",
        message="Input message content.",
        title="input title.",
    )
    async def DM(
        self, interaction: Interaction, member: Member, message: str, title: str = None
    ):
        try:
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )

            # Send the embed message to the user via direct message
            embed = Embed(
                title=f"Message from {interaction.user.guild.name}",
                color=Color.dark_grey(),
            )
            if title:
                embed.add_field(name=title, value=message)

            elif title is None:
                embed.add_field(name="", value=message)
            embed.set_thumbnail(url=interaction.user.guild.icon)
            await member.send(embed=embed)

            # Send response to the user indicating that the message was sent
            await interaction.response.send_message(
                f"Message sent to {member.mention} successfully!", ephemeral=True
            )
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Say(bot))
