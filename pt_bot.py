import discord
from discord.ext import commands, tasks
from datetime import datetime
import pytz
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

submissions = set()
missed_days = {}

TIMEZONE = pytz.timezone("US/Eastern")
REMINDER_TIMES = ["09:00","13:00","18:00","21:00"]

PUSH_ROLE = "Push Ups"
SIT_ROLE = "Sit Ups"

PUSH_CHANNEL = "pushups-submissions"
SIT_CHANNEL = "situps-submissions"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    reminder_loop.start()
    midnight_reset.start()


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.attachments:

        guild = message.guild
        push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
        sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

        for file in message.attachments:

            if file.filename.endswith((".mp4",".mov",".webm",".mkv")):

                correct_channel = False

                if message.channel.name == PUSH_CHANNEL and push_role in message.author.roles:
                    correct_channel = True

                if message.channel.name == SIT_CHANNEL and sit_role in message.author.roles:
                    correct_channel = True

                if correct_channel:

                    if message.author.id not in submissions:

                        submissions.add(message.author.id)

                        await message.channel.send(
                            f"{message.author.mention} submission recorded for today."
                        )

    await bot.process_commands(message)


@bot.command()
async def submitted(ctx):

    names = []

    for user_id in submissions:

        member = ctx.guild.get_member(user_id)

        if member:
            names.append(member.display_name)

    if names:
        await ctx.send("Submitted today:\n" + "\n".join(names))
    else:
        await ctx.send("No submissions yet.")


@bot.command()
async def missing(ctx):

    push_role = discord.utils.get(ctx.guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(ctx.guild.roles, name=SIT_ROLE)

    missing = []

    for member in push_role.members + sit_role.members:

        if member.id not in submissions:
            missing.append(member.display_name)

    if missing:
        await ctx.send("Missing submissions:\n" + "\n".join(missing))
    else:
        await ctx.send("Everyone submitted today.")


@bot.command()
async def misses(ctx):

    push_role = discord.utils.get(ctx.guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(ctx.guild.roles, name=SIT_ROLE)

    report = []

    for member in push_role.members + sit_role.members:

        misses = missed_days.get(member.id, 0)

        report.append(f"{member.display_name} — {misses}")

    await ctx.send("Missed Days:\n" + "\n".join(report))


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

            if member.id not in submissions:
                push_mentions.append(member.mention)

        for member in sit_role.members:

            if member.id not in submissions:
                sit_mentions.append(member.mention)

        if push_mentions:
            await push_channel.send(
                "Reminder to submit push-up PT video:\n" + " ".join(push_mentions)
            )

        if sit_mentions:
            await sit_channel.send(
                "Reminder to submit sit-up PT video:\n" + " ".join(sit_mentions)
            )


@tasks.loop(time=datetime.strptime("23:59","%H:%M").time())
async def midnight_reset():

    guild = bot.guilds[0]

    push_role = discord.utils.get(guild.roles, name=PUSH_ROLE)
    sit_role = discord.utils.get(guild.roles, name=SIT_ROLE)

    for member in push_role.members + sit_role.members:

        if member.id not in submissions:

            missed_days[member.id] = missed_days.get(member.id, 0) + 1

    submissions.clear()


bot.run(TOKEN)