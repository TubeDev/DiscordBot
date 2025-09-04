import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
import random


# settings
DEFAULT_CREDITS = 10    # Starter credits
MIN_BET = 1             # Minimal bet for gamble
WORK_CREDITS = 2        # Reward for correct work
FAIL_CREDITS = 1        # Penalty for wrong work
DEVELOPER_IDs = (
    845391619050176524,
)
USER_CREDITS = {
}


# get token
load_dotenv("banana.txt")
TOKEN = os.getenv("DISCORD_TOKEN")


# log handler
handler = logging.FileHandler(filename="fancy_stuff.log", mode="a", encoding="utf-8")
logger = logging.getLogger("Main")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# intents & get bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)



# --- events ---
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync slash cmds: {e}")
    
    logger.critical("BOT connected")



# --- slash commands ---
# info command
@bot.tree.command(name="info", description="Get info on your current balance")
async def info(interaction: discord.Interaction):
    user_id = interaction.user.id
    credits = USER_CREDITS.setdefault(user_id, DEFAULT_CREDITS)
    await interaction.response.send_message(f"💳 Your current account balance: {credits} credits")


# gamble command
@bot.tree.command(name="gamble", description="Gamble! Bet your credits, get double or lose it all")
async def gamble(interaction: discord.Interaction, bet: int):
    user_id = interaction.user.id
    credits = USER_CREDITS.setdefault(user_id, DEFAULT_CREDITS)

    if bet < MIN_BET:
        await interaction.response.send_message(f"⛔ Minimum bet is {MIN_BET} credits")
    elif bet > credits:
        await interaction.response.send_message(f"⛔ You cannot bet {bet}, you only have {credits} credits")
    else:
        k = random.choice([-1, 1])
        if k == -1:
            USER_CREDITS[user_id] -= bet
            await interaction.response.send_message(f"💔 You lost...    💳 Your bet of {bet} credits removed from your balance")
        elif k == 1:
            USER_CREDITS[user_id] += bet
            await interaction.response.send_message(f"🍀 You won!    💳 Added {bet} credits added to your balance")


# work command
class WorkModal(discord.ui.Modal, title="Work"):
    def __init__(self):
        super().__init__()
        
        self.operator = random.choice(["+", "-"])
        self.num1 = random.randint(0, 100)
        self.num2 = random.randint(0, 100)
        self.correct_answer = self.num1 + self.num2 if self.operator == "+" else self.num1 - self.num2
        
        self.answer = discord.ui.TextInput(label=f"📄 Work: {self.num1} {self.operator} {self.num2} = ?")
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        USER_CREDITS.setdefault(user_id, DEFAULT_CREDITS)
        
        if self.answer.value.strip() == str(self.correct_answer):
            USER_CREDITS[user_id] += WORK_CREDITS
            await interaction.response.send_message(f"🟢 Correct!    💳 + {WORK_CREDITS} credits | Balance: {USER_CREDITS[user_id]}")
        else:
            USER_CREDITS[user_id] -= FAIL_CREDITS
            await interaction.response.send_message(f"🔴 Incorrect!    💳 - {FAIL_CREDITS} credits | Balance: {USER_CREDITS[user_id]}")

@bot.tree.command(name="work", description="Work to get credits")
async def work(interaction: discord.Interaction):
    await interaction.response.send_modal(WorkModal())


# hello command
@bot.tree.command(name="hello", description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"👋 Hello {interaction.user.display_name}, I am Codie")


# dice command
@bot.tree.command(name="dice", description="Roll the dice!")
async def dice(interaction: discord.Interaction):
    roll = random.randint(1, 6)
    await interaction.response.send_message(f"🎲 Dice says: {roll}")


# ping command
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("check DMs 👀", ephemeral=True)
    await interaction.user.send("Pong")


# count command
user_cooldowns = {}
@bot.tree.command(name="count", description="Count to 'x'")
async def count(interaction: discord.Interaction, x: int):
    user_id = interaction.user.id
    
    if user_cooldowns.get(user_id, False):
        await interaction.response.send_message("NO! WAIT!")
        return
    
    user_cooldowns[user_id] = True
    try:
        if x > 30:
            txt = """⛔ I will only count to max of 30...
I bet you wanted to clog the chat by putting this ridiculously big number 💀"""
            await interaction.response.send_message(txt)
        else:
            await interaction.response.send_message(f"🧮 Counting to {x}...")
            for i in range(x):
                await interaction.channel.send(i+1)
    finally:
        if user_id in user_cooldowns:
            del user_cooldowns[user_id]



# --- prefix commands ---
# add_credit command
@bot.command()
async def add_credit(ctx: commands.Context, user: discord.User, amount: int):
    if ctx.author.id in DEVELOPER_IDs:
        USER_CREDITS.setdefault(user.id, DEFAULT_CREDITS)
        USER_CREDITS[user.id] += amount
        txt = f"Added {amount} credits to {user.mention}'s account balance\n\n💳 New balance: {USER_CREDITS[user.id]}"
        embed = discord.Embed(title=">>", description=txt, color=0x00FF00)
        await ctx.send(embed=embed)
    else:
        txt = "ERROR: Only bot developers can do this"
        embed = discord.Embed(title=">> access error", description=txt, color=0xFFFF00)
        await ctx.reply(embed=embed)


# set_credit command
@bot.command()
async def set_credit(ctx: commands.Context, user: discord.User, amount: int):
    if ctx.author.id in DEVELOPER_IDs:
        USER_CREDITS[user.id] = amount
        txt = f"Set {user.mention}'s account balance to {amount} credits\n\n💳 New balance: {USER_CREDITS[user.id]}"
        embed = discord.Embed(title=">>", description=txt, color=0x00FF00)
        await ctx.send(embed=embed)
    else:
        txt = "ERROR: Only bot developers can do this"
        embed = discord.Embed(title=">> access error", description=txt, color=0xFFFF00)
        await ctx.reply(embed=embed)


# status command
@bot.command()
async def status(ctx: commands.Context):
    txt = f"command invoked by: {ctx.author.mention}\n**system_status= NOMINAL**"
    embed = discord.Embed(title=">> status request invoke", description=txt, color=0x00FFC2)
    await ctx.send(embed=embed)


# terminate command
@bot.command()
async def terminate(ctx: commands.Context):
    if ctx.author.id in DEVELOPER_IDs:
        txt = """
---
System initiated bot shutdown protocol:
Terminating background processes...
---
**Status: OFFLINE**"""
        embed = discord.Embed(title="__BOT SHUTDOWN__", description=txt, color=0x9000FF)
        await ctx.send(embed=embed)
        logger.critical("Bot shut down by a discord command")
        await bot.close()
    else:
        txt = "ERROR: Only bot developers can do this"
        embed = discord.Embed(title=">> access error", description=txt, color=0xFFFF00)
        await ctx.reply(embed=embed)



# run the bot
class TokenError(Exception):
    pass

logger.critical("Bot start")
if TOKEN is None:
    logger.warning("[WARNING] Main: Attempt to start the bot with no token")
    raise TokenError("Attempt to start the bot with no token")
else:
    try:
        bot.run(token=TOKEN, log_handler=handler)
    except:
        logger.warning("Connection failed, token may be invalid")
        raise TokenError("Connection failed, token may be invalid")