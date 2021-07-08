from itertools import tee
import time
from discord import embeds
from discord import utils
from discord.embeds import Embed
from discord.ext import commands
from time import gmtime, strftime
from dateutil import tz
from datetime import date, datetime
from discord.utils import get, find
import discord

import constants


class TimeConverter(commands.Cog):
    """This is a cog for handling time conversions
    Note:
        All cogs inherits from `commands.Cog`_.
        All cogs are classes.
        All cogs needs a setup function (see below).

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
    """
    nl = "\n"

    def __init__(self, bot):
        self.bot = bot

    def getTimeZone(self):
        return datetime.now(tz.tzlocal())

    def getTimeZoneName(self, tz: datetime):
        return tz.tzname()

    def resolveZone(self, identifier):
        identifier = identifier.upper()
        timezones = constants.Timezones.identifier
        label = timezones[identifier]

        return label

    def getUserTimezone(self, user: discord.Member):
        label = find(lambda role: "Time" in role.name, user.roles)

        return label

    @commands.group(
        pass_context=True, 
        invoke_without_command=True,
        description="Assigns a timezone as role. If identifier is left empty prints out your current zone instead", 
        help=f"""
             **Params:**\n
             > (optional) identifier: Abbreviation of your timezone. Choose one of the predefined or leave empty\n\n
             **Examples:** \n 
             `!tz` -> Your currently assigned timezone
             `!tz cet` -> assigns Central European Time  
             `!tz est` -> assigns Eastern Standard Time \n\n
             **Available timezones:**\n
             {nl.join([str(a) + ' - ' + str(constants.Timezones.identifier[a]) for a in constants.Timezones.identifier])} \n\n
             """,
        brief="assign timezone")
    async def tz(self, ctx, identifier:str=None):
        """Assigns roles based on timezones. The timezone is predefined in the constants class

            Args:
            identifier: abbreviation for the timezone

            Note:
            not specifying the identifier will return the current timezone (!tz)
            will assign Central European Time (!tz cet)

        """
        response = discord.Embed(color=discord.Color.blue())
        user = ctx.author
           
        try: 
            if identifier is None:
                zone = self.getUserTimezone(user)
                #await ctx.send(f'Your timezone is **{zone}**', delete_after=60)
                response.description = f'Your timezone is **{zone}**'
            else:
                member = ctx.author
                label = self.resolveZone(identifier)
                role = get(member.guild.roles, name=f"{label}")
                existingTimeRole = self.getUserTimezone(user)
                guild = ctx.guild

                if role is None:
                    role = await guild.create_role(name=f"{label}")

                if not existingTimeRole is None:
                    await member.remove_roles(existingTimeRole)
                    response.description = f"Changed timezone to **{label}**"
                else:
                    response.description = f"Welcome to the zone! Your new timezone is **{label}**"

                await member.add_roles(role)        
        except Exception as e:
            response.color = discord.Color.red()
            response.add_field(name="Invalid command", value=f'The code for the timzone is invalid. Use !help tz for a list of all available timezones', inline=False)
            response.add_field(name="Error", value=e)
        finally:
            await ctx.send(embed=response, delete_after=60)


    @tz.command()
    async def convert(self, ctx, *, t:str):
        """ Dummy command for now (converts a timestamp into your timezone). Will be a subcommand of !tz
        
         """
        pass


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(TimeConverter(bot))
