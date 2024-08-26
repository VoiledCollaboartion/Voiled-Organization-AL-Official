import asyncio
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta

import discord.ui
from discord import Color, Embed, Interaction, Member, app_commands
from discord.ext import commands, tasks

sys.path.append("setup")
from setup import ADMIN_CHANNEL_ID, PROGRESS_CHANNEL_ID, guild_id

tdb_path = "databases/tasks.db"


class TaskView(discord.ui.View):
    def __init__(
        self,
        member_id=None,
        title=None,
        timeout=None,
    ):
        super().__init__(timeout=timeout)
        self.conn = sqlite3.connect(tdb_path)
        self.cursor = self.conn.cursor()
        self.member_id = member_id
        self.title = title

    @discord.ui.button(
        label="Add Time", style=discord.ButtonStyle.blurple, custom_id="add_task"
    )
    async def button1_callback(
        self, interaction: Interaction, button: discord.ui.Button
    ):
        try:
            # Implement the logic to add time to the tas
            # Fetch the task from the database
            query = """SELECT due_date FROM reminders WHERE user_id = ? AND title = ?"""
            self.cursor.execute(query, (self.member_id, self.title))
            due_date = self.cursor.fetchone()
            if not due_date:
                return await interaction.response.send_message(
                    "Task does not exist.", ephemeral=True
                )

            due_date = due_date[0]
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
            due_date = due_date.date()

            # Update the next reminder date based on the interval
            due_date += timedelta(days=1)

            # Update the database with the new next reminder date
            query = (
                """UPDATE reminders SET due_date = ? WHERE user_id = ? AND title = ?"""
            )
            self.cursor.execute(
                query,
                (
                    due_date,
                    self.member_id,
                    self.title,
                ),
            )
            self.conn.commit()

            return await interaction.response.send_message(
                "Time: [1 day] added to the task."
            )
        except Exception as e:
            # Handle the exception
            print(f"button1_callback Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )

    @discord.ui.button(
        label="Delete", style=discord.ButtonStyle.red, custom_id="delete_task"
    )
    async def button2_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Implement the logic to delete the task
        try:
            # Delete the task from the database
            query = """DELETE FROM reminders WHERE user_id = ? AND title = ?"""
            self.cursor.execute(query, (self.member_id, self.title))
            # Get the number of rows affected by the deletion
            rows_deleted = self.cursor.rowcount
            self.conn.commit()

            # Check if any rows were deleted
            if rows_deleted > 0:
                await interaction.response.send_message("Task deleted.")
            else:
                await interaction.response.send_message(
                    "Task doesn't exist.", ephemeral=True
                )

        except Exception as e:
            # Handle the exception
            print(f"button2_callback Error occurred: {e}")
            return await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )


class Task(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect(tdb_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS reminders (
                            user_id INTEGER,
                            title TEXT,
                            body TEXT,
                            due_date TEXT,
                            next_reminder_date TEXT,
                            interval INTEGER,
                            reminder_msg_id INTEGER
                )


                """
        )
        self.conn.commit()

        self.check_tasks.start()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.add_view(TaskView())
            print("Task.py is ready!")
        except Exception as e:
            # Handle the exception
            print(f"on_ready Error occurred: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.bot:
                return
            # Fetch the reminder_msg_id and title from the database
            self.cursor.execute("""SELECT reminder_msg_id, title FROM reminders""")
            rows = self.cursor.fetchall()
            for row in rows:
                reminder_msg_id, title = row
                # Pass the reminder_msg_id and title to forward_reply
                await self.forward_reply(message, reminder_msg_id, title)
        except Exception as e:
            # Handle the exception
            print(f"on_message Error occurred: {e}")

    task = app_commands.Group(name="task", description="Task")

    @task.command(name="set", description="Set task")
    @app_commands.choices(
        interval=[
            app_commands.Choice(name="Everyday", value=1),
            app_commands.Choice(name="Every 2 days", value=2),
            app_commands.Choice(name="Every week", value=7),
        ]
    )
    @app_commands.describe(
        member="Which member do you want to set a task for?",
        title="Input task title.",
        body="Input task content.",
        time="In what time? Use [*d, *w, *m], * represents number.",
        interval="At what interval should member be reminded before the due time?",
    )
    async def set(
        self,
        interaction: Interaction,
        member: Member,
        title: str,
        body: str,
        time: str,
        interval: app_commands.Choice[int],
    ):
        try:
            # Check if the user has the required permissions to execute this command
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )

            interval = interval.value

            current_date = date.today()

            # Parse the time input to determine the total number of seconds remaining
            count, unit = re.match(r"(\d+)([a-zA-Z])", time).groups()
            try:
                count = int(count)
            except ValueError:
                return await interaction.response.send_message(
                    "Invalid time unit. Please use [*d, *w, *m], '*' represents number.",
                    ephemeral=True,
                )

            unit = unit.lower()

            if unit == "d":
                pass

            elif unit == "w":
                count *= 7

            elif unit == "m":
                count *= 30

            else:
                return await interaction.response.send_message(
                    "Invalid time unit. Please use [*d, *w, *m], '*' represents number.",
                    ephemeral=True,
                )

            unit = "days"
            due_date = current_date + timedelta(days=count)
            next_reminder_date = current_date + timedelta(days=interval)

            query = """INSERT INTO reminders (user_id, title, body, due_date, next_reminder_date, interval) VALUES (?,?,?,?,?,?)"""
            self.cursor.execute(
                query, (member.id, title, body, due_date, next_reminder_date, interval)
            )
            self.conn.commit()

            # Create an Embed object with the specified color and header
            header = "YOU HAVE A NEW TASK"
            msg = f"# {title}\n```{body}```"
            footer = f"Due in {time}"
            embed = Embed(title=header, description=msg, color=Color.yellow())
            embed.set_footer(text=footer)

            await interaction.response.send_message(
                f"Task set for {member.mention}: {body} due in {count} {unit}.",
            )
            await member.send(embed=embed)

        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"set Error occurred: {e}")

    @task.command(name="show", description="Show all tasks for member")
    async def show(self, interaction: Interaction, member: Member):
        try:
            # Check if the user has the required permissions to execute this command
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )

            self.cursor.execute(
                """SELECT * FROM reminders WHERE user_id = ?""", (member.id,)
            )
            rows = self.cursor.fetchall()

            if not rows:
                return await interaction.response.send_message(
                    f"There are no tasks available for {member.mention}."
                )

            embed = Embed(title="Tasks", color=Color.yellow())
            counter = 0
            for row in rows:
                user_id, title, body, due_date, next_reminder_date, interval, _ = row
                current_date = date.today()
                due_date = datetime.strptime(due_date, "%Y-%m-%d")
                due_date = due_date.date()
                try:
                    next_reminder_date = datetime.strptime(
                        next_reminder_date, "%Y-%m-%d"
                    )
                    next_reminder_date = next_reminder_date.date()
                    nr_days_left = next_reminder_date - current_date

                    if nr_days_left.days == 1:
                        nr_days_left = "1 day"

                    else:
                        nr_days_left = f"{nr_days_left.days} days"
                except TypeError:
                    nr_days_left = (
                        "-"  # Handle the case where next_reminder_date is None
                    )
                dd_days_left = due_date - current_date

                if dd_days_left.days == 1:
                    dd_days_left = "1 day"

                else:
                    dd_days_left = f"{dd_days_left.days} days"

                counter += 1
                embed.set_author(
                    name=member.name,
                    icon_url=member.avatar.url,
                    url=f"https://www.discordapp.com/users/{user_id}",
                )
                embed.add_field(
                    name=f"{counter}. {title}",
                    value=f"```{body}```\nDue in: {dd_days_left}\nReminder: {nr_days_left}",
                    inline=False,
                )
                embed.add_field(
                    name="\u200b",  # Empty name for horizontal rule
                    value="\u200b",  # Empty value to display a horizontal rule
                    inline=False,
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"show Error occurred: {e}")

    @task.command(name="showall", description="Show list of members with pending tasks")
    @commands.guild_only()
    async def showall(self, interaction: Interaction):
        try:
            # Check if the user has the required permissions to execute this command
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )

            self.cursor.execute("""SELECT DISTINCT user_id FROM reminders""")
            user_ids = self.cursor.fetchall()

            if not user_ids:
                return await interaction.response.send_message(
                    "There are no tasks available.", ephemeral=True
                )

            embed = Embed(title="Users with Tasks", color=Color.yellow())

            for user_id in user_ids:
                for i in user_id:
                    user = await self.bot.fetch_user(i)
                    embed.add_field(
                        name=user.name,
                        value="",
                        inline=False,
                    )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"showall Error occurred: {e}")

    @task.command(name="delete", description="Delete a task for member")
    async def delete(self, interaction: Interaction, member: Member, number: int):
        try:
            # Check if the user has the required permissions to execute this command
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )

            self.cursor.execute(
                """SELECT * FROM reminders WHERE user_id = ?""", (member.id,)
            )
            rows = self.cursor.fetchall()

            if not rows:
                return await interaction.response.send_message(
                    f"There are no tasks available for {member.mention}."
                )

            if number <= 0 or number > len(rows):
                return await interaction.response.send_message(
                    f"Invalid task number. Please provide a number between 1 and {len(rows)}."
                )

            task_to_delete = rows[number - 1]  # Adjusting for 0-indexing

            self.cursor.execute(
                """DELETE FROM reminders WHERE user_id = ? AND title = ?""",
                (member.id, task_to_delete[1]),  # title is at index 1
            )
            # Commit the changes to the database
            self.conn.commit()

            await interaction.response.send_message(
                f"Task `{task_to_delete[1]}` has been deleted for {member.mention}."
            )

        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"delete Error occurred: {e}")

    async def task_now(self, member, title, body):
        try:
            header = "YOUR TASK IS DUE NOW!"
            msg = f"# {title}\n```{body}```"
            embed = Embed(title=header, description=msg, color=Color.yellow())

            await member.send(embed=embed)
            admin_channel = await self.bot.fetch_channel(ADMIN_CHANNEL_ID)

            header = f"DUE TASK"
            msg = f"{member.mention}\n**Title: {title}**\nDescription:\n```{body}```"
            embed = Embed(title=header, description=msg, color=Color.red())
            await admin_channel.send(
                embed=embed,
                view=TaskView(member.id, title),
            )
        except Exception as e:
            # Handle the exception
            print(f"task_now Error occurred: {e}")

    async def send_reminder(self, member, title, body, interval):
        try:
            current_date = date.today()
            next_reminder_date = current_date + timedelta(days=interval)
            header = "TASK REMINDER"
            msg = f"# {title}\n```{body}```\nYour replies to this message would be forwarded to the progress channel."
            embed = Embed(title=header, description=msg, color=Color.yellow())

            if member:
                sent_msg = await member.send(embed=embed)
                reminder_msg_id = sent_msg.id

                # Update next reminder date
                query = """UPDATE reminders SET reminder_msg_id = ? WHERE user_id = ? AND title = ?"""
                self.cursor.execute(query, (reminder_msg_id, member.id, title))
                self.conn.commit()

                # Update next reminder date
                query = """UPDATE reminders SET next_reminder_date = ?WHERE user_id = ? AND title = ?"""
                self.cursor.execute(query, (next_reminder_date, member.id, title))
                self.conn.commit()

        except Exception as e:
            # Handle the exception
            print(f"send_reminder Error occurred: {e}")

    async def forward_reply(self, message, reminder_msg_id, title):
        # Check if the message is a reply to a message sent via DM by the bot
        if message.reference and reminder_msg_id == message.reference.message_id:
            progress_channel = self.bot.get_channel(PROGRESS_CHANNEL_ID)
            await progress_channel.send(
                f"Update on {title} from {message.author.mention}: ```{message.content}```"
            )

    @tasks.loop(minutes=60)  # Make 1 hour
    async def check_tasks(self):
        try:
            print("Checking...")
            # Fetch tasks from database
            self.cursor.execute("""SELECT * FROM reminders""")
            tasks = self.cursor.fetchall()

            for task in tasks:
                user_id, title, body, due_date, next_reminder_date, interval, _ = task
                current_date = date.today()
                due_date = datetime.strptime(due_date, "%Y-%m-%d")
                due_date = due_date.date()

                if current_date >= due_date:
                    member = await self.bot.fetch_user(user_id)
                    await self.task_now(member, title, body)

                if next_reminder_date:
                    next_reminder_date = datetime.strptime(
                        next_reminder_date, "%Y-%m-%d"
                    )
                    next_reminder_date = next_reminder_date.date()
                    if next_reminder_date <= current_date:
                        member = self.bot.get_user(user_id)
                        await self.send_reminder(member, title, body, interval)

                    if next_reminder_date >= due_date:
                        query = """UPDATE reminders SET next_reminder_date = NULL WHERE user_id = ? AND title = ?"""
                        self.cursor.execute(query, (user_id, title))
                        self.conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Task(bot))
