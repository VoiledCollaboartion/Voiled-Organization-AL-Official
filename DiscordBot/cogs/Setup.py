import sqlite3

import discord.ui
from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

sdb_path = "databases/settings.db"


class ConfirmView(discord.ui.View):

    def __init__(self, server_id, welcome_channel=None, verified_role=None):
        super().__init__(timeout=None)
        self.server_id = server_id
        self.welcome_channel = welcome_channel
        self.verified_role = verified_role
        self.conn = sqlite3.connect(sdb_path)
        self.cursor = self.conn.cursor()

    @discord.ui.button(
        label="Confirm", style=discord.ButtonStyle.blurple, custom_id="confirm-cv"
    )
    async def button1_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            # Create settings table
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS server_settings (
                        server_id INTEGER PRIMARY KEY,
                        verified_role_id INTEGER,
                        welcome_channel_id INTEGER
            )


            """
            )
            self.conn.commit()

            query = """SELECT * FROM server_settings WHERE server_id = ?"""
            self.cursor.execute(query, (self.server_id,))
            info = self.cursor.fetchone()

            if info is None:
                if self.welcome_channel is not None:
                    self.cursor.execute(
                        """INSERT INTO server_settings 
                        (server_id, welcome_channel_id)
                        VALUES (?, ?)""",
                        (self.server_id, self.welcome_channel.id),
                    )
                    self.conn.commit()
                if self.verified_role is not None:
                    self.cursor.execute(
                        """INSERT INTO server_settings 
                        (server_id, verified_role_id)
                        VALUES (?, ?)""",
                        (self.server_id, self.verified_role.id),
                    )
                    self.conn.commit()

            else:
                if self.welcome_channel is not None:
                    self.cursor.execute(
                        """UPDATE server_settings SET welcome_channel_id=? WHERE server_id=?""",
                        (self.welcome_channel.id, self.server_id),
                    )
                    self.conn.commit()
                if self.verified_role is not None:
                    self.cursor.execute(
                        """UPDATE server_settings SET verified_role_id=? WHERE server_id=?""",
                        (self.verified_role.id, self.server_id),
                    )
                    self.conn.commit()

            if self.welcome_channel is not None:
                await interaction.response.edit_message(
                    embed=None,
                    content=f"Welcome channel set to {self.welcome_channel.mention}",
                    view=None,
                )
            if self.verified_role is not None:
                await interaction.response.edit_message(
                    embed=None,
                    content=f"Verified role set to {self.verified_role.mention}",
                    view=None,
                )

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )

    @discord.ui.button(
        label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel-cv"
    )
    async def button2_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            if self.welcome_channel is not None:
                embed = Embed(
                    title="Bot Setup",
                    description="Please select the welcome channel in your server",
                    color=Color.blue(),
                )
                return await interaction.response.edit_message(
                    embed=embed, view=ChannelView()
                )

            if self.verified_role is not None:
                embed = Embed(
                    title="Bot Setup",
                    description="Please select the role for verified members in your server",
                    color=Color.blue(),
                )
                await interaction.response.edit_message(embed=embed, view=RoleView())

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )


class ChannelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Select the welcome channel",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
    )
    async def select_channel(
        self, interaction: Interaction, select: discord.ui.ChannelSelect
    ):
        try:
            welcome_channel = select.values[0]
            server_id = interaction.guild_id
            embed = Embed(
                title="Confirmation",
                description=f"Confirm to use {select.values[0].mention} as the welcome channel ",
                color=Color.blue(),
            )
            return await interaction.response.edit_message(
                embed=embed,
                view=ConfirmView(
                    server_id=server_id,
                    welcome_channel=welcome_channel,
                    verified_role=None,
                ),
            )
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")


class RoleView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
    

    @discord.ui.select(
        placeholder="Select the role for verified members",
        cls=discord.ui.RoleSelect,
    )
    async def select_role(
        self, interaction: Interaction, select: discord.ui.RoleSelect
    ):
        try:
            verified_role = select.values[0]
            server_id = interaction.guild_id
            embed = Embed(
                title="Confirmation",
                description=f"Confirm to use {select.values[0].mention} as the role for verified members",
                color=Color.blue(),
            )
            
            return await interaction.response.edit_message(
                embed=embed,
                view=ConfirmView(
                    server_id=server_id,
                    welcome_channel=None,
                    verified_role=verified_role,
                ),
            )
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")


class Setup(commands.GroupCog, group_name="setup"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Setup.py is ready!")
        self.bot.add_view(ChannelView())

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            embed = Embed(
                title="Hey there!",
                description=f"Thanks for inviting me to {guild.name}! Please use /setup commands in your admin channel to configure me.",
            )
            await guild.owner.send(embed=embed)

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")

    @app_commands.command(name="welcome_channel", description="Configure me")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: Interaction):
        try:
            embed = Embed(
                title="Bot Setup",
                description="Please select the welcome channel in your server",
                color=Color.blue(),
            )
            await interaction.response.send_message(
                embed=embed, view=ChannelView(), ephemeral=True
            )
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")

    @welcome_channel.error
    async def welcome_channel_error(self, interaction: Interaction, error):
        await interaction.response.send_message(
            "Only admins can use this command!", ephemeral=True
        )

    @app_commands.command(name="verified_role", description="Configure me")
    @app_commands.checks.has_permissions(administrator=True)
    async def verified_role(self, interaction: Interaction):
        try:
            embed = Embed(
                title="Bot Setup",
                description="Please select the role for verified members in your server",
                color=Color.blue(),
            )
            await interaction.response.send_message(
                embed=embed, view=RoleView(), ephemeral=True
            )
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")

    @verified_role.error
    async def verified_role_error(self, interaction: Interaction, error):
        await interaction.response.send_message(
            "Only admins can use this command!", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Setup(bot))
