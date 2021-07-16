import json
import random
import os
import constants
import discord
from discord.ext import commands

mainshop = [
    {"name": "Jar of Mayo", "price": 100, "description": "Yes, mayo."},
    {"name": "Bananas", "price": 100, "description": "Yummy"},
    {"name": "Diamond", "price": 10000, "description": "shiny"},
    {"name": "Lambo", "price": 99999, "description": "Lambo go VRRRROOM"}
]


class Currency(commands.Cog):
    """This is a category of commands for currency.
    """

    channel_id = constants.ChannelIDs.VEGAS

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="$bal",
        help="Shows the balance in your bank account.",
        brief="Bank account balance"
    )
    async def bal(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author

        users = await self.get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        em = discord.Embed(title=f"{user.name}'s Balance", color=discord.Color.red())
        em.add_field(name="\u200b", value=f"${wallet_amt}")
        await ctx.send(embed=em)

    @commands.command(
        name='$beg',
        help="Beg to get some money. Can only be used once per day",
        brief="Beg for $$"
    )
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def beg(self, ctx):

        await self.open_account(ctx.author)
        user = ctx.author

        users = await self.get_bank_data()

        earnings = random.randrange(101)

        await ctx.send(f'{ctx.author.mention} Got ${earnings}!!')

        users[str(user.id)]["wallet"] += earnings

        with open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json", 'w') as f:
            json.dump(users, f, indent=4)

    @commands.command(
        name="$send",
        help="Send money to another user.\n\n"
             "Params:\n"
             "> member: The member to send money to.\n"
             "> amount: The amount to send\n\n"
             "Example: !$send @sudoshu 69",
        brief="Send money"
    )
    async def send(self, ctx, member: discord.Member, amount=None):
        await self.open_account(ctx.author)
        await self.open_account(member)
        if amount is None:
            await ctx.send(f"{ctx.author.mention} Please enter the amount")
            return

        bal = await self.update_bank(ctx.author)
        if amount == 'all':
            amount = bal

        amount = int(amount)

        if amount > bal:
            await ctx.send(f'{ctx.author.mention} You do not have sufficient balance')
            return
        if amount < 0:
            await ctx.send(f'{ctx.author.mention} Amount must be positive!')
            return

        await self.update_bank(ctx.author, -1 * amount)
        await self.update_bank(member, amount)
        await ctx.send(f'{ctx.author.mention} gave {member.mention} ${amount}')

    @commands.command(
        name="$slots",
        help="Play slots for a chance to win money!\n\n"
             "Params:\n"
             "> amount: The amount you wish to gamble.\n"
             "Example: !$slots 69",
        brief="Gamble slots"
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def slots(self, ctx, amount=None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send(f"{ctx.author.mention} Please enter the amount")
            return

        bal = await self.update_bank(ctx.author)

        amount = int(amount)

        if amount > bal:
            await ctx.send(f'{ctx.author.mention} You do not have sufficient balance')
            return
        if amount < 0:
            await ctx.send(f'{ctx.author.mention} Amount must be positive!')
            return

        slots = ['bus', 'train', 'horse', 'tiger', 'monkey', 'cow']
        slot1 = slots[random.randint(0, 5)]
        slot2 = slots[random.randint(0, 5)]
        slot3 = slots[random.randint(0, 5)]

        slot_output = '| :{}: | :{}: | :{}: |\n'.format(slot1, slot2, slot3)

        ok = discord.Embed(title="Slots Machine", color=discord.Color(0xFFEC))
        ok.add_field(name=f"{format(slot_output)}\nWon", value=f'{ctx.author.mention} You won ${2 * amount}')

        won = discord.Embed(title="Slots Machine", color=discord.Color(0xFFEC))
        won.add_field(name=f"{format(slot_output)}\nWon", value=f'{ctx.author.mention} You won ${4 * amount}')

        lost = discord.Embed(title="Slots Machine", color=discord.Color(0xFFEC))
        lost.add_field(name=f"{format(slot_output)}\nLost", value=f'{ctx.author.mention} You lost ${1 * amount}')

        if slot1 == slot2 == slot3:
            await self.update_bank(ctx.author, 4 * amount)
            await ctx.send(embed=won)
            return

        if slot1 == slot2 or slot1 == slot3 or slot2 == slot3:
            await self.update_bank(ctx.author, 2 * amount)
            await ctx.send(embed=ok)
            return

        else:
            await self.update_bank(ctx.author, -1 * amount)
            await ctx.send(embed=lost)
            return

    @commands.command(
        name="$yolo",
        help="YOLO your whole bank account into slots!",
        brief="YOLO"
    )
    async def yolo(self, ctx):
        await self.open_account(ctx.author)
        bal = await self.update_bank(ctx.author)

        bal = int(bal)

        if bal == 0:
            await ctx.send(f'{ctx.author.mention} You are broke!')
            return

        await self.slots(ctx, bal)

    @commands.command(
        name="$shop",
        help="Display all items for sale in the shop",
        brief="Show shop"
    )
    async def shop(self, ctx):
        em = discord.Embed(title="Shop")

        for item in mainshop:
            name = item["name"]
            price = item["price"]
            desc = item["description"]
            em.add_field(name=name, value=f"${price} | {desc}")

        await ctx.send(embed=em)

    @commands.command(
        name="$buy",
        help="Buy an item from the shop.\n\n"
             "Params:\n"
             "> amount: How many of the item you wish to buy.\n"
             "> item: The you wish to buy.\n\n"
             "Examples: \n"
             "> !$buy 2 lambo",
        brief="Buy item"
    )
    async def buy(self, ctx, amount=1, *, item):
        await self.open_account(ctx.author)

        res = await self.buy_this(ctx.author, item, amount)

        if not res[0]:
            if res[1] == 1:
                await ctx.send(f"{ctx.author.mention} Something went wrong and a price could not be found.")
                return
            if res[1] == 2:
                await ctx.send(f"{ctx.author.mention} That Object isn't there!")
                return
            if res[1] == 3:
                await ctx.send(f"{ctx.author.mention} You don't have enough money to buy {amount} {item}")
                return

        await ctx.send(f"{ctx.author.mention} You just bought {amount} {item}")

    @commands.command(
        name="$inv",
        help="Display all items you own",
        brief="Show inventory"
    )
    async def inv(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        try:
            inv = users[str(user.id)]["inventory"]
        except:
            inv = []

        em = discord.Embed(title=f"{ctx.author.name}'s Inventory")
        for item in inv:
            name = item["item"]
            amount = item["amount"]

            em.add_field(name=name, value=amount)

        await ctx.send(embed=em)

    async def buy_this(self, user, item_name, amount):
        item_name = item_name.lower()
        name_ = None
        price = None
        for item in mainshop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                price = item["price"]
                break

        if price is None:
            return [False, 1]

        if name_ is None:
            return [False, 2]

        cost = price * amount

        users = await self.get_bank_data()

        bal = await self.update_bank(user)

        if bal < cost:
            return [False, 3]

        try:
            index = 0
            t = None
            for thing in users[str(user.id)]["inventory"]:
                n = thing["item"]
                if n == item_name:
                    old_amt = thing["amount"]
                    new_amt = old_amt + amount
                    users[str(user.id)]["inventory"][index]["amount"] = new_amt
                    t = 1
                    break
                index += 1
            if t is None:
                obj = {"item": item_name, "amount": amount}
                users[str(user.id)]["inventory"].append(obj)
        except:
            obj = {"item": item_name, "amount": amount}
            users[str(user.id)]["inventory"] = [obj]

        with open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json", "w") as f:
            json.dump(users, f, indent=4)

        await self.update_bank(user, cost * -1)

        return [True, "Worked"]

    @commands.command(
        name="$sell",
        help="Sell an item from your inventory for money.\n\n"
             "Params:\n"
             "> amount: The amount of items you wish to sell.\n"
             "> item: The item you wish to sell.\n\n"
             "Examples: \n"
             "> !$sell 2 lambo",
        brief="Sell item"
    )
    async def sell(self, ctx, amount=1, *, item):
        await self.open_account(ctx.author)

        res = await self.sell_this(ctx.author, item, amount)

        if not res[0]:
            if res[1] == 1:
                await ctx.send(f"{ctx.author.mention} That Object isn't there!")
                return
            if res[1] == 2:
                await ctx.send(f"{ctx.author.mention} You don't have {amount} {item} in your inventory.")
                return
            if res[1] == 3:
                await ctx.send(f"{ctx.author.mention} You don't have {item} in your inventory.")
                return

        await ctx.send(f"{ctx.author.mention} You just sold {amount} {item}.")

    async def sell_this(self, user, item_name, amount, price=None):
        item_name = item_name.lower()
        name_ = None
        for item in mainshop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                if price is None:
                    price = 0.7 * item["price"]
                break

        if name_ is None:
            return [False, 1]

        cost = price * amount

        users = await self.get_bank_data()

        await self.update_bank(user)

        try:
            index = 0
            t = None
            for thing in users[str(user.id)]["inventory"]:
                n = thing["item"]
                if n == item_name:
                    old_amt = thing["amount"]
                    new_amt = old_amt - amount
                    if new_amt < 0:
                        return [False, 2]
                    users[str(user.id)]["inventory"][index]["amount"] = new_amt
                    t = 1
                    break
                index += 1
            if t is None:
                return [False, 3]
        except discord.ext.commands.CommandError:
            return [False, 3]

        with open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json", "w") as f:
            json.dump(users, f, indent=4)

        await self.update_bank(user, cost)

        return [True, "Worked"]

    @commands.command(
        name="$lead",
        help="Display the leaderboard of most wealthy users",
        brief="Show money leaderboard"
    )
    async def leaderboard(self, ctx, x=10):
        users = await self.get_bank_data()
        leader_board = {}
        total = []
        for user in users:
            name = int(user)
            total_amount = users[user]["wallet"]
            leader_board[total_amount] = name
            total.append(total_amount)

        total = sorted(total, reverse=True)

        em = discord.Embed(title=f"Top {x} Richest People",
                           description="This is decided on the basis of money in the bank",
                           color=discord.Color(0xfa43ee))
        index = 1
        for amt in total:
            id_ = leader_board[amt]

            member = self.bot.get_user(id_)
            name = member.name
            em.add_field(name=f"{index}. {member.mention}", value=f"{amt}", inline=False)
            if index == x:
                break
            else:
                index += 1

        await ctx.send(embed=em)

    async def open_account(self, user: discord.Member):

        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 0

        with open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json", 'w') as f:
            json.dump(users, f, indent=4)

        return True

    @staticmethod
    async def get_bank_data():
        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json', 'r') as f:
            users = json.load(f)

        return users

    async def update_bank(self, user: discord.Member, change=0):
        await self.open_account(user)

        users = await self.get_bank_data()

        users[str(user.id)]['wallet'] += change

        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}bank.json', 'w') as f:
            json.dump(users, f, indent=4)
        bal = users[str(user.id)]['wallet']
        return bal


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(Currency(bot))
