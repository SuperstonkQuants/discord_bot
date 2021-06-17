import discord
from discord.ext import commands
from discord.utils import get


class ReactionRoles(commands.Cog):
    """This is a cog for giving roles to users for performing a reaction
    Note:
        All cogs inherits from `commands.Cog`_.
        All cogs are classes.
        All cogs needs a setup function (see below).

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """This command give the user a role when reacting to the welcome message.
        That role will then unlock the get-roles channel, where another reaction can get the user other roles.

        :param payload:
        Note:
            This command can be used only from the bot owner.
            This command is hidden from the help menu.
            This command deletes its messages after 20 seconds.


        """

        message_id = payload.message_id

        # For welcome channel, reaction adds role to access get-roles channel
        if message_id == 854535314436521984:
            guild_id = payload.guild_id
            guild = self.bot.get_guild(guild_id)
            role = get(payload.member.guild.roles, name='Not Verified')

            if role is not None:
                member = get(guild.members, id=payload.user_id)
                if member is not None:
                    await payload.member.add_roles(role)
                    print(f"Added role to {member}")
                else:
                    print("User not found . . .")
            else:
                print("Role not found . . .")

        # For get-roles channel
        if message_id == 854851285152432128:
            guild_id = payload.guild_id
            guild = self.bot.get_guild(guild_id)
            role = get(payload.member.guild.roles, name='Computer Ape')

            if role is not None:
                member = get(guild.members, id=payload.user_id)
                if member is not None:
                    await payload.member.add_roles(role)
                    print(f"Added role to {member}")
                else:
                    print("User not found . . .")
            else:
                print("Role not found . . .")

    # Future use remove roles functions
    # @commands.Cog.listener()
    # async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(ReactionRoles(bot))
