from datetime import datetime
import discord

class Message():
    """
        Provides basic embed templates for all kinds of messages to use. Keeps everything tidied up in one place

        Examples:
        Create an error message = ErrorMessage("Error", "Something went wrong...").new()

        Create a green message -> msg = Message("Message", "hello world", discord.Color.green()).new()
    """
    def __init__(self, title:str="\u200b", msg:str="\u200b", color: discord.Color = discord.Color.blue()):
        self.description = msg
        self.title = title
        self.color = color

    def new(self):
        embed = discord.Embed(title=f"{self.title}", description=f"{self.description}", color=self.color)
        return embed

class ErrorMessage(Message):
    def __init__(self, title:str, msg:str, color: discord.Color = discord.Color.red()):
        super().__init__(title, msg, color)
        
    def new(self):
        embed = super().new()
        embed.timestamp = datetime.now()
        return embed

class WarnMessage(Message):
    def __init__(self, title:str, msg:str,  color: discord.Color = discord.Color.orange()):
        super().__init__(title, msg, color)

    def new(self):
        return super().new()
        