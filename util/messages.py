from datetime import datetime
import discord

class Message():
    def __init__(self, title:str, msg:str):
        self.description = msg
        self.title = title
        self.color = discord.Color.blue()
        self.embed = discord.Embed(title=f"{self.title}", description=f"{self.description}",color=self.color)

    def new(self): 
        return self.embed

class ErrorMessage(Message):
    def __init__(self):
        self.color = discord.Color.red()
        self.embed.timestamp = datetime.now()

class WarnMessage(Message):
    def __init__(self):
        self.color = discord.Color.orange()