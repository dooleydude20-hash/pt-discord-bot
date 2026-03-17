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
last_reminder = None

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
                        await message.add_reaction("✅")

                elif message.channel.name == SIT_CHANNEL:

                    if message.author.id not in sit_submissions:
                        sit_submissions.add(message.author.id)
                        await message.add_reaction("✅")

    await bot.process_commands(message)


@bot.command()
async def status(ctx):

    guild = ctx.guild

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    if not push_role or not sit_role:
        await ctx.send("Roles not found.")
        return

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
**PT Status**

**Push Ups Submitted**
{chr(10).join(push_done) or "None"}

**Push Ups Missing**
{chr(10).join(push_missing) or "None"}

**Sit Ups Submitted**
{chr(10).join(sit_done) or "None"}

**Sit Ups Missing**
{chr(10).join(sit_missing) or "None"}
"""

    await ctx.send(report)


@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):

    push_submissions.discard(member.id)
    sit_submissions.discard(member.id)

    await ctx.send(f"{member.display_name}'s submissions have been reset.")


@tasks.loop(minutes=1)
async def reminder_loop():

    global last_reminder

    now = datetime.now(TIMEZONE).strftime("%H:%M")

    if now not in REMINDER_TIMES or now == last_reminder:
        return

    last_reminder = now

    guild = bot.guilds[0]

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    push_channel = discord.utils.get(guild.text_channels, name=PUSH_CHANNEL)
    sit_channel = discord.utils.get(guild.text_channels, name=SIT_CHANNEL)

    if not push_role or not sit_role:
        return

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
            "**Reminder: Submit PUSH UPS video**\n" + " ".join(push_mentions)
        )

    if sit_mentions:
        await sit_channel.send(
            "**Reminder: Submit SIT UPS video**\n" + " ".join(sit_mentions)
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
**PT Daily Report**

**Push Ups Submitted**
{chr(10).join(push_done) or "None"}

**Push Ups Missing**
{chr(10).join(push_missing) or "None"}

**Sit Ups Submitted**
{chr(10).join(sit_done) or "None"}

**Sit Ups Missing**
{chr(10).join(sit_missing) or "None"}
"""

    await status_channel.send(report)


@tasks.loop(time=time(0,0))
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
