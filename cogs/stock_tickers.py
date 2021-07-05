import io

import discord
import matplotlib.pyplot as plt
import yfinance as yf
from discord.ext import commands


class StockTickers(commands.Cog):
    """This is a cog that gets info about a stock ticker.
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

    @staticmethod
    def get_close_price(symbol):
        ticker = yf.Ticker(symbol)
        data_today = ticker.history(period='1d')
        return data_today['Close'][0]

    @commands.command(
        name="ticker-close",
        help="Display the close price of a stock",
        brief="Stock close"
    )
    async def get_close(self, ctx, symbol):
        # print(StockTickers.get_close_price(symbol))
        await ctx.send(f'${symbol} Closing price today is ${StockTickers.get_close_price(symbol)}')

    @staticmethod
    def get_open_price(symbol):
        ticker = yf.Ticker(symbol)
        data_today = ticker.history(period='1d')
        return data_today['Open'][0]

    @commands.command(
        name="ticker-open",
        help="Display the open price of a stock",
        brief="Stock open"
    )
    async def get_open(self, ctx, symbol):
        # print(StockTickers.get_open_price(symbol))
        await ctx.send(f'{symbol} Opening price today is ${StockTickers.get_open_price(symbol)}')

    @commands.command(name='graph', aliases=['gr'])
    async def graph(self, ctx, symbol):

        if not symbol:
            raise commands.CommandError(message=f'Required argument missing: `symbol`.')

        data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers=symbol,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            period="1d",

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval="1m",

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
            raise commands.CommandError(message=f'Could not find data for: {symbol}.')

        print(data)

        link = f'https://finance.yahoo.com/quote/{symbol}?p={symbol}&.tsrc=fin-srch'

        colour = 0x00b2ff
        embed = discord.Embed(title=symbol, colour=colour, url=link)

        plt.style.use('dark_background')
        data['Close'].plot(color='#47a0ff')
        plt.xlabel("Date")
        plt.ylabel("Close")
        plt.title(f"${symbol} Price data")

        plt.savefig('images/graph.png', transparent=True)

        with open('images/graph.png', 'rb') as f:
            file = io.BytesIO(f.read())

        image = discord.File(file, filename='graph.png')
        embed.set_image(url=f'attachment://graph.png')

        await ctx.send(file=image, embed=embed)


def setup(bot):
    """Every cog needs a setup function like this."""
    bot.add_cog(StockTickers(bot))
