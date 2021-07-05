import json
from datetime import datetime

import discord
from discord.ext import commands, tasks

from cogs.currency import Currency
from cogs.stock_tickers import StockTickers


class PredictionGame(commands.Cog):
    """This is a cog for the Xanastrology channel, to automate the prediction game.
    Note:
    All cogs inherits from `commands.Cog`_.
    All cogs are classes, so they need self as first argument in their methods.
    All cogs use different decorators for commands and events (see example in dev.py).
    All cogs needs a setup function (see below).

    Documentation:
        https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
    """

    submissions_open = False
    channel_id = 861024504624840744

    def __init__(self, bot):
        self.bot = bot
        self.check_time.start()

    @tasks.loop(seconds=5.0)
    async def check_time(self):
        """This is a background task that loops every 5 seconds.
        The coroutine looped with this task will change set the submission_open bool,
        and update the leaderboard on open/close.

        Documentation:
            https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")  # Current time in 24 hour format HH:MM:SS
        current_day = now.weekday()  # Current day as int (0=monday to 6=sunday)

        # ToDo: Get all days market is closed in here as well (holidays)

        # if the market is open set submissions_open bool to False
        if '09:00:00' <= current_time <= '14:00:00' and current_day != 5 and current_day != 6:
            self.submissions_open = False
        else:
            self.submissions_open = True

        # if market just closed, check results
        # current_time must be between 6 seconds to make sure check_results is only run once
        if '14:01:00' <= current_time <= '14:01:06' and current_day != 5 and current_day != 6:
            channel = self.bot.get_channel(self.channel_id)
            await self.check_results(channel)

    @commands.command(
        name='predict',
        help="Make a prediction for $GME\n\n"
             "Params:\n"
             "> prediction: The amount you are predicting\n"
             "> method: The The method of your prediction\n\n"
             "Example: !predict 69.69 my smooth brain",
        brief="Predict $GME"
    )
    async def predict(self, ctx, prediction=0.0, *, method):
        await self.create_new_predictions_object()
        user = ctx.author

        if self.submissions_open:
            res = await self.add_new_prediction_storage(user, prediction, method)
            if not res[0]:
                if res[1] == 1:
                    await ctx.send(f"{user.mention} You have already submitted a prediction using that method.")
                    return
                if res[1] == 2:
                    await ctx.send(f"{user.mention} You have submitted the maximum allowed predictions.")
                    return

            await ctx.send(f'{user.mention} submitted a prediction of {prediction} ({method})')
        else:
            await ctx.send(f'{user.mention} Submissions are closed while the market is open!')

    @commands.command(name='check-results', hidden=True)
    @commands.is_owner()
    async def check_results(self, ctx, x=3):

        # Get the close price for GME
        close_price = StockTickers.get_close_price("gme")

        # Had trouble with using self.get_prediction_storage_data() here so loading json directly instead
        data = json.loads(open("storage/predictions_today.json").read())

        # This will sort the data relative to close price
        sorted_array = sorted(data['predictions'], key=lambda d: abs(close_price - d['prediction']))

        # Put the sorted data back into json object and write file
        # Do we even need to do this ??? data should be cleared at end anyways ...
        data['predictions'] = sorted_array
        with open('storage/predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

        # Start creating the embed message
        em = discord.Embed(
            title=f":trophy: {str(datetime.now().strftime('%A, %B %d %Y'))} just closed. :trophy:\n"
            f"      $GME closing price is ${round(close_price, 2)}",
            description=f"__Top {x} Performers Today__",
            color=discord.Color(0xfa43ee)
        )

        # Some text for the embeds that is reused
        first_place = f"**:first_place: First Place:**"
        second_place = f"**:second_place: Second Place:**"
        third_place = f"**:third_place: Third Place:**"

        # Index used to store what place we are on in the loop
        # Also by design, since the data is already sorted with first place at the beginning,
        # this will keep track of what "place" we are on (first place, second, third ...)
        index = 1

        # To account for any scenarios where there is a tie (same prediction)
        # At the end of each loop we store the previous users' prediction in this variable
        # We can then compare this to the next users' prediction to see if they match
        prev = None

        # Loop through all predictions in the sorted array
        # This means the loop is starting with the first place prediction
        for prediction in sorted_array:

            # Store variables for the users' submission
            id_ = prediction['user']
            pred_ = prediction['prediction']
            meth_ = prediction['method']
            member = self.bot.get_user(id_)

            # Make sure the user has data in the leaderboard json storage
            await self.create_new_leaderboard_user(member)

            # These are used to store the embed field as we progress
            em_name = None
            em_value = None

            # Decrease index if current users' prediction is the same as previous users' prediction
            # This makes it so that if we start at first place, and the next prediction is the same,
            # there is a tie, and the second prediction also wins 1st place (etc. for 2nd and 3rd)
            if prev == pred_:
                index -= 1

            # update first place
            if index == 1:

                if pred_ == prev:
                    # Due to the way embeds work, if this is true then we have already created the field for 1st place.
                    # To not create a new field, we can search for it here, and append to the value
                    embed_dict = em.to_dict()
                    for field in embed_dict["fields"]:
                        if field["name"] == first_place:
                            field["value"] += f"> {member.mention} {pred_} ({meth_}) \n"
                else:
                    # Create first place name and value
                    em_name = first_place
                    em_value = f"> {member.mention} {pred_} ({meth_}) \n"

                # Update the leaderboard and bank with prize money
                await self.update_leaderboard(member, 1000, 1, 0, 0, 0)
                await Currency.update_bank(Currency(self.bot), member, 1000)

            # update second place
            if index == 2:
                if pred_ == prev:
                    embed_dict = em.to_dict()
                    for field in embed_dict["fields"]:
                        if field["name"] == second_place:
                            field["value"] += f"> {member.mention} {pred_} ({meth_}) \n"
                else:
                    em_name = second_place
                    em_value = f"> {member.mention} {pred_} ({meth_}) \n"
                await self.update_leaderboard(member, 500, 0, 1, 0, 0)
                await Currency.update_bank(Currency(self.bot), member, 500)

            # update third place
            if index == 3:
                if pred_ == prev:
                    embed_dict = em.to_dict()
                    for field in embed_dict["fields"]:
                        if field["name"] == third_place:
                            field["value"] += f"> {member.mention} {pred_} ({meth_}) \n"
                else:
                    em_name = third_place
                    em_value = f"> {member.mention} {pred_} ({meth_}) \n"
                await self.update_leaderboard(member, 100, 0, 0, 1, 0)
                await Currency.update_bank(Currency(self.bot), member, 100)

            # We only want to display the top 3 so stop break if index > 3
            if index > x:
                break
            else:
                index += 1  # Increment the index
                prev = pred_  # Set prev prediction for next iteration

                # Create embed field from name and value set from the loop
                if em_name is not None and em_value is not None:
                    em.add_field(
                        name=em_name,
                        value=em_value,
                        inline=False
                    )

        # Loop done, send the embed
        channel = self.bot.get_channel(self.channel_id)
        await channel.send(embed=em)

        # When check_results is done, clear the predictions for today
        await self.clear_prediction_storage()

        # Finished, send the leaderboard command
        await self.leaderboard(channel)

    @commands.command(
        name="plb",
        help="Display the leaderboard of predictions",
        brief="Prediction leaderboard"
    )
    async def leaderboard(self, ctx, x=10):

        # Get the leaderboard storage
        users = await self.get_leaderboard_storage_data()

        # This will sort the users by prize_total
        top_users = sorted(users, key=lambda k: -users[k]["prize_total"])

        # Strings used to hold each field for the embed
        names = ''
        prize_totals = ''
        awards = ''

        # Used for loop below to track position
        i = 0

        # Note: too lazy to implement ties, i think its fine for now

        # Loop through sorted totals
        for user in top_users:

            # Set leaderboard to only show top x
            if i == x:
                break

            # Set some variables for the user
            member = self.bot.get_user(int(user))
            name = member.name
            pt = users[user]["prize_total"]
            num_first = users[user]["awards"][0]["first"]
            num_second = users[user]["awards"][0]["second"]
            num_third = users[user]["awards"][0]["third"]
            num_mayo = users[user]["awards"][0]["mayo"]

            # Append name and prize_total to strings
            names += f"{i + 1}: {name}\n"
            prize_totals += f"{pt}\n"

            # Yes this looks ridiculous but i could not think of another way to do this
            # What i want is to only show awards if the user has them
            # This will append the users' awards to the awards string
            if num_first > 0 and num_second > 0 and num_third > 0 and num_mayo > 0:  # 1111
                awards += f"x{num_first}:first_place:" \
                    f"x{num_second}:second_place:" \
                    f"x{num_third}:third_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first > 0 and num_second > 0 and num_third > 0 and num_mayo == 0:  # 1110
                awards += f"x{num_first}:first_place:" \
                    f"x{num_second}:second_place:" \
                    f"x{num_third}:third_place:\n"
            elif num_first > 0 and num_second > 0 and num_third == 0 and num_mayo > 0:  # 1101
                awards += f"x{num_first}:first_place:" \
                    f"x{num_second}:second_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first > 0 and num_second > 0 and num_third == 0 and num_mayo == 0:  # 1100
                awards += f"x{num_first}:first_place:" \
                    f"x{num_second}:second_place:\n"
            elif num_first > 0 and num_second == 0 and num_third > 0 and num_mayo > 0:  # 1011
                awards += f"x{num_first}:first_place:" \
                    f"x{num_third}:third_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first > 0 and num_second == 0 and num_third > 0 and num_mayo == 0:  # 1010
                awards += f"x{num_first}:first_place:" \
                    f"x{num_third}:third_place:\n"
            elif num_first > 0 and num_second == 0 and num_third == 0 and num_mayo > 0:  # 1001
                awards += f"x{num_first}:first_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first > 0 and num_second == 0 and num_third == 0 and num_mayo == 0:  # 1000
                awards += f"x{num_first}:first_place:\n"
            elif num_first == 0 and num_second > 0 and num_third > 0 and num_mayo > 0:  # 0111
                awards += f"x{num_second}:second_place:" \
                    f"x{num_third}:third_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first == 0 and num_second > 0 and num_third > 0 and num_mayo == 0:  # 0110
                awards += f"x{num_second}:second_place:" \
                    f"x{num_third}:third_place:\n"
            elif num_first == 0 and num_second > 0 and num_third == 0 and num_mayo > 0:  # 0101
                awards += f"x{num_second}:second_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first == 0 and num_second > 0 and num_third == 0 and num_mayo == 0:  # 0100
                awards += f"x{num_second}:second_place:\n"
            elif num_first == 0 and num_second == 0 and num_third > 0 and num_mayo > 0:  # 0011
                awards += f"x{num_third}:third_place:" \
                    f"x{num_mayo}:mayo:\n"
            elif num_first == 0 and num_second == 0 and num_third > 0 and num_mayo == 0:  # 0010
                awards += f"x{num_third}:third_place:\n"
            elif num_first == 0 and num_second == 0 and num_third == 0 and num_mayo > 0:  # 0001
                awards += f"x{num_mayo}:mayo:\n"

            # Increase position
            i += 1

        # Loop finished, start creating the embed
        em = discord.Embed(
            title=f":trophy: Leaderboard as of {str(datetime.now().strftime('%A, %B %d %Y'))} :trophy:\n",
            # description=f"__Top {x} Performers Today__",
            color=discord.Color(0xfa43ee),
            dynamic=True
        )

        # Add the fields with strings obtained from loop (this way it shows up like a table with inline=True)
        # Embeds are weird as fuck, and only allow 3 inline fields
        em.add_field(name='Top 10', value=names, inline=True)
        em.add_field(name='Total', value=prize_totals, inline=True)
        em.add_field(name='Awards', value=awards, inline=True)

        # Send the embed
        channel = self.bot.get_channel(self.channel_id)
        await channel.send(embed=em)

    async def create_new_predictions_object(self):

        data = await self.get_prediction_storage_data()

        if data:
            return False
        else:
            data = {'predictions': []}

        with open('storage/predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

        return True

    @staticmethod
    async def get_prediction_storage_data():
        with open('storage/predictions_today.json', 'r') as f:
            data = json.load(f)

        return data

    @staticmethod
    async def clear_prediction_storage():
        data = {}
        with open('storage/predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def add_new_prediction_storage(self, user, prediction, method):
        data = await self.get_prediction_storage_data()

        count = 0
        for item in data["predictions"]:
            # print(item)
            if item["user"] == user.id:
                count += 1
                if item["method"] == method:
                    return [False, 1]

        # print(count)
        if count >= 3:
            return [False, 2]

        data['predictions'].append({
            "user": user.id,
            "prediction": prediction,
            "method": method
        })
        with open('storage/predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

        return [True]

    async def create_new_leaderboard_user(self, user):

        users = await self.get_leaderboard_storage_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["prize_total"] = 0
            users[str(user.id)]["awards"] = [{"first": 0, "second": 0, "third": 0, "mayo": 0}]

        with open('storage/prediction_leaderboards.json', 'w') as f:
            json.dump(users, f, indent=4)

        return True

    @staticmethod
    async def get_leaderboard_storage_data():
        with open('storage/prediction_leaderboards.json', 'r') as f:
            users = json.load(f)

        return users

    async def update_leaderboard(self, user, prize_total, first, second, third, mayo):
        users = await self.get_leaderboard_storage_data()

        users[str(user.id)]["prize_total"] += prize_total
        users[str(user.id)]["awards"][0]["first"] += first
        users[str(user.id)]["awards"][0]["second"] += second
        users[str(user.id)]["awards"][0]["third"] += third
        users[str(user.id)]["awards"][0]["mayo"] += mayo

        with open('storage/prediction_leaderboards.json', 'w') as f:
            json.dump(users, f, indent=4)

        return True


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(PredictionGame(bot))
