import discord
from discord.ext import commands
import random
from discord.ext.commands import CheckFailure
import json
import time
import helpers.matterwatch as matterwatch
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
console=Console()
with open("./config/config.json", "r") as jsonfile:
    config = json.load(jsonfile)
role_list=config["roles"]
class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def ping(self, ctx):
        """ Pings the bot. """
       
        t1 = time.monotonic()
        msg = await ctx.send("Pong!")
        t2 = time.monotonic()

        latency = round((t2-t1)*1000)
        heartbeat = round(self.bot.latency * 1000)
        e = discord.Embed(title="Rok Toolkit Ping",color=0x17AC87)
        e.add_field(name="⏱️ Latency",value=f"{latency}ms", inline=True)
        e.add_field(name="💓 Heartbeat", value=f"{heartbeat}ms", inline=True)
        await msg.edit(content="", embed=e)
    def checker():
      async def predicate(ctx):
          reqrole=ctx.guild.get_role(role_list["fight"])
          for role in ctx.author.roles:
            if ctx.guild.owner.id==ctx.author.id and role!=reqrole:
              pass
            else:  
              return True
      return commands.check(predicate)
    @checker()
    @commands.command(hidden=True)  
    async def fight(self, ctx, user: discord.Member):
        """Fight a user."""
        potatoes = random.randint(1, 1000)
        await ctx.send(f"{ctx.author.mention} fought {user.mention} with {potatoes} potatoes!")

    @fight.error
    async def fight_error(self, ctx, error):
        role=ctx.guild.get_role(role_list["fight"])
        if config["error_checker"]==True:
          if isinstance (error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("```[⚠️] Missing Argument [⚠️]\n Please make sure to mention the user you want to fight```")
            return
          if isinstance (error, discord.ext.commands.errors.MissingRole):
            if role!=None:
              await ctx.send(f"```[⚠️] Missing Permissions [⚠️]\n You are missing the required role: {role.name}```")
              return
            else:
              await ctx.send("```[⚠️] How? [⚠️]\nHow the heck did you get this bot into this guild? You shouldnt even have this bot.```")
              return
        else:
          console.print(Panel.fit(Text.from_ansi("Error Checker turned off so no error returns for the fight error checker"),title=Text.from_ansi(f"{matterwatch.Red}Misc Cog Error:{matterwatch.End}")))
        return
async def setup(bot):
    await bot.add_cog(Misc(bot))