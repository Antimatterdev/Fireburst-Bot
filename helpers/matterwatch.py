import asyncio
import os
import sys
from functools import wraps
from pathlib import Path
try:
  from discord.ext import commands
except ImportError:
  from nextcord.ext import commands
from watchfiles import Change, awatch
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
console=Console()
End = '\33[0m'
Bold = '\33[1m'
Green = '\33[32m'
Red = '\33[31m'
Cyan ="\33[36m"
class Watcher:
    """The core matterwatch class -- responsible for starting up watchers and managing cogs.

    Attributes
        :client: A Bot client.
        :path: Root name of the cogs directory; matterwatch will only watch within
        this directory -- recursively.
        :debug: Whether to run the bot only when the debug flag is True.
        Defaults to True.
        :loop: Custom event loop. If not specified, will use the current running
        event loop.
        :preload: Whether to detect and load all found cogs on startup. Defaults
        to False.
        :colors: Whether to use colorized terminal outputs or not. Defaults to
        True.
    """

    def __init__(
        self,
        client: commands.Bot,
        path: str = 'commands',
        debug: bool = True,
        loop: asyncio.BaseEventLoop = None,
        preload: bool = False,
        colors: bool = True,
    ):
        self.client = client
        self.path = path
        self.debug = debug
        self.loop = loop
        self.preload = preload
        self.colors = colors

        if self.colors:
            self.CEND = '\33[0m'
            self.CBOLD = '\33[1m'
            self.CGREEN = '\33[32m'
            self.CRED = '\33[31m'
        else:
            self.CEND, self.CBOLD, self.CGREEN, self.CRED = '', '', '', ''

    @staticmethod
    def get_cog_name(path: str) -> str:
        """Returns the cog file name without .py appended to it."""
        _path = os.path.normpath(path)
        return _path.split(os.sep)[-1:][0][:-3]

    def get_dotted_cog_path(self, path: str) -> str:
        """Returns the full dotted path that discord.py uses to load cog files."""
        _path = os.path.normpath(path)
        tokens = _path.split(os.sep)
        reversed_tokens = list(reversed(tokens))

        # iterate over the list backwards in order to get the first occurrence in cases where a duplicate
        # name exists in the path (ie. example_proj/example_proj/commands)
        try:
            root_index = reversed_tokens.index(self.path.split('/')[0]) + 1
        except ValueError:
            raise ValueError('Use forward-slash delimiter in your `path` parameter.')

        return '.'.join([token for token in tokens[-root_index:-1]])

    async def _start(self):
        """Starts a watcher, monitoring for any file changes and dispatching event-related methods appropriately."""
        while self.dir_exists():
            try:
                async for changes in awatch(Path.cwd() / self.path):
                    self.validate_dir()

                    reverse_ordered_changes = sorted(changes, reverse=True)

                    for change in reverse_ordered_changes:
                        change_type = change[0]
                        change_path = change[1]

                        filename = self.get_cog_name(change_path)

                        new_dir = self.get_dotted_cog_path(change_path)
                        cog_dir = f'{new_dir}.{filename}' if new_dir else f'{self.path}.{filename}'

                        if change_type == Change.deleted:
                            if cog_dir in self.client.extensions:
                                await self.unload(cog_dir)
                        elif change_type == Change.added:
                            if cog_dir not in self.client.extensions:
                                await self.load(cog_dir)
                        elif change_type == Change.modified and change_type != (Change.added or Change.deleted):
                            if cog_dir in self.client.extensions:
                                await self.reload(cog_dir)
                            else:
                                await self.load(cog_dir)

            except FileNotFoundError:
                continue

            else:
                await asyncio.sleep(1)

        else:
            await self.start()

    def check_debug(self):
        """Determines if the watcher should be added to the event loop based on debug flags."""
        return any([(self.debug and __debug__), not self.debug])

    def dir_exists(self):
        """Predicate method for checking whether the specified dir exists."""
        return Path(Path.cwd() / self.path).exists()

    def validate_dir(self):
        """Method for raising a FileNotFound error when the specified directory does not exist."""
        if not self.dir_exists():
            raise FileNotFoundError
        return True

    async def start(self):
        """Checks for a user-specified event loop to start on, otherwise uses current running loop."""
        _check = False
        while not self.dir_exists():
            if not _check:
                console.print(Panel.fit(Text.from_ansi(f'The path {self.CBOLD}{Path.cwd() / self.path}{self.CEND} does not exist.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
                _check = True

        else:
            console.print(Panel.fit(Text.from_ansi(f'Found {self.CBOLD}{Path.cwd() / self.path}{self.CEND}!'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))
            if self.preload:
                await self._preload()

            if self.check_debug():
                if self.loop is None:
                    self.loop = asyncio.get_event_loop()
                console.print(Panel.fit(Text.from_ansi(f'Watching for file changes in {self.CBOLD}{Path.cwd() / self.path}{self.CEND}...'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))
                self.loop.create_task(self._start())

    async def load(self, cog_dir: str):
        """Loads a cog file into the client."""
        try:
            await self.client.load_extension(cog_dir)
        except commands.ExtensionAlreadyLoaded:
            console.print(Panel.fit(Text.from_ansi(f'Cannot reload {cog_dir} because it is not loaded.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
        except commands.NoEntryPointError:
            console.print(Panel.fit(Text.from_ansi(f'{self.CBOLD}{self.CRED}[Error]{self.CEND} Failed to load {self.CBOLD}{cog_dir}{self.CEND}; no entry point found.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
        except Exception as exc:
            self.cog_error(exc)
        else:
            console.print(Panel.fit(Text.from_ansi(f'{self.CBOLD}{self.CGREEN}[Cog Loaded]{self.CEND} {cog_dir}'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))

    async def unload(self, cog_dir: str):
        """Unloads a cog file into the client."""
        try:
            await self.client.unload_extension(cog_dir)
        except commands.ExtensionNotLoaded:
            console.print(Panel.fit(Text.from_ansi(f'Cannot reload {cog_dir} because it is not loaded.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
        except Exception as exc:
            self.cog_error(exc)
        else:
            console.print(Panel.fit(Text.from_ansi(f'{self.CBOLD}{self.CRED}[Cog Unloaded]{self.CEND} {cog_dir}'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))

    async def reload(self, cog_dir: str):
        """Attempts to atomically reload the file into the client."""
        try:
            await self.client.reload_extension(cog_dir)
        except commands.NoEntryPointError:
            console.print(Panel.fit(Text.from_ansi(f'{self.CBOLD}{self.CRED}[Error]{self.CEND} Failed to reload {self.CBOLD}{cog_dir}{self.CEND}; no entry point found.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
        except commands.ExtensionNotLoaded:
            console.print(Panel.fit(Text.from_ansi(f'Cannot reload {cog_dir} because it is not loaded.'),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))
        except Exception as exc:
            self.cog_error(exc)
        else:
            console.print(Panel.fit(Text.from_ansi(f'{self.CBOLD}{self.CGREEN}[Cog Reloaded]{self.CEND} {cog_dir}'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))

    @staticmethod
    def cog_error(exc: Exception):
        """Logs exceptions. TODO: Need thorough exception handling."""
        if isinstance(exc, (commands.ExtensionError, SyntaxError)):
          console.print(Panel.fit(Text.from_ansi(exc),title=Text.from_ansi(f"{self.CRED}MatterWatch Error:{self.CEND}")))

    async def _preload(self):
        console.print(Panel.fit(Text.from_ansi('Preloading cogs...'),title=Text.from_ansi(f"{self.CGREEN}MatterWatch:{self.CEND}")))
        for cog in {(file.stem, file) for file in Path(Path.cwd() / self.path).rglob('*.py')}:
            new_dir = self.get_dotted_cog_path(cog[1])
            await self.load('.'.join([new_dir, cog[0]]))


def watch(**kwargs):
    """Instantiates a watcher by hooking into a Bot client methods' `self` attribute."""

    def decorator(function):
        @wraps(function)
        async def wrapper(client):
            cw = Watcher(client, **kwargs)
            await cw.start()
            ret_val = await function(client)
            return ret_val

        return wrapper

    return decorator
