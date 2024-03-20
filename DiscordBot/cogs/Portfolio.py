import asyncio
import sqlite3
import sys

import discord
from discord import Attachment, Embed, Interaction, app_commands
from discord.ext import commands

sys.path.append("setup")
from setup import PREMIUM_ROLE_NAME, guild_id

pdb_path = "databases/portfolios.db"


class Portfolio(commands.Cog):
    def __init__(
        self,
        bot,
    ):
        self.bot = bot
        self.conn = sqlite3.connect(pdb_path)
        self.cursor = self.conn.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Portfolio.py is ready!")

    portfolio = app_commands.Group(name="portfolio", description="Portfolio")

    @portfolio.command(name="create", description="Create a portfolio.")
    @app_commands.describe(
        full_name="Input your full name.",
        professional_skill="What's your professional skill?",
        key_skills="What are your key skills? (Separate each skill with a comma.)",
        experience="How many years of experience do you have in this profession?",
        about_me="Add a bio.",
        github="Add a link to your GitHub profile.",
        x="Add a link to your 𝕏 profile.",
        upwork="Add a link to your Upwork profile.",
        project="Upload a project.",
    )
    async def create(
        self,
        interaction: Interaction,
        full_name: str,
        professional_skill: str,
        key_skills: str,
        experience: str,
        about_me: str,
        github: str = None,
        x: str = None,
        upwork: str = None,
        project: Attachment = None,
    ):
        try:
            # Create portfolio table
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS users_portfolio (
                        user_id INTEGER PRIMARY KEY,
                        full_name TEXT,
                        professional_skill TEXT,
                        key_skills TEXT,
                        experience TEXT,
                        about_me TEXT,
                        github TEXT,
                        x TEXT,
                        upwork TEXT,
                        project_url TEXT
            """
            )
            self.conn.commit()

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

            # Load user data from database on bot startup
            user_id = interaction.user.id

            query = """SELECT * FROM users_portfolio WHERE user_id = ?"""
            self.cursor.execute(query, (user_id,))
            self.conn.commit()

            user_info = self.cursor.fetchone()

            if user_info:
                await interaction.response.send_message(
                    "You already have a portfolio. Use /portfolio_edit to edit.",
                    ephemeral=True,
                )
                return

            project_url = None

            if project is not None:
                project_url = project.url

            user_info = (
                user_id,
                full_name,
                professional_skill,
                key_skills,
                experience,
                about_me,
                github,
                x,
                upwork,
                project_url,
                # Add more information here later
            )

            # Insert user data to database
            query = """INSERT INTO users_portfolio (
                user_id,
                full_name,
                professional_skill,
                key_skills,
                experience,
                about_me,
                github,
                x,
                upwork,
                project_url
                )
                VALUES
                (?,?,?,?,?,?,?,?,?,?)
                """

            self.cursor.execute(query, user_info)
            self.conn.commit()

            await interaction.response.send_message(
                f"Portfolio saved! Use */portfolio_show* to show portfolio.",
                ephemeral=True,
            )
        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"Error occurred: {e}")

    @portfolio.command(name="show", description="Show your portfolio.")
    @app_commands.describe(member="Whose portfolio?")
    async def show(
        self,
        interaction: Interaction,
        member: discord.Member = None,
    ):
        try:
            # If member parameter is not provided, default to the interaction user
            if member is None:
                member = interaction.user

            # Get the profile picture URL of the mentioned member, if any
            profile_pic_url = member.avatar.url

            user_id = member.id

            query = """SELECT * FROM users_portfolio WHERE user_id = ?"""
            self.cursor.execute(query, (user_id,))
            user_info = self.cursor.fetchone()

            if user_info is None:
                # If user_info is None, it means the user doesn't have a portfolio
                await interaction.response.send_message(
                    f"{member.display_name} hasn't created a portfolio yet.",
                    ephemeral=True,
                )
                return

            (
                _,
                full_name,
                professional_skill,
                key_skills,
                experience,
                about_me,
                github,
                x,
                upwork,
                project_url,
            ) = user_info

            # Split the string of key skills into a list
            key_skills = [skill.strip() for skill in key_skills.split(",")]

            embed = Embed(title=professional_skill)
            embed.set_author(
                name=full_name,
                icon_url=profile_pic_url,
                url=f"https://www.discordapp.com/users/{user_id}",
            )
            embed.add_field(name="Key Skills", value="\n".join(key_skills))
            embed.add_field(name="Experience", value=experience)
            embed.add_field(name="About me:", value=about_me, inline=False)

            if github:
                embed.add_field(name="", value=f"[GitHub]({github})", inline=True)
            if x:
                embed.add_field(name="", value=f"[𝕏]({x})", inline=False)
            if upwork:
                embed.add_field(name="", value=f"[UpWork]({upwork})", inline=False)

            if project_url:
                embed.set_image(url=project_url)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"Error occurred: {e}")

    @portfolio.command(name="edit", description="Edit your portfolio.")
    @app_commands.describe(
        full_name="Edit your full name.",
        professional_skill="Edit your professional skill.",
        key_skills="Edit your key skills. (Separate each skill with a comma)",
        experience="Edit your years of experience.",
        about_me="Edit your bio.",
        github="Edit your GitHub profile link.",
        x="Edit your 𝕏 profile link.",
        upwork="Edit your Upwork profile link.",
    )
    async def edit(
        self,
        interaction: Interaction,
        full_name: str = None,
        professional_skill: str = None,
        about_me: str = None,
        key_skills: str = None,
        experience: str = None,
        github: str = None,
        x: str = None,
        upwork: str = None,
    ):
        if interaction.guild.id is not guild_id:
            return
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

        user_id = interaction.user.id
        query = """SELECT * FROM users_portfolio WHERE user_id = ?"""
        self.cursor.execute(query, (user_id,))
        user_info = self.cursor.fetchone()
        if not user_info:
            await interaction.response.send_message(
                "You haven't created a portfolio yet. Use */portfolio_create* to create one.",
                ephemeral=True,
            )
            return

        # Update user data with edited information
        if full_name is not None:
            query = """UPDATE users_portfolio SET full_name = ? WHERE user_id = ?"""
            self.cursor.execute(query, (full_name, user_id))
        if professional_skill is not None:
            query = """UPDATE users_portfolio SET professional_skill = ? WHERE user_id = ?"""
            self.cursor.execute(query, (professional_skill, user_id))
        if about_me is not None:
            query = """UPDATE users_portfolio SET about_me = ? WHERE user_id = ?"""
            self.cursor.execute(query, (about_me, user_id))
        if key_skills is not None:
            query = """UPDATE users_portfolio SET key_skills = ? WHERE user_id = ?"""
            self.cursor.execute(query, (key_skills, user_id))
        if experience is not None:
            query = """UPDATE users_portfolio SET experience = ? WHERE user_id = ?"""
            self.cursor.execute(query, (experience, user_id))
        if github is not None:
            query = """UPDATE users_portfolio SET github = ? WHERE user_id = ?"""
            self.cursor.execute(query, (github, user_id))
        if x is not None:
            query = """UPDATE users_portfolio SET x = ? WHERE user_id = ?"""
            self.cursor.execute(query, (x, user_id))
        if upwork is not None:
            query = """UPDATE users_portfolio SET upwork = ? WHERE user_id = ?"""
            self.cursor.execute(query, (upwork, user_id))
        self.conn.commit()
        await interaction.response.send_message(
            "Portfolio updated successfully!", ephemeral=True
        )

    @portfolio.command(name="delete", description="Delete your portfolio")
    async def delete(self, interaction: Interaction):
        try:
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

            user_id = interaction.user.id

            query = """SELECT * FROM users_portfolio WHERE user_id = ?"""
            self.cursor.execute(query, (user_id,))
            user_info = self.cursor.fetchone()
            if not user_info:
                await interaction.response.send_message(
                    "You haven't created a portfolio yet.", ephemeral=True
                )
                return
            query = """DELETE FROM users_portfolio WHERE user_id = ?"""
            self.cursor.execute(query, (user_id,))
            self.conn.commit()

            await interaction.response.send_message(
                "Portfolio deleted successfully!", ephemeral=True
            )
        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"Error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Portfolio(bot))
