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
from setup import (
    WELCOME_CHANNEL_ID,
    VERIFICATION_CHANNEL_ID,
    RULES_CHANNEL_ID,
    CHAT_CHANNEL_ID,
    VERIFIED_ROLE_NAME,
    UNVERIFIED_ROLE_NAME,
)

verification_codes = {}


class Verification(commands.Cog):

    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Verification.py is ready!")
        self.bot.add_view(VerifyView())

    @commands.command()
    async def initialize(self, ctx, channel: discord.TextChannel = None):
        """
        Initialize the verification process.

        Usage: !initialize [channel]

        This command starts the verification process by sending an embed with a verification button.
        Only administrators can use this command.
        """

        if not ctx.author.guild_permissions.administrator:
            return

        if channel is None:
            txt = await ctx.send("Please specify a channel.")
            await asyncio.sleep(5)  # Adjust the delay duration as needed (in seconds)
            await txt.delete()

        embed = Embed(
            title="Verification", description="Click the button below to verify."
        )
        await channel.send(embed=embed, view=VerifyView())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Assign unverified role to new member
        unverified_role = discord.utils.get(
            member.guild.roles, name=UNVERIFIED_ROLE_NAME
        )
        await member.add_roles(unverified_role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the message author is undergoing verification
        if (
            isinstance(message.author, discord.Member)
            and message.author.id in verification_codes
        ):
            code = verification_codes[message.author.id]
            verification_channel_id = VERIFICATION_CHANNEL_ID

            verification_channel = self.bot.get_channel(verification_channel_id)

            # Check if the message content matches the verification code
            if message.content == code:
                await message.delete()  # Delete the user's message
                # Assign the verified role
                v_role = discord.utils.get(
                    message.author.guild.roles, name=VERIFIED_ROLE_NAME
                )
                await message.author.add_roles(v_role)

                # Send a message indicating successful verification and delete it after a short delay

                success_message = await verification_channel.send(
                    f"{message.author.mention}, you have been verified! Head to <#{WELCOME_CHANNEL_ID}> for more."
                )

                # Remove the unverified role
                u_role = discord.utils.get(
                    message.author.guild.roles, name=UNVERIFIED_ROLE_NAME
                )
                await message.author.remove_roles(u_role)

                # main message
                welcome_channel_id = WELCOME_CHANNEL_ID
                welcome_channel = self.bot.get_channel(welcome_channel_id)
                welcome_message = f"Hey, {message.author.mention}! Welcome to {message.author.guild.name}."

                WELCOME_CHANNEL_MESSAGE = f"""
    📜| Rules in <#{RULES_CHANNEL_ID}> \n
    🗣️| Chat in ⁠<#{CHAT_CHANNEL_ID}> \n
                    """

                # embed message
                embed = discord.Embed(
                    title="Welcome!", description=WELCOME_CHANNEL_MESSAGE
                )
                await welcome_channel.send(welcome_message, embed=embed)

                # Clean up the verification code
                del verification_codes[message.author.id]
                await asyncio.sleep(
                    5
                )  # Adjust the delay duration as needed (in seconds)
                await success_message.delete()

            else:
                # Delete the user's incorrect verification code message
                await message.delete()
                # Send a message indicating incorrect verification code

                failed_message = await verification_channel.send(
                    "Incorrect verification code. Please try again."
                )
                await asyncio.sleep(
                    5
                )  # Adjust the delay duration as needed (in seconds)
                await failed_message.delete()

        # await self.bot.process_commands(message)


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.green, custom_id="verify"
    )
    async def verify(self, interaction: Interaction, button: discord.ui.Button):
        user = interaction.user

        # Generate a verification code
        code = generate_verification_code()
        verification_codes[user.id] = code

        # Send a message with the verification code and delete it after a short delay
        await interaction.response.send_message(
            f"Your verification code is: {code}", ephemeral=True
        )


def generate_verification_code():
    # You can customize the code generation logic here
    # For simplicity, let's generate a random 4-digit code
    import random

    return str(random.randint(1000, 9999))


async def setup(bot):
    await bot.add_cog(Verification(bot))
