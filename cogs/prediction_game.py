import json
import os
from datetime import datetime
import statistics
import discord
from discord.ext import commands, tasks

import constants
from cogs.currency import Currency
from cogs.stock_tickers import StockTickers
import logging as log


class PredictionGame(commands.Cog):
    """This is a category of commands for the Xanastrology channel, to automate the prediction game.
    Note: These commands may only be used in Xanastrology!

    The maximum allowed submissions per member is three.
    Submissions will be closed at market open.
    Submissions for the next day will re-open at market close + 20 minutes.

    The prizes are outlined below:
      1st Place: Wins $1000
      2nd Place: Wins $500
      3rd Place: Wins $100

    If the prediction is outside the top 3 winners for the day, but within 1% of close price, a mayo award is won.
      Mayo: Wins $50
    """

    submissions_open = False
    channel_id = constants.ChannelIDs.XANASTROLOGY
    mayo_emoji = "<:mayo:863563385442664478>"

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
        # Close till 4:20:10pm EST to allow time for results to be run, and prediction storage to be cleared
        if '09:30:00' <= current_time <= '16:20:10' and current_day != 5 and current_day != 6:
            self.submissions_open = False
        else:
            self.submissions_open = True

        # Run the results of current pending predictions
        # Need to wait for yahoo to get proper close price so why not 420man:=)
        # Need to set a time range here, since we are in a task with a timer of 5s
        # We only want to run this check_results function once, so set our range check for 6s
        if '16:20:00' <= current_time <= '16:20:06' and current_day != 5 and current_day != 6:
            channel = self.bot.get_channel(self.channel_id)
            await self.check_results(channel)

    @commands.command(
        name='predict',
        help="Make a prediction for $GME\n\n"
             "Params:\n"
             "> prediction: The amount you are predicting\n"
             "> method: The method of your prediction\n\n"
             "Example: !predict 69.69 my smooth brain",
        brief="Predict $GME"
    )
    async def predict(self, ctx, prediction=0.0, *, method):
        user = ctx.author

        # Make sure we are in proper channel, and exit if not
        channel = self.bot.get_channel(self.channel_id)
        if ctx.channel != channel:
            await ctx.send(f"{user.mention} The PredictionGame commands are restricted to {channel.mention} only.")
            return

        await self.create_new_predictions_object()

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        if self.submissions_open:
            res = await self.add_new_prediction_storage(user, prediction, method)
            if not res[0]:
                if res[1] == 1:
                    await channel.send(f"{user.mention} You have already submitted a prediction using that method.")
                    return
                if res[1] == 2:
                    await channel.send(f"{user.mention} You have submitted the maximum allowed predictions.")
                    return

            await channel.send(f'{user.mention} submitted a prediction of {prediction} ({method})')
        else:
            if '16:00:00' <= current_time <= '16:20:10':
                await channel.send(f'{user.mention} Submissions are closed while waiting for results. Try again at 4:20pm EST')
            await channel.send(f'{user.mention} Submissions are closed while the market is open!')

    @commands.command(name='check-results', hidden=True)
    @commands.is_owner()
    async def check_results(self, ctx):

        try:
            # Get the close price for GME
            close_price = StockTickers.get_close_price("gme")
        except Exception as e:
            log.error(f"{e}")
            await ctx.send('There was an error with yfinance api :(\nNo results today, sorry.')
            return

        # Had trouble with using self.get_prediction_storage_data() here so loading json directly instead
        data = json.loads(open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json").read())

        if not data:
            log.info(f"prediction_game check_results no prediction data!")
            await ctx.send('Whoops, looks like there are no predictions :(\nNo results today, sorry.')
            return

        # This will sort the data relative to close price
        sorted_array = sorted(data['predictions'], key=lambda d: abs(close_price - d['prediction']))

        # message will hold the message text to send
        message = "*Top Performers Today:*\n\n"

        place_titles = {
            "msg_title1": "**:first_place: First Place: :first_place:**\n",
            "msg_title2": "**:second_place: Second Place: :second_place:**\n",
            "msg_title3": "**:third_place: Third Place: :third_place:**\n"
        }
        awards = {
            "first": 1000,
            "second": 500,
            "third": 100,
            "mayo": 50
        }

        try:
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

                # Get the discord member
                member = self.bot.get_user(prediction['user'])

                # Make sure the user has data in the leaderboard json storage
                await self.create_new_leaderboard_user(member)

                if index <= 3:
                    # Decrease index if current users' prediction is the same as previous users' prediction
                    # This makes it so that if we start at first place, and the next prediction is the same,
                    # there is a tie, and the second prediction also wins 1st place (etc. for 2nd and 3rd)
                    if prev == prediction['prediction']:
                        index -= 1
                    else:
                        # If no tie is found, append the place title text to the message
                        message += place_titles[f"msg_title{index}"]

                    # Append the members' name/prediction/method to the message
                    message += f"> {member.mention} ${prediction['prediction']} ({prediction['method']}) \n"

                    # Update the members' wallet with prize money
                    await Currency.update_bank(Currency(self.bot), member, awards[list(awards)[index - 1]])

                    # Update the leaderboard
                    await self.update_leaderboard(member, awards[list(awards)[index - 1]], list(awards)[index - 1])

                # Mayo time
                elif index > 3:
                    if close_price - (close_price * 0.01) <= prediction['prediction'] <= close_price + (close_price * 0.01):
                        message += f"\n\n{self.mayo_emoji} = *Outside top 3 but within 1% of close price.*\n\n"
                        message += f"> {member.mention} ${prediction['prediction']} ({prediction['method']}) \n"
                        await Currency.update_bank(Currency(self.bot), member, 50)
                        await self.update_leaderboard(member, awards["mayo"], "mayo")

                index += 1  # Increment the index
                prev = prediction['prediction']  # Set prev prediction for next iteration

        except Exception as e:
            log.error(f"{e}")

        finally:
            now = datetime.now()
            em = discord.Embed(
                title=f"**__:trophy: {str(now.strftime('%A, %B %d %Y'))} just closed. ({round(close_price, 2)}) :trophy:__**",
                color=discord.Color(0xfa43ee)
            )
            em.add_field(name="\u200b", value=message)
            await ctx.send(embed=em)

            # Send updated leaderboard
            await self.leaderboard(ctx)

            # When check_results is done, clear the predictions for today
            await self.clear_prediction_storage()

    @commands.command(
        name="plb",
        help="Display the leaderboard of predictions",
        brief="Prediction leaderboard"
    )
    async def leaderboard(self, ctx, x=10):

        # Make sure we are in proper channel, and exit if not
        channel = self.bot.get_channel(self.channel_id)
        if ctx.channel != channel:
            await ctx.send(f"{ctx.author.mention} The PredictionGame commands are restricted to {channel.mention} only.")
            return

        # Get the leaderboard storage
        users = await self.get_leaderboard_storage_data()
        if not users:
            await ctx.send('No leaderboard yet :(')
            return

        # This will sort the users by prize_total
        top_users = sorted(users, key=lambda k: -users[k]["prize_total"])

        # Strings used to hold each field for the message
        message = ""

        # Used for loop below to track position
        i = 0

        try:
            # Loop through sorted totals
            for user in top_users:

                # Set leaderboard to only show top x
                if i == x:
                    break

                # Some variable to help see whats going on
                member = self.bot.get_user(int(user))
                prize_total = users[user]["prize_total"]
                awards = users[user]["awards"]

                # Append @user and prize total to message string
                message += f"**{i + 1}:**  {member.mention} - ${prize_total}"

                # Loop through awards
                for key in awards.keys():
                    if awards[key] != 0:
                        if key != "mayo":
                            message += f" - :{key}_place:*x{awards[key]}*"
                        else:
                            message += f" - {self.mayo_emoji} *x{awards[key]}*"

                # Add new line to message, and increase position
                message += "\n"
                i += 1

        except Exception as e:
            log.error(f"{e}")

        finally:
            em = discord.Embed(
                title=f"**__:trophy: Leaderboard as of {str(datetime.now().strftime('%A, %B %d %Y'))} :trophy:__**\n",
                color=discord.Color(0xfa43ee)
            )
            em.add_field(name="\u200b", value=message)
            await ctx.send(embed=em)

    @commands.command(
        name="pred-status",
        help="Display the current days' predictions in relation to the current price.",
        brief="Current Predictions"
    )
    async def prediction_status(self, ctx):

        # Make sure we are in proper channel, and exit if not
        channel = self.bot.get_channel(self.channel_id)
        if ctx.channel != channel:
            await ctx.send(f"{ctx.author.mention} The PredictionGame commands are restricted to {channel.mention} only.")
            return

        # Had trouble with using self.get_prediction_storage_data() here so loading json directly instead
        data = json.loads(open(f"{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json").read())

        # If no data send message back, and exit
        if not data:
            await ctx.send('No predictions for today yet :(')
            return

        try:
            # Get the current price for GME
            current_price = StockTickers.get_close_price("gme")
        except Exception as e:
            log.error(f"{e}")
            await ctx.send('There was an error with yfinance api :(')
            return

        # This will sort the data relative to price
        sorted_array = sorted(data['predictions'], key=lambda d: abs(current_price - d['prediction']))

        # Strings used to hold each field for the embed
        message = f"*$GME price is* ${round(current_price, 2)}\n\n"

        i = 0

        try:
            # Loop through sorted totals
            for user in sorted_array:

                # Get % deviation
                deviation = round(abs(user["prediction"] - current_price), 4)

                # Append name and prize_total to strings
                member = self.bot.get_user(user['user'])
                message += f"{i + 1}: {member.mention}  {user['prediction']}  ({user['method']}) ({deviation} %)\n"

                # increase position
                i += 1

        except Exception as e:
            log.error(f"{e}")

        finally:
            em = discord.Embed(
                title=f"**__Current predictions today {str(datetime.now().strftime('%A, %B %d %Y'))}__**",
                color=discord.Color(0xfa43ee)
            )
            em.add_field(name='\u200b', value=message)
            await channel.send(embed=em)

    async def create_new_predictions_object(self):

        data = await self.get_prediction_storage_data()

        if data:
            return False
        else:
            data = {'predictions': []}

        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

        return True

    @staticmethod
    async def get_prediction_storage_data():
        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json', 'r') as f:
            data = json.load(f)

        return data

    @staticmethod
    async def clear_prediction_storage():
        data = {}
        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json', 'w') as f:
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
        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}predictions_today.json', 'w') as f:
            json.dump(data, f, indent=4)

        return [True]

    async def create_new_leaderboard_user(self, user):

        users = await self.get_leaderboard_storage_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["prize_total"] = 0
            users[str(user.id)]["awards"] = {"first": 0, "second": 0, "third": 0, "mayo": 0}

        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}prediction_leaderboards.json', 'w') as f:
            json.dump(users, f, indent=4)

        return True

    @staticmethod
    async def get_leaderboard_storage_data():
        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}prediction_leaderboards.json', 'r') as f:
            users = json.load(f)

        return users

    async def update_leaderboard(self, user, prize_total, award):
        users = await self.get_leaderboard_storage_data()

        users[str(user.id)]["prize_total"] += prize_total

        if award == "first":
            users[str(user.id)]["awards"]["first"] += 1
        elif award == "second":
            users[str(user.id)]["awards"]["second"] += 1
        elif award == "third":
            users[str(user.id)]["awards"]["third"] += 1
        elif award == "mayo":
            users[str(user.id)]["awards"]["mayo"] += 1

        with open(f'{constants.FilePaths.STORAGE_PATH}{os.sep}prediction_leaderboards.json', 'w') as f:
            json.dump(users, f, indent=4)

        return True


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(PredictionGame(bot))
