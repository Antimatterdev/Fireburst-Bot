import discord
from discord.ext import commands
import helpers.matterwatch as matterwatch
import json
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
console=Console()
with open("./config/config.json", "r") as jsonfile:
    config = json.load(jsonfile)
class RokClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.presences = False
        super().__init__(help_command=None,command_prefix=(config["prefix"]), intents=intents)
    @matterwatch.watch(path='cogs',preload=True)
    async def on_ready(self):
        text = Text.from_ansi(f"Logged in as {matterwatch.Bold}{matterwatch.Cyan}{self.user.name}{matterwatch.End} with version {matterwatch.Bold}{matterwatch.Green}{config['version']}{matterwatch.End}")
        console.print(Panel.fit(text))
bot = RokClient()
bot.run(config["token"])