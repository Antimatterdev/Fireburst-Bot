import discord
from discord.ext import commands
from discord.errors import Forbidden
import json
import helpers.matterwatch as matterwatch
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
console=Console()
with open("./config/config.json", "r") as jsonfile:
    config = json.load(jsonfile)
async def send_content(ctx, con):
    try:
        await ctx.send(con)
    except Forbidden:
        if config["error_checker"]==True:
          await ctx.author.send(f"**Error**:\n```[⚠️] Missing permissions [⚠️]\nIt seems like im missing permissions to send messages in {ctx.channel.name} on {ctx.guild.name}.\nPlease inform the server team about this issue```\n\n**Requested Content:**\n{con}")
        console.print(Panel.fit(Text.from_ansi(f"Missing Permissions to send messages in channel [{ctx.channel.name}] on [{ctx.guild.name}]"),title=Text.from_ansi(f"{matterwatch.Red}Help Cog Error:{matterwatch.End}")))
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def help(self, ctx, *input):
        """Shows this message"""
        content=""
        prefix = config["prefix"]
        version = config["version"]
        owner_id=config["ownerid"]
        if not input:
            cogs_desc = ''
            command_list=[]
            for cog in self.bot.cogs:
              if self.bot.cogs[cog].__doc__!=None and cog.lower()!="help":
                cogs_desc += f'{cog}: {self.bot.cogs[cog].__doc__}\n'
              elif cog.lower()!="help":
                cogs_desc+=f'{cog}:\n'
              else:
                pass
              for command in self.bot.get_cog(cog).get_commands():
                  if command.name.lower()!="help":
                    command_list.append(command.name.lower())
                  if not command.name.lower()=="help":
                    if not command.hidden:
                      cogs_desc += f'   {command.name} {command.help}\n'
                    else:
                      try:
                        run= await command.can_run(ctx)
                      except:
                        run=False
                      if run==True:
                        cogs_desc+=f"   {command.name} {command.help}\n"
            content+=f"```{cogs_desc}"
            commands_desc = ''
            for command in self.bot.walk_commands():
                found=0
                for commands_li in command_list:
                  if command.name.lower()==commands_li:
                    found=1
                if found!=1:
                  if not command.hidden:
                    commands_desc += f'   {command.name} {command.help}\n'
                  else:
                    try:
                      run= await command.can_run(ctx)
                    except:
                      run=False
                    if run==True:
                      commands_desc+=f"   {command.name} {command.help}\n"
            if commands_desc!='':
                content+=f"No Category:\n{commands_desc}"
            content+=f"\nType {ctx.clean_prefix}help command for more info on a command.\nYou can also type {ctx.clean_prefix}help category for more info on a category```"
        elif str(input[0].lower()) == "help":
          content=f"```{ctx.clean_prefix}help [command]\n\nShows this message```"
        elif len(input) == 1 and not str(input[0].lower())=="help":
            if config["error_checker"]==True:
              content = f"```[⚠️] Module or Command Not Found [⚠️]\nThe item you requested may be disabled or you may have a typo in your request.```"
            else:
              content=f'No command called \"{input[0].lower()}\" found.' 
            if config["category_help"]==True:
              for cog in self.bot.cogs:
                if cog.lower() == input[0].lower():
                    content = f"```{cog} - Commands:\n"
                    for command in self.bot.get_cog(cog).get_commands():
                        if not command.hidden:
                            content+=f"  {ctx.clean_prefix}{command.name} {command.help}\n"
                        else:
                          try:
                            run= await command.can_run(ctx)
                          except:
                            run=False
                          if run==True:
                            content+=f"  {ctx.clean_prefix}{command.name} {command.help}\n"
                    content+=f"Type {ctx.clean_prefix}help command for more info on a command.\nYou can also type {ctx.clean_prefix}help category for more info on a category```"
            for cog in self.bot.cogs:
              for command in self.bot.get_cog(cog).get_commands():
                    if command.name.lower()==input[0].lower():
                      if not command.hidden:
                        content=f"```{ctx.clean_prefix}{command.name}"
                        for param in command.clean_params:
                          content+=f" <{param}>"
                        content+=f"\n\n{command.help}```"
                      else:
                        content=f"```{ctx.clean_prefix}{command.name}"
                        for param in command.clean_params:
                          content+=f" <{param}>"
                        content+=f"\n\n{command.help}```"
              break
        elif len(input) > 1:
            if config["error_checker"]==True:
              content="```[⚠️] Too many arguments [⚠️]\nPlease request only one module at once.```"
            console.print(Panel.fit(Text.from_ansi("Too many arguments supplied"),title=Text.from_ansi(f"{matterwatch.Red}Help Cog Error:{matterwatch.End}")))
        else:
            if config["error_checker"]==True:
              user=await self.bot.fetch_user(owner_id)
              content =f"```[⚠️] Welcome to the backrooms [⚠️]\nI don't know how you got here but here you are.\nPlease contact {user.display_name} for assistance```"
            console.print(Panel.fit(Text.from_ansi("Unknown Error"),title=Text.from_ansi(f"{matterwatch.Red}Help Cog Error:{matterwatch.End}")))
        if content!="":
          if input:
            if content==f"```[⚠️] Module or Command Not Found [⚠️]\nThe item you requested may be disabled or you may have a typo in your request.```" or content==f"No command called {input[0].lower()} found.":
              console.print(Panel.fit(Text.from_ansi("Module or Command could not be found from user input"),title=Text.from_ansi(f"{matterwatch.Red}Help Cog Error:{matterwatch.End}")))
              await send_content(ctx, content)
            else:
              await send_content(ctx, content) 
          else:
            await send_content(ctx, content) 
        else:
          console.print(Panel.fit(Text.from_ansi("No Content For Message supplied (I coded the help cog in a way that the error checkers would fix this but you may have them turned off)"),title=Text.from_ansi(f"{matterwatch.Red}Help Cog Error:{matterwatch.End}")))
async def setup(bot):
    await bot.add_cog(Help(bot))