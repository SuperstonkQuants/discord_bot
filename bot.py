from itertools import cycle
from os import listdir
import os
from discord.ext import commands, tasks
from discord import Intents
from discord.ext.commands import Bot
import discord
from dotenv import load_dotenv
import logging

intents = Intents().all()

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.DEBUG)


def get_prefix(bot, message):
    """This function returns a Prefix for our bot's commands.

    Args:
        bot (commands.Bot): The bot that is invoking this function.
        message (discord.Message): The message that is invoking.

    Returns:
        string or iterable containing strings: A string containing prefix or an iterable containing prefixes
    Notes:
        Through a database (or even a json) this function can be modified to returns per server prefixes.
        This function should returns only strings or iterable containing strings.
        This function shouldn't returns numeric values (int, float, complex).
        Empty strings as the prefix always matches, and should be avoided, at least in guilds.
    """
    if not isinstance(message.guild, discord.Guild):
        """Checks if the bot isn't inside of a guild. 
        Returns a prefix string if true, otherwise passes.
        """
        return '!'

    return ['!', '?', '>']


# bot = commands.Bot(command_prefix=get_prefix, description='SuperstonkQuantBot Commands', intents=intents)
bot = Bot(command_prefix=get_prefix, description='SuperstonkQuantBot Commands', intents=intents)

if __name__ == '__main__':
    """Loads the cogs from the `./cogs` folder."""
    for cog in listdir('./cogs'):
        if cog.endswith('.py'):
            bot.load_extension(f'cogs.{cog[:-3]}')


# This is the decorator for events (outside of cogs).
@bot.event
async def on_ready():
    """This coroutine is called when the bot is connected to Discord.
    Note:
        `on_ready` doesn't take any arguments.

    Documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_ready
    """
    print(f'{bot.user.name} is online and ready!')

    change_status.start()


# Starts the task `change_status`_.
statuslist = cycle([
    'Pythoning',
    'Doing stuff...',
    'Getting Kenny Some Mayo',
])


@tasks.loop(seconds=16)
async def change_status():
    """This is a background task that loops every 16 seconds.
    The coroutine looped with this task will change status over time.
    The statuses used are in the cycle list called `statuslist`_.

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
    """
    await bot.change_presence(activity=discord.Game(next(statuslist)))
    # Changes the bot status to `Pythoning`_.


# This is the decorator for commands (outside of cogs).
@bot.command()
async def greet(ctx):
    """This coroutine sends a greeting message when called by the command.
    Note:
        All commands must be preceded by the bot prefix.
    """
    await ctx.send(f'Hello {ctx.message.author.mention}!')
    # The bot send a message on the channel that is being invoked in and mention the invoker.


bot.run(TOKEN)  # Runs the bot with its token. Don't put code below this command.
