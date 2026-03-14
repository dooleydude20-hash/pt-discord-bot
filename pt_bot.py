import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

push_submissions = set()
sit_submissions = set()

push_missed = {}
sit_missed = {}

TIMEZONE = pytz.timezone("US/Eastern")

REMINDER_TIMES = ["09:00","11:00","13:00","15:00","18:00","21:00","23:00"]

PUSH_CHANNEL = "pushups-submissions"
SIT_CHANNEL = "situps-submissions"

PUSH_ROLE = "Push Ups"
SIT_ROLE = "Sit Ups"

STATUS_CHANNEL = "pt-status"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    reminder_loop.start()
    midnight_reset.start()
    daily_report.start()


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.attachments:

        for file in message.attachments:

            if file.filename.endswith((".mp4",".mov",".webm",".mkv")):

                if message.channel.name == PUSH_CHANNEL:

                    if message.author.id not in push_submissions:
                        push_submissions.add(message.author.id)
                        await message.channel.send(
                            f"{message.author.mention} Push Ups submission recorded."
                        )

                elif message.channel.name == SIT_CHANNEL:

                    if message.author.id not in sit_submissions:
                        sit_submissions.add(message.author.id)
                        await message.channel.send(
                            f"{message.author.mention} Sit Ups submission recorded."
                        )

    await bot.process_commands(message)


@bot.command()
async def status(ctx):

    guild = ctx.guild

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    push_done = []
    push_missing = []

    sit_done = []
    sit_missing = []

    for member in push_role.members:
        if member.id in push_submissions:
            push_done.append(member.display_name)
        else:
            push_missing.append(member.display_name)

    for member in sit_role.members:
        if member.id in sit_submissions:
            sit_done.append(member.display_name)
        else:
            sit_missing.append(member.display_name)

    report = f"""
Push Ups Submitted
{chr(10).join(push_done) or "None"}

Push Ups Missing
{chr(10).join(push_missing) or "None"}

Sit Ups Submitted
{chr(10).join(sit_done) or "None"}

Sit Ups Missing
{chr(10).join(sit_missing) or "None"}
"""

    await ctx.send(report)


@bot.command()
async def misses(ctx):

    guild = ctx.guild

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    report = []

    report.append("Push Ups Missed Days")

    for member in push_role.members:
        report.append(f"{member.display_name} — {push_missed.get(member.id,0)}")

    report.append("\nSit Ups Missed Days")

    for member in sit_role.members:
        report.append(f"{member.display_name} — {sit_missed.get(member.id,0)}")

    await ctx.send("\n".join(report))


@tasks.loop(minutes=1)
async def reminder_loop():

    now = datetime.now(TIMEZONE).strftime("%H:%M")

    if now in REMINDER_TIMES:

        guild = bot.guilds[0]

        push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
        sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

        push_channel = discord.utils.get(guild.text_channels, name=PUSH_CHANNEL)
        sit_channel = discord.utils.get(guild.text_channels, name=SIT_CHANNEL)

        push_mentions = []
        sit_mentions = []

        for member in push_role.members:
            if member.id not in push_submissions:
                push_mentions.append(member.mention)

        for member in sit_role.members:
            if member.id not in sit_submissions:
                sit_mentions.append(member.mention)

        if push_mentions:
            await push_channel.send(
                "Reminder to submit PUSH UPS video:\n" + " ".join(push_mentions)
            )

        if sit_mentions:
            await sit_channel.send(
                "Reminder to submit SIT UPS video:\n" + " ".join(sit_mentions)
            )


@tasks.loop(time=time(23,59))
async def daily_report():

    guild = bot.guilds[0]

    status_channel = discord.utils.get(guild.text_channels, name=STATUS_CHANNEL)

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    push_done = []
    push_missing = []

    sit_done = []
    sit_missing = []

    for member in push_role.members:
        if member.id in push_submissions:
            push_done.append(member.display_name)
        else:
            push_missing.append(member.display_name)

    for member in sit_role.members:
        if member.id in sit_submissions:
            sit_done.append(member.display_name)
        else:
            sit_missing.append(member.display_name)

    report = f"""
PT Daily Report

Push Ups Submitted
{chr(10).join(push_done) or "None"}

Push Ups Missing
{chr(10).join(push_missing) or "None"}

Sit Ups Submitted
{chr(10).join(sit_done) or "None"}

Sit Ups Missing
{chr(10).join(sit_missing) or "None"}
"""

    await status_channel.send(report)


@tasks.loop(time=time(23,59))
async def midnight_reset():

    guild = bot.guilds[0]

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    for member in push_role.members:
        if member.id not in push_submissions:
            push_missed[member.id] = push_missed.get(member.id,0) + 1

    for member in sit_role.members:
        if member.id not in sit_submissions:
            sit_missed[member.id] = sit_missed.get(member.id,0) + 1

    push_submissions.clear()
    sit_submissions.clear()


bot.run(TOKEN)
