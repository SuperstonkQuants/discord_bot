import logging.config
import os
import discord
from itertools import cycle
from os import listdir
from util.messages import WarnMessage
from discord import Intents
from discord.ext import commands, tasks
from discord.ext.commands import Bot

import constants

# Declare all intents
intents = Intents().all()

# Declare discord token, defined in constants.py
TOKEN = constants.Tokens.DISCORD_TOKEN

# Get and set constant file paths
constants.FilePaths.ROOT_PATH = os.path.abspath(os.getcwd())
constants.FilePaths.COGS_PATH = f"{constants.FilePaths.ROOT_PATH}{os.sep}cogs"
constants.FilePaths.STORAGE_PATH = f"{constants.FilePaths.ROOT_PATH}{os.sep}storage"
constants.FilePaths.IMAGES_PATH = f"{constants.FilePaths.ROOT_PATH}{os.sep}images"

# Setup logging to console and file
# Documentation: https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
logging.config.fileConfig(f"{constants.FilePaths.ROOT_PATH}{os.sep}config{os.sep}logging.conf")
log = logging.getLogger('discord')

log.info("Starting discordbot ...")


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


bot = Bot(
    command_prefix=get_prefix,
    description='SuperstonkQuantBot Commands',
    intents=intents,
    case_insensitive=True
 )

# Load all cogs
if __name__ == '__main__':
    """Loads the cogs from the `./cogs` folder."""
    for cog in listdir(f"{constants.FilePaths.COGS_PATH}"):
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


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(f"{ctx.author.mention} That command wasn't found! Sorry :(")
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(f"{ctx.author.mention} {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        embed = WarnMessage(f"You are missing something :disappointed_relieved:", f"Use `!{ctx.command} {' '.join(f'[{p}]' for p in ctx.command.clean_params)}`").new()
        embed.set_footer(text=f"For more information call !help {ctx.command}")
        await ctx.message.reply(embed=embed)

# Starts the task `change_status`_.
statuslist = cycle([
    'Pythoning',
    'Doing stuff...',
    'Getting Kenny Some Mayo',
    '!help for more info',
])


@tasks.loop(seconds=31)
async def change_status():
    """This is a background task that loops every 31 seconds.
    The coroutine looped with this task will change status over time.
    The statuses used are in the cycle list called `statuslist`_.

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
    """
    await bot.change_presence(activity=discord.Game(next(statuslist)))


# This is the decorator for commands (outside of cogs).
@bot.command()
async def greet(ctx):
    """This coroutine sends a greeting message when called by the command.
    Note:
        All commands must be preceded by the bot prefix.
    """
    await ctx.send(f'Hello {ctx.message.author.mention}!')
    # The bot send a message on the channel that is being invoked in and mention the invoker.


class HelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

bot.help_command = HelpCommand()

bot.run(TOKEN)  # Runs the bot with its token. Don't put code below this command.
