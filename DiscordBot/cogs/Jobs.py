import sqlite3
import sys

import discord.ui
from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

sys.path.append("setup")
from setup import FORUM_CHANNEL_ID, GUILD_ID

jdb_path = "databases/jobs.db"

conn = sqlite3.connect(jdb_path)
c = conn.cursor()

c.execute(
    """CREATE TABLE IF NOT EXISTS jobs (
    thread_id INTEGER PRIMARY KEY,
    job_poster_id INTEGER
    )"""
)
conn.commit()


def save_job_post(thread_id, job_poster_id):
    try:
        c.execute(
            """INSERT OR REPLACE INTO jobs 
                (thread_id, job_poster_id) VALUES (?, ?)""",
            (thread_id, job_poster_id),
        )
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")


def load_job_post(thread_id):
    try:
        c.execute(
            """SELECT job_poster_id FROM jobs WHERE thread_id = ?""", (thread_id,)
        )
        result = c.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"An error occurred: {e}")

c.execute(
    """CREATE TABLE IF NOT EXISTS job_applications (
    thread_id INTEGER,
    applicant_id INTEGER,
    status TEXT,
    PRIMARY KEY (thread_id, applicant_id)
    )"""
)
conn.commit()


def save_application(thread_id, applicant_id, status="pending"):
    try:
        c.execute(
            """
                  INSERT OR REPLACE INTO job_applications 
                  (thread_id, applicant_id, status)
                  VALUES (?, ?, ?)
                  """,
            (thread_id, applicant_id, status),
        )
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")


def check_application_status(thread_id, applicant_id):
    try:
        c.execute(
            """SELECT status FROM job_applications 
                WHERE thread_id = ? AND applicant_id = ?""",
            (thread_id, applicant_id),
        )
        result = c.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


class JobsModal(discord.ui.Modal, title="Post A Job"):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    try:
        job_title = discord.ui.TextInput(
            label="An appropriate title for your job", placeholder="Title"
        )
        description = discord.ui.TextInput(
            label="An appropriate description for your job",
            placeholder="Description",
            style=discord.TextStyle.long,
        )

        async def on_submit(self, interaction: Interaction):
            forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
            job_poster = interaction.user

            if isinstance(forum_channel, discord.ForumChannel):
                apply_view = ApplyView(self.bot, job_poster.id)
                embed = Embed(
                    color=Color.blurple(),
                )
                # Use display_avatar which guarantees an avatar, whether custom or default
                embed.set_author(
                    name=job_poster.name,
                    icon_url=job_poster.display_avatar.url,
                    url=f"https://www.discordapp.com/users/{job_poster.id}",
                )
                embed.add_field(name="", value=self.description.value)

                post = await forum_channel.create_thread(
                    name=self.job_title.value,
                    embed=embed,
                    view=apply_view,
                )
                save_job_post(post.thread.id, job_poster.id)
                await interaction.response.send_message(
                    f"Post '{self.job_title.value}' created successfully!",
                    ephemeral=True,
                )

            else:
                await interaction.response.send_message("Invalid forum channel.")

    except Exception as e:
        print(f"An error occurred: {e}")


class AcceptView(discord.ui.View):
    def __init__(self, bot, applicant, thread_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.applicant = applicant
        self.thread_id = thread_id
        # Create the buttons
        self.accept_button = discord.ui.Button(
            label="Accept Proposal",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_proposal_{self.applicant.id}",
        )
        self.accept_button.callback = self.accept_proposal  # Assign callback manually

        self.decline_button = discord.ui.Button(
            label="Decline Proposal",
            style=discord.ButtonStyle.danger,
            custom_id=f"decline_proposal_{self.applicant.id}",
        )
        self.decline_button.callback = self.decline_proposal  # Assign callback manually

        # Add buttons to the view only once
        self.add_item(self.accept_button)
        self.add_item(self.decline_button)

    async def accept_proposal(self, interaction: Interaction):
        try:
            # Disable both buttons
            self.accept_button.disabled = True
            self.decline_button.disabled = True

            guild = self.bot.get_guild(GUILD_ID)
            # Defer the response to allow editing the original message
            await interaction.response.defer()

            # Fetch the applicant and send them a message
            applicant_id = self.accept_button.custom_id.split("_")[-1]
            applicant = await self.bot.fetch_user(int(applicant_id))
            job_post_link = f"https://discord.com/channels/{guild.id}/{self.thread_id}"
            await applicant.send(f"Your job proposal to {job_post_link} was accepted.")

            # Edit only the view (buttons), keeping the cover letter and other content intact
            await interaction.edit_original_response(view=self)
            await interaction.followup.send("You accepted this job proposal.")

            # Create permissions for the category
            # Admin role should have administrator access
            admin_role = discord.utils.get(
                guild.roles, permissions=discord.Permissions(administrator=True)
            )

            # Define the permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),  # Deny everyone else
                applicant: discord.PermissionOverwrite(
                    view_channel=True
                ),  # Allow applicant
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True
                ),  # Allow job poster
            }

            # Add admin role if found
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)

            # Check if category already exists
            category_name = f"{interaction.user.name}'s Project Workspace"
            category = discord.utils.get(guild.categories, name=category_name)

            if not category:
                # If category does not exist, create a new one
                category = await guild.create_category(
                    category_name, overwrites=overwrites
                )

                # Create channels under the new category with emojis in the names
                await guild.create_text_channel("📄┃information", category=category)
                await guild.create_text_channel("🔔┃notifications", category=category)
                await guild.create_text_channel("📋┃tasks", category=category)
                await guild.create_text_channel("📈┃progress", category=category)
                workdesk_channel = await guild.create_text_channel(
                    "💻┃workdesk", category=category
                )

                # Create a voice channel under the new category with an emoji
                await guild.create_voice_channel("🎤┃voice-chat", category=category)

                await interaction.user.send(
                    f"A project workspace has been created for your job posting in {guild.name}.\n"
                    f"Here is a direct link: https://discord.com/channels/{guild.id}/{workdesk_channel.id}"
                )

                # Create a voice channel under the new category with an emoji
                await guild.create_voice_channel("🎤┃voice-chat", category=category)

                await interaction.user.send(
                    f"A project workspace has been created for your job posting in {guild.name}.\n"
                    f"Here is a direct link: https://discord.com/channels/{guild.id}/{workdesk_channel.id}"
                )

            else:
                workdesk_channel = discord.utils.get(
                    category.channels, name="💻┃workdesk"
                )

            # Notify the applicant and job poster with the direct link to the 'information' channel
            await applicant.send(
                f"You have been invited to the project workspace in {guild.name} under the category '{category.name}'!\n"
                f"Here is a direct link: https://discord.com/channels/{guild.id}/{workdesk_channel.id}"
            )
            save_application(self.thread_id, self.applicant.id, status="accepted")
        except Exception as e:
            # Handle exceptions
            print(f"Error occurred: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

    async def decline_proposal(self, interaction: Interaction):
        try:
            # Disable both buttons
            self.accept_button.disabled = True
            self.decline_button.disabled = True

            # Defer the response to allow editing the original message
            await interaction.response.defer()

            # Fetch the applicant and send them a message
            applicant_id = self.decline_button.custom_id.split("_")[-1]
            applicant = await self.bot.fetch_user(int(applicant_id))
            await applicant.send("Your job proposal was declined.")
            await interaction.followup.send("You declined this job proposal.")

            # Edit only the view (buttons), keeping the cover letter and other content intact
            await interaction.edit_original_response(view=self)
            save_application(self.thread_id, self.applicant.id, status="rejected")
        except Exception as e:
            # Handle exceptions
            print(f"Error occurred: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


class JobsView(discord.ui.View):
    def __init__(
        self,
        bot,
    ):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Post Job", style=discord.ButtonStyle.blurple, custom_id="post_job"
    )
    async def button_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            modal = JobsModal(self.bot)
            return await interaction.response.send_modal(modal)
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )


class ApplyModal(discord.ui.Modal, title="Submit a proposal"):

    def __init__(self, bot, job_poster_id, applicant, thread_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.job_poster_id = job_poster_id
        self.applicant = applicant
        self.thread_id = thread_id

    try:
        letter = discord.ui.TextInput(
            label="Write your cover letter",
            placeholder="Cover Letter",
            style=discord.TextStyle.long,
        )

        async def on_submit(self, interaction: Interaction):
            embed = Embed(
                color=Color.blurple(),
            )
            # Use display_avatar which guarantees an avatar, whether custom or default
            embed.set_author(
                name=self.applicant.name,
                icon_url=self.applicant.display_avatar.url,
                url=f"https://www.discordapp.com/users/{self.applicant.id}",
            )
            embed.add_field(name="", value=self.letter.value)
            job_poster = await self.bot.fetch_user(self.job_poster_id)
            title = "New Job Application"
            description = f"{self.applicant.mention} applied to your job post."
            await job_poster.send(
                f"# {title}\n{description}",
                embed=embed,
                view=AcceptView(self.bot, self.applicant, self.thread_id),
            )
            await interaction.response.send_message(
                "Applied successfully!", ephemeral=True
            )

    except Exception as e:
        print(f"An error occurred: {e}")


class ApplyView(discord.ui.View):
    def __init__(
        self,
        bot,
        job_poster_id=None,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.job_poster_id = job_poster_id

    @discord.ui.button(
        label="Apply",
        style=discord.ButtonStyle.blurple,
        custom_id="apply_job",
    )
    async def button1_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            applicant = interaction.user

            thread_id = interaction.channel.id
            job_poster_id = self.job_poster_id or load_job_post(thread_id)

            # Check if the applicant is the job poster
            if applicant.id == job_poster_id:
                await interaction.response.send_message(
                    "You can't apply to your own job post!", ephemeral=True
                )
                return

            if job_poster_id is None:
                await interaction.response.send_message(
                    "Unable to find the job poster.", ephemeral=True
                )
                return

            # Check the application status
            status = check_application_status(thread_id, applicant.id)

            if status == "pending":
                await interaction.response.send_message(
                    "You have already applied to this job. Wait for a response before reapplying.",
                    ephemeral=True,
                )

            elif status == "accepted":
                await interaction.response.send_message(
                    "Your application has already been accepted!", ephemeral=True
                )
                return

            modal = ApplyModal(self.bot, job_poster_id, applicant, thread_id)
            await interaction.response.send_modal(modal)

            # Save the application as 'pending'
            save_application(thread_id, applicant.id, status="pending")

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="close_job",
    )
    async def button2_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            thread_id = interaction.channel.id
            job_poster_id = self.job_poster_id or load_job_post(thread_id)

            guild = interaction.guild

            # Check if the user is the allowed user or has admin permissions
            admin_role = discord.utils.get(
                guild.roles, permissions=discord.Permissions(administrator=True)
            )
            user_has_admin = (
                admin_role in interaction.user.roles if admin_role else False
            )

            # Check if the button user is the job poster or admin
            if interaction.user.id == job_poster_id or user_has_admin:
                thread = interaction.channel
                await thread.delete()

            else:
                await interaction.response.send_message(
                    "You are not allowed to do that!", ephemeral=True
                )
                return

        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )

    @discord.ui.button(
        label="Bump",
        style=discord.ButtonStyle.green,
        custom_id="bump_post",
    )
    async def button3_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            # Check if the button user is the job poster or admin
            thread_id = interaction.channel.id
            job_poster_id = self.job_poster_id or load_job_post(thread_id)
            if interaction.user.id == job_poster_id:
                await interaction.response.send_message(
                    "Bump successful!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You are not allowed to do that!", ephemeral=True
                )
                return
        except Exception as e:
            # Handle the exception
            print(f"Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )


class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.add_view(JobsView(self.bot))
            self.bot.add_view(ApplyView(self.bot))
            print("Jobs.py is ready!")
        except Exception as e:
            print(f"An error occurred: {e}")

    jobs = app_commands.Group(name="jobs", description="Jobs")

    @jobs.command(
        name="send_embed", description="Send POST JOB embedded message (admin only)."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def Jobs(self, interaction: Interaction):
        try:
            await interaction.response.send_message(view=JobsView(self.bot))
        except Exception as e:
            print(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Jobs(bot))
