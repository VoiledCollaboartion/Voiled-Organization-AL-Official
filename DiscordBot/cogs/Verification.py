import asyncio
import sqlite3
import random
import string
import os
import discord.ui
import logging

from datetime import datetime
from captcha.image import ImageCaptcha
from discord import Color, Embed, Interaction, Message
from discord.ui import Select, View
from discord.ext import commands

sdb_path = "databases/settings.db"
VERIFIED_ROLE_ID = 0
WELCOME_CHANNEL_ID = 0
class MyDropdown(Select):
    def __init__(self, captcha_text, server_info):
        self.captcha_text = captcha_text
        self.server_info = server_info
        # Define the options that will appear in the dropdown
        options = [
            discord.SelectOption(label=captcha_text),
            discord.SelectOption(label=''.join(random.choices(string.ascii_uppercase + string.digits, k=6))),
            discord.SelectOption(label=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
        ]
        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        server = user.guild
        # When the user selects an option, this callback is triggered
        selected_option = self.values[0]
        await interaction.response.send_message(f"You selected: {selected_option}")
        
        try:
            # Check if the message content matches the verification code
            if selected_option == self.captcha_text:
                (_, VERIFIED_ROLE_ID, WELCOME_CHANNEL_ID) = self.server_info
                # Assign the verified role
                v_role = discord.utils.get(server.roles, id=VERIFIED_ROLE_ID)
                if v_role:
                    await user.add_roles(v_role)


                # Send a msg indicating successful verification and delete it after a short delay

                await user.send(
                    f"{user.mention}, you have been verified! You now have access to {server.name}.",
                )
                
                # await asyncio.sleep(1)
                await interaction.channel.delete()

                if welcome_channel:

                    # main message
                    welcome_channel = server.get_channel(WELCOME_CHANNEL_ID)
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

class VerifyView(discord.ui.View):
    def __init__(self, bot, message_id=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.conn = sqlite3.connect(sdb_path)
        self.cursor = self.conn.cursor()
        self.message_id = message_id  # Store the message ID

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
                    )"""
                )
            self.conn.commit()
            
            query = """SELECT * FROM server_settings WHERE server_id = ?"""
            self.cursor.execute(query, (server.id,))
            self.conn.commit()
            
            server_info = self.cursor.fetchone()
            if server_info is None:
                await server.owner.send(
                    f"Please set the role for verified members in {server.name}!"
                )
                return await interaction.response.send_message(
                    "Oops! An error occurred verifying you... Please try again later."
                )

            
            captcha_text, image_file = generate_captcha()
            print(captcha_text)
            
                
            channel = interaction.channel
            if self.message_id:
                # Fetch the old message
                message = await channel.fetch_message(self.message_id)
                await message.delete()  # Delete the old message

            # Send the new message with updated content
            embed = Embed(
                title="Verification",
                description="Complete CAPTCHA",
                color=Color.blue(),
            )
            embed.set_image(url=f"attachment://{image_file}")
            self.clear_items()

            with open(image_file, "rb") as file:
                self.add_item(MyDropdown(captcha_text, server_info))
                new_message = await channel.send(
                    embed=embed,
                    file=discord.File(file, image_file),
                    view=self
                )
                self.message_id = new_message.id  # Update message ID in view
            
            
            os.remove(image_file)

        except Exception as e:
            # Handle the exception
            print(f"verify Error occurred: {e}")

# Function to generate a CAPTCHA
def generate_captcha():
    # Create a list of random letters
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Generate CAPTCHA image
    image_captcha = ImageCaptcha(width=280, height=90)
    image = image_captcha.generate_image(captcha_text)
    image_file = f"captcha_{captcha_text}.png"
    image.save(image_file)
    return captcha_text, image_file

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
            print(f"on_ready Error occurred: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            guild = member.guild

            # create a verification channel
            category = discord.utils.get(guild.categories, name="VERIFICATION")
            if category is None:
                category = await guild.create_category("VERIFICATION")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
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
            
            # Create a VerifyView instance without the message_id
            view = VerifyView(self.bot)
            message = await channel.send(embed=embed, view=view)
            # Update VerifyView with the message_id
            view.message_id = message.id
            
        except Exception as e:
            # Handle the exception
            print(f"on_member_join Error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))
