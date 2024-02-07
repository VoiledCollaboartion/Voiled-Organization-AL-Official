import asyncio
import json
import os

import discord
import discord.ui
from discord import (
    Color,
    Embed,
    Interaction,
    TextChannel,
    app_commands,
)
from discord.ext import commands

# settings
JSON_FILE = "user_info.json"  # File to store user data
TOKEN = ""
PREFIX = "/"
# Input appropriate IDs and contents.
WELCOME_CHANNEL_ID = 1198917938183421982

VERIFICATION_CHANNEL_ID = 1198917980323598388
RULES_CHANNEL_ID = 0
CHAT_CHANNEL_ID = 1198917963206635601
VERIFIED_ROLE_NAME = "Verified"
UNVERIFIED_ROLE_NAME = "Unverified"
PREMIUM_ROLE_NAME = "Verified"


intents = discord.Intents.all()
intents.members = True  # Enable the member update event
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

verification_codes = {}  # Dictionary to store user codes

user_info = {}

# Load user data from JSON file on bot startup
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as file:
        user_info = json.load(file)


@bot.event
async def on_ready():
    print("Logged in as " + bot.user.name)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    bot.add_view(Verification())


@bot.tree.command(
    name="say_msg", description="Sends message to specified channel. (Admin only)"
)
@app_commands.describe(
    message="Input message.",
    channel="Which channel should I send the message to?",
)
async def say_msg(interaction: Interaction, channel: discord.TextChannel, message: str):
    """
    Send a message to a specified channel.

    Parameters:
    - channel: The channel where the message will be sent.
    - message: The message content to send.

    Usage: /say_msg <channel> <message>

    This command sends a message to the specified channel.
    Only users with appropriate permissions can use this command.
    """
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


@bot.tree.command(
    name="say_embed",
    description="Sends embedded message to specified channel. (Admin only)",
)
@app_commands.describe(
    header="Input header.",
    message="Input message.",
    channel="Which channel should I send the message to?",
    color_name="red, green, blue",
)
async def say_embed(
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


@bot.tree.command(
    name="say_dm",
    description="Sends a direct message or to specified member. (Admin only)",
)
@app_commands.describe(message="Input message.")
async def say_DM(interaction: Interaction, user: discord.Member, message: str):
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


@bot.command(help="Initialize the verification process")
@app_commands.describe(channel="Mention the channel to send the verification message.")
async def initialize(ctx, channel: discord.TextChannel = None):
    """
    Initialize the verification process.

    Usage: !initialize [channel]

    This command starts the verification process by sending an embed with a verification button.
    If no channel is specified, the message will be sent to the default verification channel.
    Only administrators can use this command.
    """
    if not ctx.author.guild_permissions.administrator:
        return

    if channel is None:
        return await ctx.send("Channel not found.")

    embed = discord.Embed(
        title="Verification", description="Click the button below to verify."
    )
    await channel.send(embed=embed, view=Verification())



@bot.event
async def on_member_join(member):
    # Assign unverified role to new member
    unverified_role = discord.utils.get(member.guild.roles, name=UNVERIFIED_ROLE_NAME)
    await member.add_roles(unverified_role)


class Verification(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify", style=discord.ButtonStyle.green, custom_id="verify"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        # Generate a verification code
        code = generate_verification_code()
        verification_codes[user.id] = code

        # Send a message with the verification code and delete it after a short delay
        await interaction.response.send_message(
            f"Your verification code is: {code}", ephemeral=True
        )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if the message author is undergoing verification
    if (
        isinstance(message.author, discord.Member)
        and message.author.id in verification_codes
    ):
        code = verification_codes[message.author.id]
        verification_channel_id = VERIFICATION_CHANNEL_ID

        verification_channel = bot.get_channel(verification_channel_id)

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
            welcome_channel = bot.get_channel(welcome_channel_id)
            welcome_message = f"Hey, {message.author.mention}! Welcome to {message.author.guild.name}."

            WELCOME_CHANNEL_MESSAGE = f"""
📜| Rules in <#{RULES_CHANNEL_ID}> \n
🗣️| Chat in ⁠<#{CHAT_CHANNEL_ID}> \n
                """

            # embed message
            embed = discord.Embed(title="Welcome!", description=WELCOME_CHANNEL_MESSAGE)
            await welcome_channel.send(welcome_message, embed=embed)

            # Clean up the verification code
            del verification_codes[message.author.id]
            await asyncio.sleep(5)  # Adjust the delay duration as needed (in seconds)
            await success_message.delete()

        else:
            # Delete the user's incorrect verification code message
            await message.delete()
            # Send a message indicating incorrect verification code

            failed_message = await verification_channel.send(
                "Incorrect verification code. Please try again."
            )
            await asyncio.sleep(5)  # Adjust the delay duration as needed (in seconds)
            await failed_message.delete()

    await bot.process_commands(message)


@bot.tree.command(name="ping", description="Ping the bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Ping!")


@bot.tree.command(name="portfolio_create", description="Portfolio")
@app_commands.describe(
    first_name="What's your first name?",
    last_name="What's your last name?",
    professional_skill="What's your main skill?",
    key_skills="What are your key skills? (Separate with commas.)",
    experience="What is your experience?",
    about_me="Write about yourself.",
    github="Input your GitHub link.",
    twitter="Input your Twitter link.",
    upwork="Input your UpWork link.",
)
async def portfolio_create(
    interaction: Interaction,
    first_name: str,
    last_name: str,
    professional_skill: str,
    key_skills: str,
    experience: str,
    about_me: str,
    github: str = None,
    twitter: str = None,
    upwork: str = None,
):
    # Split the string of key skills into a list
    key_skills_list = [skill.strip() for skill in key_skills.split(",")]

    # Check if the user has the required role
    required_role = discord.utils.get(interaction.guild.roles, name=PREMIUM_ROLE_NAME)
    if (
        required_role not in interaction.user.roles
        or not interaction.user.guild_permissions.administrator
    ):
        return await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )

    # Store user information
    user_id = str(interaction.user.id)
    user_data = user_info.get(user_id)
    if user_data:
        await interaction.response.send_message(
            "You already have a portfolio. Use /portfolio_edit to edit.", ephemeral=True
        )
        return

    profile_pic_url = interaction.user.avatar.url
    user_info[user_id] = {
        "first_name": first_name,
        "last_name": last_name,
        "user_name": interaction.user.name,
        "profile_pic_url": interaction.user.avatar.url,
        "professional_skill": professional_skill,
        "key_skills": key_skills_list,
        "experience": experience,
        "about_me": about_me,
        "github": github,
        "twitter": twitter,
        "upwork": upwork,
        # Add more information here later
    }

    # Write user data to JSON file
    with open(JSON_FILE, "w") as file:
        json.dump(user_info, file)

    await interaction.response.send_message(
        f"Portfolio saved! Use */portfolio_show* to show portfolio.", ephemeral=True
    )
@bot.tree.command(name="upload_project", description="Upload a project photo")
async def upload_project(interaction: Interaction):
    # Check if the user has the required role
    required_role = discord.utils.get(interaction.guild.roles, name=PREMIUM_ROLE_NAME)
    if (
        required_role not in interaction.user.roles
        or not interaction.user.guild_permissions.administrator
    ):
        return await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )

    await interaction.response.send_message("Upload your project.", ephemeral=True)


    try:
        # Wait for the user to upload a photo
        message = await bot.wait_for(
            "message", check=lambda m: m.author == interaction.user and m.attachments,
            timeout=60
        )

        # Assuming the user uploads only one photo, we'll take the first attachment
        attachment = message.attachments[0]
        photo_url = attachment.url

        # Update the user's information with the photo URL
        user_id = str(interaction.user.id)
        user_data = user_info.get(user_id)
        if user_data:
            user_data["project_photo_url"] = photo_url

            # Write updated user data to JSON file
            with open(JSON_FILE, "w") as file:
                json.dump(user_info, file)

            # Send a follow-up message to confirm successful upload
            await interaction.followup.send("Project photo uploaded successfully!", ephemeral=True)

        else:
            await interaction.followup.send(
                "User data not found. Please create a portfolio first.", ephemeral=True
            )

    except asyncio.TimeoutError:
        await interaction.followup.send(
            content="Upload process timed out. Please try again later."
        )
    except Exception as e:
        await interaction.followup.send(
            content=f"An error occurred: {e}"
        )


@bot.tree.command(name="portfolio_show", description="Portfolio")
@app_commands.describe(member="Optional: Mention the member whose portfolio you want to show.")
async def portfolio_show(
    interaction: Interaction,
    member: discord.Member = None,
):
    
    # If member parameter is not provided, default to the interaction user
    if member is None:
        member = interaction.user

    user_id = str(member.id)
    user_data = user_info.get(user_id)
    if not user_data:
        await interaction.response.send_message(
            f"{member.display_name} hasn't created a portfolio yet.", ephemeral=True
        )
        return

    first_name = user_data["first_name"]
    last_name = user_data["last_name"]
    profile_pic_url = user_data["profile_pic_url"]
    professional_skill = user_data["professional_skill"]
    key_skills_list = user_data["key_skills"]
    experience = user_data["experience"]
    about_me = user_data["about_me"]
    github = user_data["github"]
    twitter = user_data["twitter"]
    upwork = user_data["upwork"]
    project_photo_url = user_data.get("project_photo_url")

    embed = discord.Embed(title=professional_skill)
    embed.set_author(
        name=f"{first_name} {last_name}",
        icon_url=profile_pic_url,
        url=f"https://www.discordapp.com/users/{user_id}",
    )
    embed.add_field(name="Key Skills", value="\n".join(key_skills_list))
    embed.add_field(name="Experience", value=experience)
    embed.add_field(name="About me:", value=about_me, inline=False)

    if github:
        embed.add_field(name="", value=f"[GitHub]({github})", inline=True)
    if twitter:
        embed.add_field(name="", value=f"[Twitter]({twitter})", inline=False)
    if upwork:
        embed.add_field(name="", value=f"[UpWork]({upwork})", inline=False)




    if project_photo_url:
        embed.set_image(url=project_photo_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="portfolio_edit", description="Edit Portfolio")
@app_commands.describe(
    first_name="Edit your first name.",
    last_name="Edit your last name.",
    professional_skill="Edit your main skill.",
    bio="Edit your bio.",
    key_skills="Edit your key skills. (Separate with commas.)",
    experience="Edit your experience.",
    github="Edit your GitHub link.",
    twitter="Edit your Twitter link.",
    upwork="Edit your UpWork link.",

)
async def portfolio_edit(
    interaction: Interaction,
    first_name: str = None,
    last_name: str = None,
    professional_skill: str = None,
    bio: str = None,
    key_skills: str = None,
    experience: str = None,
    github: str = None,
    twitter: str = None,
    upwork: str = None,

):
    # Check if the user has the required role
    required_role = discord.utils.get(interaction.guild.roles, name=PREMIUM_ROLE_NAME)
    if (
        required_role not in interaction.user.roles
        or not interaction.user.guild_permissions.administrator
    ):
        return await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )

    user_id = str(interaction.user.id)
    user_data = user_info.get(user_id)
    if not user_data:
        await interaction.response.send_message(
            "You haven't created a portfolio yet. Use */portfolio_create* to create one.",
            ephemeral=True,
        )
        return

    # Update user data with edited information
    if first_name is not None:
        user_data["first_name"] = first_name
    if last_name is not None:
        user_data["last_name"] = last_name
    if professional_skill is not None:
        user_data["professional_skill"] = professional_skill
    if bio is not None:
        user_data["bio"] = bio
    if key_skills is not None:
        user_data["key_skills"] = [skill.strip() for skill in key_skills.split(",")]
    if experience is not None:
        user_data["experience"] = experience
    if github is not None:
        user_data["github"] = github
    if twitter is not None:
        user_data["twitter"] = twitter
    if upwork is not None:
        user_data["upwork"] = upwork

    # Update user info dictionary
    user_info[user_id] = user_data

    # Write updated user data to JSON file
    with open(JSON_FILE, "w") as file:
        json.dump(user_info, file)

    await interaction.response.send_message(
        "Portfolio updated successfully!", ephemeral=True
    )

@bot.tree.command(name="portfolio_delete", description="Delete Portfolio")
async def portfolio_delete(interaction: Interaction):
    # Check if the user has the required role
    required_role = discord.utils.get(interaction.guild.roles, name=PREMIUM_ROLE_NAME)
    if (
        required_role not in interaction.user.roles
        or not interaction.user.guild_permissions.administrator
    ):
        return await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )

    user_id = str(interaction.user.id)
    if user_id not in user_info:
        await interaction.response.send_message(
            "You haven't created a portfolio yet.", ephemeral=True
        )
        return

    del user_info[user_id]

    # Write updated user data to JSON file
    with open(JSON_FILE, "w") as file:
        json.dump(user_info, file)

    await interaction.response.send_message(
        "Portfolio deleted successfully!", ephemeral=True
    )

def generate_verification_code():
    # You can customize the code generation logic here
    # For simplicity, let's generate a random 4-digit code
    import random

    return str(random.randint(1000, 9999))


bot.run(TOKEN)
