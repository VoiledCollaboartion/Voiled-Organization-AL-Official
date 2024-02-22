import asyncio
import re
import sqlite3
import sys
from datetime import datetime, timedelta

from discord import Color, DMChannel, Embed, Interaction, Member, app_commands
from discord.ext import commands, tasks

sys.path.append("setup")
from setup import PROGRESS_CHANNEL_ID

tdb_path = "databases/tasks.db"


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
        print("Task.py is ready!")

    task = app_commands.Group(name="task", description="Task")

    @task.command(name="set", description="Set task.")
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
        time="In what time? Use [*d, *w, *m], '*' represents number.",
        interval="At what interval should member be reminded before the due date?",
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

            current_date = datetime.now().replace(microsecond=0)
            print(current_date)
            # current_date = current_date.strftime("%H:%M:%S")

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

            await interaction.response.send_message(
                f"Task set for {member.mention}: {body} due in {count} {unit}."
            )

            # Create an Embed object with the specified color and header
            header = "YOU HAVE A NEW TASK"
            msg = f"# {title}\n```{body}```"
            footer = f"Due in {time}"
            embed = Embed(title=header, description=msg, color=Color.yellow())
            embed.set_footer(text=footer)

            await member.send(embed=embed)

        except Exception as e:
            # Handle the exception
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            print(f"Error occurred: {e}")

    async def task_now(self, member, title, body):
        header = "YOUR TASK IS DUE NOW!"
        msg = f"# {title}\n```{body}```"
        embed = Embed(title=header, description=msg, color=Color.yellow())

        await member.send(embed=embed)
        # Delete task from database
        query = """DELETE FROM reminders WHERE user_id = ? AND title = ?"""
        self.cursor.execute(query, (member.id, title))
        self.conn.commit()

    async def send_reminder(self, member, title, body, interval):
        current_date = datetime.now().replace(microsecond=0)
        next_reminder_date = current_date + timedelta(days=interval)
        header = "TASK REMINDER"
        msg = f"# {title}\n```{body}```\nYour replies to this message would be forwarded to the progress channel."
        embed = Embed(title=header, description=msg, color=Color.yellow())

        sent_msg = await member.send(embed=embed)
        reminder_msg_id = sent_msg.id

        # Update next reminder date
        query = """UPDATE reminders SET next_reminder_date = ? AND reminder_msg_id = ? WHERE user_id = ? AND title = ?"""
        self.cursor.execute(
            query, (next_reminder_date, reminder_msg_id, member.id, title)
        )
        self.conn.commit()

    async def forward_reply(self, message, reminder_msg_id, title):
        # Check if the message is a reply to a message sent via DM by the bot
        if message.reference and reminder_msg_id == message.reference.message_id:
            progress_channel = self.bot.get_channel(PROGRESS_CHANNEL_ID)
            await progress_channel.send(
                f"Update on {title} from {message.author}: ```{message.content}```"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # Fetch the reminder_msg_id and title from the database
        self.cursor.execute("""SELECT reminder_msg_id, title FROM reminders""")
        rows = self.cursor.fetchall()
        for row in rows:
            reminder_msg_id, title = row
            # Pass the reminder_msg_id and title to forward_reply
            await self.forward_reply(message, reminder_msg_id, title)

    @tasks.loop(seconds=10)
    async def check_tasks(self):
        try:
            # Fetch tasks from database
            self.cursor.execute("""SELECT * FROM reminders""")
            tasks = self.cursor.fetchall()

            for task in tasks:
                user_id, title, body, due_date, next_reminder_date, interval, _ = task
                member = self.bot.get_user(user_id)
                current_date = datetime.now().replace(microsecond=0)
                due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")

                if next_reminder_date:
                    next_reminder_date = datetime.strptime(
                        next_reminder_date, "%Y-%m-%d %H:%M:%S"
                    )
                    if next_reminder_date <= current_date:
                        await self.send_reminder(member, title, body, interval)

                    if next_reminder_date >= due_date:
                        query = """UPDATE reminders SET next_reminder_date = NULL WHERE user_id = ? AND title = ?"""
                        self.cursor.execute(query, (member.id, title))
                        self.conn.commit()

                if current_date >= due_date:
                    await self.task_now(member, title, body)
        except Exception as e:
            print(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(Task(bot))
