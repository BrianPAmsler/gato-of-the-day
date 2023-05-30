import discord
import datetime
import persistence

from typing import Any
from time import strptime
from discord.flags import Intents
from pytz import timezone, utc
from discord.ext import commands, tasks
from gato_collector import get_gato, get_perro
from os import path

SAVE_FILE = "channels.json"

async def gato(channel, title="Gato of the Day"):
    embed = discord.Embed(title=title, description="")
    embed.set_image(url=get_gato())
    await channel.send(embed=embed)

async def perro(channel, title="Doggo of the Day"):
    embed = discord.Embed(title=title, description="")
    embed.set_image(url=get_perro())
    await channel.send(embed=embed)

def to_utc(dt: datetime.datetime):
    dt = dt.astimezone(utc)

    return datetime.time(hour=dt.hour, minute=dt.minute, tzinfo=utc)

def make_cog(dt, channel: discord.TextChannel):
    time = to_utc(dt)

    class GatoCog(commands.Cog):
        def __init__(self, channel: discord.TextChannel):
            self.channel = channel
            self.my_task.start()

        def cog_unload(self):
            self.my_task.cancel()

        @tasks.loop(time=time)
        async def my_task(self):
            await gato(self.channel)
    
    return GatoCog(channel)

class GatoClient(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.channels = set()
        self.cogs = {}
    
    def add_channel(self, channel: int, dt: datetime):
        tpl = (channel, dt)

        if tpl in self.channels:
            return False
        
        ch = self.get_channel(channel)
        self.cogs[tpl] = make_cog(dt, ch)
        self.channels.add(tpl)
        
        persistence.save_client(self, SAVE_FILE)

        return True
    
    def remove_channel(self, channel: int):
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

    client = GatoClient(intents=intents)

    @client.event
    async def on_ready():
        if path.exists(SAVE_FILE):
            persistence.load_client(client, SAVE_FILE)
            
            for channel in client.channels:
                client.cogs[channel] = make_cog(channel[1], client.get_channel(channel[0]))

        print(f'We have logged in as {client.user}')

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user:
            return
        
        if message.content.startswith("!gato"):
            await gato(message.channel, title="Gato")

        if message.content.startswith("!perro"):
            await perro(message.channel, title="Doggo")

        if not message.author.guild_permissions.administrator:
            return

        parts = message.content.split(' ')
        
        if parts[0] == '!gotd':
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

    secret_file = open("discord-client-secret.txt", 'r')
    secret = secret_file.read().strip()
    secret_file.close()
    
    client.run(secret)