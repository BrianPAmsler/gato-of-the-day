import discord
import datetime
from img_cache import ImageCache
import persistence

from typing import Any
from time import strptime
from discord.flags import Intents
from pytz import timezone, utc
from discord.ext import commands, tasks
from gato_collector import get_pic, is_valid_name, get_title, load_api_info, names
from os import path
import requests
from os import system
import functools
import typing

SAVE_FILE = "channels.json"


async def run_blocking(blocking_func: typing.Callable, client, *args, **kwargs) -> typing.Any:
    """Runs a blocking function in a non-blocking way"""
    func = functools.partial(
        blocking_func, *args, **kwargs)  # `run_in_executor` doesn't support kwargs, `functools.partial` does
    return await client.loop.run_in_executor(None, func)

def ishi(url: str) -> str:
    fname = "pre_input.jpg"
    if url.endswith(".png"):
        fname = "pre_input.png"

    data = requests.get(url, allow_redirects=True)
    f = open(fname, 'wb')
    f.write(data.content)
    f.close()

    # remove background
    print("Removing background...")
    system('backgroundremover -i "' + fname + '" -o "input.png"')

    # make ishihara
    print("Generating image...")
    system('image_processing -i "input.png" -o "output.png"')

    return fname

def generate_ishihara(animal: str) -> str:
    url = get_pic(animal)
    while url.endswith(".gif"):
        print("IGNORED GIF")
        url = get_pic(animal)
    
    ishi(url)

    return "output.png"

async def ishihara(channel: discord.TextChannel, animal: str, cache: ImageCache) -> None:
    if not is_valid_name(animal):
        await channel.send("Invalid animal!")
        return
    
    # downlaod gato
    tempfile = cache.get(animal)

    await channel.send(file=discord.File(tempfile.file))

async def send_pic(channel: discord.TextChannel, animal: str, title: str) -> None:
    embed = discord.Embed(title=title, description="")
    embed.set_image(url=get_pic(animal))
    await channel.send(embed=embed)

def to_utc(dt: datetime.datetime) -> datetime.time:
    dt = dt.astimezone(utc)

    return datetime.time(hour=dt.hour, minute=dt.minute, tzinfo=utc)

def make_cog(dt, channel: discord.TextChannel) -> commands.Cog:
    time = to_utc(dt)

    class GatoCog(commands.Cog):
        def __init__(self, channel: discord.TextChannel):
            self.channel = channel
            self.my_task.start()

        def cog_unload(self):
            self.my_task.cancel()

        @tasks.loop(time=time)
        async def my_task(self):
            await send_pic(self.channel, "gato", "Gato of the Day")

    return GatoCog(channel)

class GatoClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.channels = set()
        self.cogs = {}

    def add_channel(self, channel: int, dt: datetime) -> bool:
        tpl = (channel, dt)

        if tpl in self.channels:
            return False

        ch = self.get_channel(channel)
        self.cogs[tpl] = make_cog(dt, ch)
        self.channels.add(tpl)

        persistence.save_client(self, SAVE_FILE)

        return True

    def remove_channel(self, channel: int) -> None:
        for i, tpl in list(enumerate(self.channels)):
            if tpl[0] == channel:
                self.cogs[tpl].cog_unload()
                self.channels.remove(tpl)
                del self.cogs[tpl]

        persistence.save_client(self, SAVE_FILE)

def to_dt(time: datetime.datetime, tz) -> datetime.datetime:
    dt = datetime.datetime.now()
    dt = dt.astimezone(tz)

    return dt.replace(hour=time.tm_hour, minute=time.tm_min, second=0, microsecond=0)

def run_bot():
    intents = discord.Intents.default()
    intents.message_content = True

    load_api_info()
    
    cache = ImageCache("ishicache", 10, generate_ishihara)

    for animal in names():
        cache.init_cache(animal)

    cache.start()

    client = GatoClient(intents=intents)

    @client.event
    async def on_ready():
        if path.exists(SAVE_FILE):
            persistence.load_client(client, SAVE_FILE)

            for channel in client.channels:
                client.cogs[channel] = make_cog(
                    channel[1], client.get_channel(channel[0]))

        print(f'We have logged in as {client.user}')

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user:
            return

        parts = message.content.split(' ')

        if parts[0] == '!gotd':
            if not message.author.guild_permissions.administrator:
                return
            if len(parts) < 2:
                return

            if parts[1] == "list":
                pass
            elif parts[1] == "remove":
                client.remove_channel(message.channel.id)
                await message.channel.send("Channel unregistered!")
            else:
                if len(parts) < 3:
                    return

                channel = message.channel
                time = strptime(parts[1], "%I:%M%p")
                tz = timezone(parts[2])

                t = to_dt(time, tz)
                if client.add_channel(channel.id, t):
                    await channel.send("Channel registered for Gato of the Day!")
                else:
                    await channel.send("Channel already registered for given time!")
        elif parts[0] == "!ishihara":
            if len(parts) >= 1:
                animal = parts[1]
                await ishihara(message.channel, animal, cache)
        elif parts[0][0] == "!" and is_valid_name(parts[0][1:]):
            animal = parts[0][1:]
            await send_pic(message.channel, animal, get_title(animal))

    secret_file = open("discord-client-secret.txt", 'r')
    secret = secret_file.read().strip()
    secret_file.close()

    try:
        client.run(secret)
    except KeyboardInterrupt:
        cache.kill()
