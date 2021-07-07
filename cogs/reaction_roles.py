import discord
from discord.ext import commands
from discord.utils import get

import constants


class ReactionRoles(commands.Cog):
    """This is a cog that adds a role when a user reacts to a message.
    Note:
    All cogs inherits from `commands.Cog`_.
    All cogs are classes, so they need self as first argument in their methods.
    All cogs use different decorators for commands and events (see example in dev.py).
    All cogs needs a setup function (see below).

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """This command give the user a role when reacting to the welcome message.
        That will then unlock the unapproved-users channel, where a moderator will need to verify the user manually.

        :param payload:

        """
        # Get the message id of the message that the user reacted to.
        message_id = payload.message_id

        # Get the message id of the message we want the user to react to.
        actual_message_id = constants.MessageIDs.RULES_MSGID

        # Compare that id's match, and if true continue to give the role.
        if message_id == actual_message_id:
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


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(ReactionRoles(bot))
