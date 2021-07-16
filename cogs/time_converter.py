from util.messages import ErrorMessage, WarnMessage, Message
from time import strftime
import pytz
from discord.ext import commands
from dateutil import parser
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
        self.timezones = constants.Timezones.identifier
  
    def getTimezoneName(self, identifier:str):
        return self.timezones[identifier][0]

    def getTimezoneAbbreviation(self, identifier:str):
        return self.timezones[identifier][1]

    def resolveZone(self, identifier):
        identifier = identifier.upper()
        label = self.getTimezoneName(identifier)

        return label

    def getUserTimezone(self, user: discord.Member):
        label = find(lambda role: "Time" in role.name, user.roles)

        return label

    def getUserTimezoneIdentifier(self, user: discord.Member):
        label = self.getUserTimezone(user)

        for id in self.timezones:
            timezone = self.getTimezoneName(id)
            if str(label) == str(timezone):
                identifier = id

        return identifier

    def convertTime(self, time, identifier):
        abbreviation = self.getTimezoneAbbreviation(identifier)
        timezone = pytz.timezone(abbreviation)
        format = "%H:%M  (%d.%m.%y)"
        converted = time.astimezone(timezone)

        return converted.strftime(format)

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
             {nl.join([str(a) + ' - ' + constants.Timezones.identifier[a][0] for a in constants.Timezones.identifier])} \n\n
             """,
        brief="assign timezone")
    async def tz(self, ctx, identifier:str=None):
        """Assigns roles based on timezones. The timezone is predefined in the constants class

            Args:
            identifier: abbreviation for the timezone

            Note:
            not specifying the identifier will return the current timezone (!tz)

        """
        user = ctx.author
        response = Message(f"{user.name}").new()

        try: 
            if identifier is None:
                zone = self.getUserTimezone(user)
                response.description = f'Your timezone is **{zone}**'
            else:
                label = self.resolveZone(identifier)
                role = get(user.guild.roles, name=f"{label}")
                existingTimeRole = self.getUserTimezone(user)
                guild = ctx.guild

                if role is None:
                    role = await guild.create_role(name=f"{label}")

                if not existingTimeRole is None:
                    await user.remove_roles(existingTimeRole)
                    response.description = f"Changed timezone to **{label}**"
                else:
                    response.description = f"Welcome to the zone! Your new timezone is **{label}**"

                await user.add_roles(role)        
        except Exception as e:
            response = ErrorMessage("Invalid command", f"The code for the timzone is invalid. Use `!help tz` for a list of all available timezones").new()
            response.add_field(name="Error message:", value=e, inline=False)
        finally:
            await ctx.send(embed=response, delete_after=60)


    @tz.group(aliases=["conv","-c"], pass_context=True)
    async def convert(self, ctx, time:str, member: discord.Member):
        """ Converts a time into the timezone of target member (experimental)
            
            Params:
            `time` - a timestring or 'now' (literally)
            `member` - member into whoms timezone you want to convert to

            Examples:
            `!tz -c now @OrlandoOom` -> gets the current time of @OrlandoOom
            `!tz -c 7:00 @OrlandoOom` -> converts 7:00 into @OrlandoOom's timezone

            Note:
            * passing 'now' will take a datetime.now() timestamp
            * AM and PM are not implemented yet        
         """
        try:
            parsedTime = datetime.now() if time.lower() == "now" else parser.parse(time)

            identifier = self.getUserTimezoneIdentifier(member)
            await ctx.send(f"{self.convertTime(parsedTime, identifier)}")
        except Exception as e:
            errMessage = ErrorMessage("Could not parse time", f"{e}").new()
            await ctx.send(embed=errMessage)

    @tz.command(aliases=["-o"], help="Get the timezone of target user")
    async def of(self, ctx, member: discord.Member):
        zone = self.getUserTimezone(member)
        await ctx.message.reply(content=f"{member.mention}'s timezone: {self.nl}{self.nl} **{zone}**")

    @tz.command(aliases=["all", "-w"], help="Show every users timetag")
    async def world(self, ctx):
        """
        Shows a clustered board of all users and their timezones. Only implies users that have an assigned timezone
        """
        timeboard = discord.Embed(title="Timezones", color=discord.Color.green())
        guild = ctx.guild
        
        for tz in self.timezones:
            zone = self.getTimezoneName(tz)
            memberWithZone = get(guild.roles, name=f"{zone}")
            embedContent = ""

            if not memberWithZone is None:
                for member in memberWithZone.members:
                    embedContent = f"{embedContent} > {member.name} {self.nl}"

                timeboard.add_field(name=f"{zone}  :clock1:  {self.convertTime(datetime.now(), tz)}", value=f"{embedContent}", inline=False)

        await ctx.send(embed=timeboard)

def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(TimeConverter(bot))
