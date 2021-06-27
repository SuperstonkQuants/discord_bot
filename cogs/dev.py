from os import listdir
from sys import version_info as sysv

import discord
from discord.ext import commands


class Dev(commands.Cog):
    """This is a cog with owner-only commands.
    Note:
        All cogs inherits from `commands.Cog`_.
        All cogs are classes, so they need self as first argument in their methods.
        All cogs use different decorators for commands and events (see example below).
        All cogs needs a setup function (see below).
    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
    """

    def __init__(self, bot):
        self.bot = bot

    # This is the decorator for events (inside of cogs).
    @commands.Cog.listener()
    async def on_ready(self):
        # Prints on the shell the version of Python and Discord.py installed in our computer.
        print(f'Python {sysv.major}.{sysv.minor}.{sysv.micro} - Disord.py {discord.__version__}\n')

    # This is the decorator for commands (inside of cogs).
    @commands.command(name='reloadall', hidden=True)  # This command is hidden from the help menu.
    # Only the owner (or owners) can use the commands decorated with this.
    @commands.is_owner()
    async def reload_all(self, ctx):
        """This commands reloads all the cogs in the `./cogs` folder.

        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command deletes its messages after 20 seconds."""

        message = await ctx.send('Reloading...')
        await ctx.message.delete()
        try:
            for cog in listdir('./cogs'):
                if cog.endswith('.py'):
                    self.bot.reload_extension(f'cogs.{cog[:-3]}')
        except Exception as exc:
            await message.edit(content=f'An error has occurred: {exc}', delete_after=20)
        else:
            await message.edit(content='All cogs have been reloaded.', delete_after=20)

    def check_cog(self, cog):
        """Returns the name of the cog in the correct format.
        Args:
            self
            cog (str): The cogname to check

        Returns:
            cog if cog starts with `cogs.`, otherwise an fstring with this format`cogs.{cog}`_.
        Note:
            All cognames are made lowercase with `.lower()`_.
        """
        if (cog.lower()).startswith('cogs.'):
            return cog.lower()
        return f'cogs.{cog.lower()}'

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load_cog(self, ctx, *, cog: str):
        """This commands loads the selected cog, as long as that cog is in the `./cogs` folder.

        Args:
            cog (str): The name of the cog to load. The name is checked with `.check_cog(cog)`_.

        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command deletes its messages after 20 seconds.
            :param ctx:
        """
        message = await ctx.send('Loading...')
        await ctx.message.delete()
        try:
            self.bot.load_extension(self.check_cog(cog))
        except Exception as exc:
            await message.edit(content=f'An error has occurred: {exc}', delete_after=20)
        else:
            await message.edit(content=f'{self.check_cog(cog)} has been loaded.', delete_after=20)

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload_cog(self, ctx, *, cog: str):
        """This commands unloads the selected cog, as long as that cog is in the `./cogs` folder.

        Args:
            cog (str): The name of the cog to unload. The name is checked with `.check_cog(cog)`_.
        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command deletes its messages after 20 seconds.
            :param ctx:
        """
        message = await ctx.send('Unloading...')
        await ctx.message.delete()
        try:
            self.bot.unload_extension(self.check_cog(cog))
        except Exception as exc:
            await message.edit(content=f'An error has occurred: {exc}', delete_after=20)
        else:
            await message.edit(content=f'{self.check_cog(cog)} has been unloaded.', delete_after=20)

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, *, cog: str):
        """This commands reloads the selected cog, as long as that cog is in the `./cogs` folder.

        Args:
            cog (str): The name of the cog to reload. The name is checked with `.check_cog(cog)`_.
        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command deletes its messages after 20 seconds.
            :param ctx:
        """
        message = await ctx.send('Reloading...')
        await ctx.message.delete()
        try:
            self.bot.reload_extension(self.check_cog(cog))
        except Exception as exc:
            await message.edit(content=f'An error has occurred: {exc}', delete_after=20)
        else:
            await message.edit(content=f'{self.check_cog(cog)} has been reloaded.', delete_after=20)

    @commands.command(name='member-list', hidden=True)
    @commands.is_owner()
    async def member_list(self, ctx):
        """This commands gets a list of all members and sends in a text file.

        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command sends a message with the file to download.
        """
        with open('users.txt', 'w') as f:
            async for member in ctx.guild.fetch_members(limit=None):
                print("{},{}".format(member, member.id), file=f,)

        await ctx.send(file=discord.File(r'users.txt'))


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(Dev(bot))
