import asyncio
import sqlite3
from datetime import datetime

import discord.ui
from discord import Color, Embed, Interaction, Message, TextChannel
from discord.ext import commands

sdb_path = "databases/settings.db"

verification_codes = {}


class VerifyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.conn = sqlite3.connect(sdb_path)
        self.cursor = self.conn.cursor()

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.green, custom_id="verify"
    )
    async def verify(self, interaction: Interaction, button: discord.ui.Button):
        try:

            user = interaction.user
            server = user.guild

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
            self.cursor.execute(query, (server.id,))
            self.conn.commit()

            server_info = self.cursor.fetchone()
            print(server_info)

            if server_info is None:
                await server.owner.send(
                    f"Please set the role for verified members in {server.name}!"
                )
                return await interaction.response.send_message(
                    "Oops! An error occurred verifying you... Please try again later."
                )

            (_, VERIFIED_ROLE_ID, WELCOME_CHANNEL_ID) = server_info
            # Generate a verification code
            code = generate_verification_code()
            verification_codes[user.id] = code
            embed = Embed(
                title=f"Verification for {server.name}",
                description=f"Reply with the following code: ||{code}||",
                color=Color.green(),
            )
            await interaction.channel.send(embed=embed, delete_after=60)

            def check(m: Message):
                try:
                    return m.author.id == interaction.user.id
                except Exception as e:
                    # Handle the exception
                    print(f"Error occurred: {e}")

            try:
                # Check if correct code was sent
                msg = await self.bot.wait_for("message", check=check, timeout=60)

                # Check if the message content matches the verification code
                if msg.content == code:
                    # Assign the verified role
                    v_role = discord.utils.get(server.roles, id=VERIFIED_ROLE_ID)
                    await user.add_roles(v_role)

                    # Send a msg indicating successful verification and delete it after a short delay

                    await user.send(
                        f"{user.mention}, you have been verified! You now have access to {server.name}.",
                    )
                    await asyncio.sleep(5)
                    await interaction.channel.delete()

                    if welcome_channel:

                        # main message
                        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
                        # welcome_message = f"Hey, {user.mention}!"

                        current_date = datetime.now().replace(microsecond=0)

                        # embed message
                        embed = discord.Embed(
                            title=f"{user.mention} just joined!",
                            color=Color.dark_grey(),
                        )
                        account_age = int(user.created_at.timestamp())
                        value = f"Display Name: {user.display_name}\
                            \nUsername: {user.name}\
                            \nDiscord Member Since: <t:{account_age}:D>"
                        embed.add_field(name=f"About {user.display_name}", value=value)
                        embed.timestamp = current_date
                        if user.avatar:
                            embed.set_thumbnail(url=user.avatar.url)
                        embed.set_footer(text="\u200b")
                        await welcome_channel.send(embed=embed)

                    # Clean up the verification code
                    del verification_codes[user.id]

                else:
                    # Send a message indicating incorrect verification code

                    await user.send(
                        "Incorrect verification code. Please try again.", delete_after=5
                    )

            except asyncio.TimeoutError:
                await user.send(
                    f"Verification process timed out. Please go back to {server.name} and try again.",
                    delete_after=10,
                )

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")


def generate_verification_code():
    # You can customize the code generation logic here
    # For simplicity, let's generate a random 4-digit code
    import random

    return str(random.randint(1000, 9999))


class Verification(commands.Cog):

    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            print("Verification.py is ready!")
            self.bot.add_view(VerifyView(self.bot))
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            guild = member.guild

            # create a verification channel
            category = discord.utils.get(guild.categories, name="VERIFICATION")
            if category is None:
                category = await guild.create_category("VERIFICATION")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
            }
            channel = await category.create_text_channel(
                f"{member.name}", overwrites=overwrites
            )

            embed = Embed(
                title="Verification",
                description="To gain access to the server, click the button below to verify.",
                color=Color.green(),
            )
            await channel.send(embed=embed, view=VerifyView(self.bot))
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))
