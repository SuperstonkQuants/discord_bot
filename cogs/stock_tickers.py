import io
import os

from yfinance import shared

import constants
import discord
import matplotlib.pyplot as plt
import yfinance as yf
import logging as log
from discord.ext import commands


class StockTickers(commands.Cog):
    """This is a cog that gets info about a stock ticker.

    """

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_close_price(symbol):
        ticker = yf.Ticker(symbol)
        data_today = ticker.history(threads=False, period='1d')
        if data_today.empty:
            return False
        else:
            return data_today['Close'][0]

    @staticmethod
    def get_open_price(symbol):
        ticker = yf.Ticker(symbol)
        data_today = ticker.history(period='1d')
        if data_today.empty:
            return False
        else:
            return data_today['Open'][0]

    @commands.command(
        name="ticker-close",
        help="Display the close price of a stock",
        brief="Stock close"
    )
    async def get_close(self, ctx, symbol):
        price = self.get_close_price(symbol)
        if not price:
            await ctx.send(f"There was an error with the yfinance api :(\nError: {shared._ERRORS}")
            log.error(f"Error: {shared._ERRORS}")
            return
        await ctx.send(f'${symbol} Closing price today is ${price}')

    @commands.command(
        name="ticker-open",
        help="Display the open price of a stock",
        brief="Stock open"
    )
    async def get_open(self, ctx, symbol):
        price = self.get_open_price(symbol)
        if not price:
            await ctx.send(f"There was an error with the yfinance api :(\nError: {shared._ERRORS}")
            log.error(f"Error: {shared._ERRORS}")
            return
        await ctx.send(f'{symbol} Opening price today is ${price}')

    @commands.command(
        name='graph',
        aliases=['gr'],
        help="Display the graph for a stock\n\n"
             "Params:\n"
             "> symbol: The symbol for the stock\n"
             "> period: The time period for the graph\n"
             "> interval: The time interval for the graph\n\n"
             "Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max\n"
             "Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo\n\n"
             "Example: !graph gme 5d",
        brief="Stock graph"
    )
    async def graph(self, ctx, symbol, period="1d", interval="1m"):
        # https://pypi.org/project/yfinance/
        try:
            data = yf.download(  # or pdr.get_data_yahoo(...
                # tickers list or string as well
                tickers=symbol,

                # use "period" instead of start/end
                # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
                # (optional, default is '1mo')
                period=period,

                # fetch data by interval (including intraday if period < 60 days)
                # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                # (optional, default is '1d')
                interval=interval,

                # group by ticker (to access via data['SPY'])
                # (optional, default is 'column')
                group_by='column',

                # adjust all OHLC automatically
                # (optional, default is False)
                auto_adjust=True,

                # download pre/post regular market hours data
                # (optional, default is False)
                prepost=True,

                # use threads for mass downloading? (True/False/Integer)
                # (optional, default is True)
                threads=True,

                # proxy URL scheme use use when downloading?
                # (optional, default is None)
                proxy=None
            )
            if data.empty:
                raise Exception

        except Exception as e:
            await ctx.send(f"There was an error with the yfinance api :(\nError: {shared._ERRORS}")
            log.error(f"Error: {e}\n{shared._ERRORS}")
            return

        link = f'https://finance.yahoo.com/quote/{symbol}?p={symbol}&.tsrc=fin-srch'
        colour = 0x00b2ff
        embed = discord.Embed(
            title=f"${symbol.upper()} - {period} - {interval}",
            colour=colour,
            url=link
        )

        plt.clf()
        plt.style.use('dark_background')
        data['Close'].plot(color='#47a0ff')
        plt.xlabel("Date")
        plt.ylabel("Close")
        plt.title(f"${symbol.upper()} Price data")
        plt.savefig(f"{constants.FilePaths.IMAGES_PATH}{os.sep}graph.png", transparent=True)

        with open(f"{constants.FilePaths.IMAGES_PATH}{os.sep}graph.png", 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')
        embed.set_image(url=f'attachment://graph.png')

        try:
            await ctx.send(file=image, embed=embed)
        except Exception as e:
            await ctx.send(f"There was an error sending the graph :(\nError: {e}")
            log.error(f"{e}")
            return

    @commands.command(
        name='ticker-options',
        help="Display the options chain for a stock\n\n"
             "Params:\n"
             "> symbol: The symbol for the stock\n\n"
             "Example: !options gme",
        brief="Stock options"
    )
    @commands.is_owner()  # testing, this download a lot of shit
    async def ticker_options(self, ctx, symbol):
        # https://pypi.org/project/yfinance/
        try:
            ticker = yf.Ticker(symbol)
            options = ticker.options

            for date in options:
                chain = ticker.option_chain(date)
                print(chain)

            #if options.empty:
             #   raise Exception

        except Exception as e:
            await ctx.send(f"There was an error with the yfinance api :(\nError: {shared._ERRORS}")
            log.error(f"Error: {e}\n{shared._ERRORS}")
            return

    @commands.command(
        name='ticker-info',
        help="Display the info for a stock\n\n"
             "Params:\n"
             "> symbol: The symbol for the stock\n\n"
             "Example: !ticker-info gme",
        brief="Stock info"
    )
    @commands.is_owner()  # testing, this download a lot of shit
    async def ticker_info(self, ctx, symbol):
        # https://pypi.org/project/yfinance/
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if info.empty:
                raise Exception

            return info

        except Exception as e:
            await ctx.send(f"There was an error with the yfinance api :(\nError: {shared._ERRORS}")
            log.error(f"Error: {e}\n{shared._ERRORS}")
            return



def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(StockTickers(bot))
