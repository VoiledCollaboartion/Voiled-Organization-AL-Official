import discord
from discord.ext import commands
import os
import json
import asyncio

from discord import (
    Embed,
    Interaction,
    app_commands,
)

import sys

sys.path.append("setup")
from setup import JSON_FILE, PREMIUM_ROLE_NAME

user_info = {}


# Load user data from JSON file on bot startup
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as file:
        user_info = json.load(file)


class Portfolio(commands.Cog):
    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Portfolio.py is ready!")

    portfolio = app_commands.Group(name="portfolio", description="Portfolio")

    @portfolio.command(name="create", description="Portfolio")
    async def create(
        self,
        interaction: Interaction,
        full_name: str,
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
        required_role = discord.utils.get(
            interaction.guild.roles, name=PREMIUM_ROLE_NAME
        )
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
                "You already have a portfolio. Use /portfolio_edit to edit.",
                ephemeral=True,
            )
            return

        profile_pic_url = interaction.user.avatar.url
        user_info[user_id] = {
            "full_name": full_name,
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

    @portfolio.command(name="upload_project", description="Upload a project photo")
    async def upload_project(self, interaction: Interaction):
        # Check if the user has the required role
        required_role = discord.utils.get(
            interaction.guild.roles, name=PREMIUM_ROLE_NAME
        )
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
            message = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == interaction.user and m.attachments,
                timeout=60,
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
                await interaction.followup.send(
                    "Project photo uploaded successfully!", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    "User data not found. Please create a portfolio first.",
                    ephemeral=True,
                )

        except asyncio.TimeoutError:
            await interaction.followup.send(
                content="Upload process timed out. Please try again later."
            )
        except Exception as e:
            await interaction.followup.send(content=f"An error occurred: {e}")

    @portfolio.command(name="show", description="Portfolio")
    async def show(
        self,
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

        full_name = user_data["full_name"]
        profile_pic_url = user_data["profile_pic_url"]
        professional_skill = user_data["professional_skill"]
        key_skills_list = user_data["key_skills"]
        experience = user_data["experience"]
        about_me = user_data["about_me"]
        github = user_data["github"]
        twitter = user_data["twitter"]
        upwork = user_data["upwork"]
        project_photo_url = user_data.get("project_photo_url")

        embed = Embed(title=professional_skill)
        embed.set_author(
            name=full_name,
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

    @portfolio.command(name="edit", description="Edit Portfolio")
    async def edit(
        self,
        interaction: Interaction,
        full_name: str = None,
        professional_skill: str = None,
        bio: str = None,
        key_skills: str = None,
        experience: str = None,
        github: str = None,
        twitter: str = None,
        upwork: str = None,
    ):
        # Check if the user has the required role
        required_role = discord.utils.get(
            interaction.guild.roles, name=PREMIUM_ROLE_NAME
        )
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
        if full_name is not None:
            user_data["full_name"] = full_name
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

    @portfolio.command(name="delete", description="Delete Portfolio")
    async def delete(self, interaction: Interaction):
        # Check if the user has the required role
        required_role = discord.utils.get(
            interaction.guild.roles, name=PREMIUM_ROLE_NAME
        )
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


async def setup(bot):
    await bot.add_cog(Portfolio(bot))
