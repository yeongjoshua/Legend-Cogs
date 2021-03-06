import discord
from discord.ext import commands
from cogs.utils import checks
from .utils.dataIO import dataIO, fileIO
from __main__ import send_cmd_help
import os
import datetime
import time
import asyncio

settings_path = "data/stats/settings.json"

class stats:
    """Clash Royale 1v1 Duels with bets"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json(settings_path)
        self.member_log = dataIO.load_json('data/clanlog/member_log.json')
        self.cycle_task1 = bot.loop.create_task(self.updateUserCount())
        self.cycle_task2 = bot.loop.create_task(self.updateMiscCount())

    def __unload(self):
        self.cycle_task1.cancel()
        self.cycle_task2.cancel()

    @commands.group(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def stats(self, ctx):
        """Server Stats settings"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @stats.command(pass_context=True)
    async def setup(self, ctx):
        """Setup the server stats"""

        server = ctx.message.server

        everyone = discord.PermissionOverwrite(connect=False, view_channel=True)

        member_channel = await self.bot.create_channel(server, '0 Members', (server.default_role, everyone), type=discord.ChannelType.voice)
        guests_channel = await self.bot.create_channel(server, '0 Guests', (server.default_role, everyone), type=discord.ChannelType.voice)
        online_channel = await self.bot.create_channel(server, '0 Online Users', (server.default_role, everyone), type=discord.ChannelType.voice)
        user_channel = await self.bot.create_channel(server, '0 Total Users', (server.default_role, everyone), type=discord.ChannelType.voice)
        server_channel = await self.bot.create_channel(server, '0 Days Old', (server.default_role, everyone), type=discord.ChannelType.voice)
        time_channel = await self.bot.create_channel(server, '0 GMT', (server.default_role, everyone), type=discord.ChannelType.voice)

        self.settings[server.id] = {}
        self.settings[server.id]['channels'] = {}
        self.settings[server.id]['channels']['member_channel'] = member_channel.id
        self.settings[server.id]['channels']['guests_channel'] = guests_channel.id
        self.settings[server.id]['channels']['online_channel'] = online_channel.id
        self.settings[server.id]['channels']['user_channel'] = user_channel.id
        self.settings[server.id]['channels']['server_channel'] = server_channel.id
        self.settings[server.id]['channels']['time_channel'] = time_channel.id

        fileIO(settings_path, "save", self.settings)
        await self.bot.say("Stats Setup Compeleted.")

    async def getUserCount(self, server, name):
        """Returns the numbers of people with the member role"""
        members = server.members

        count = 0
        for member in members:
            for role in member.roles:
                if role.name == name:
                    count += 1

        return count

    async def updateUserCount(self):
        """Update counter every few minutes"""
        await self.bot.wait_until_ready()

        try:
            await asyncio.sleep(20)  # Start-up Time
            while True:
                servers = [x for x in self.bot.servers if x.id in self.settings]
                for server in servers:
                    channels = self.settings[server.id]['channels']

                    self.member_log = dataIO.load_json('data/clanlog/member_log.json')
                    passed = (datetime.datetime.utcnow() - server.created_at).days

                    await self.bot.edit_channel(server.get_channel(channels['member_channel']),name="{} Members".format(str(self.member_log[max(self.member_log.keys())])))
                    await self.bot.edit_channel(server.get_channel(channels['guests_channel']),name="{} Guests".format(await self.getUserCount(server, "Guest")))
                    await self.bot.edit_channel(server.get_channel(channels['user_channel']),name="{} Total Users".format(len(server.members)))
                    await self.bot.edit_channel(server.get_channel(channels['server_channel']),name="{} Days Old".format(str(passed)))
                    
                await asyncio.sleep(600)  # task runs every 600 seconds
        except asyncio.CancelledError:
            pass

    async def updateMiscCount(self):
        """Update counter every few minutes"""
        await self.bot.wait_until_ready()

        try:
            await asyncio.sleep(20)  # Start-up Time
            while True:
                servers = [x for x in self.bot.servers if x.id in self.settings]
                for server in servers:
                    channels = self.settings[server.id]['channels']

                    online = len([m.status for m in server.members
                      if m.status == discord.Status.online or
                      m.status == discord.Status.idle])   

                    await self.bot.edit_channel(server.get_channel(channels['online_channel']),name="{} Online Users".format(str(online)))
                    await self.bot.edit_channel(server.get_channel(channels['time_channel']),name="{} GMT".format(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")))
        
                await asyncio.sleep(15)  # task runs every 60 seconds
        except asyncio.CancelledError:
            pass

def check_folders():
    if not os.path.exists("data/stats"):
        print("Creating data/stats folder...")
        os.makedirs("data/stats")

def check_files():
    f = settings_path
    if not fileIO(f, "check"):
        print("Creating stats settings.json...")
        dataIO.save_json(f, {})

    f = "data/clanlog/member_log.json"
    if not fileIO(f, "check"):
        print("Creating empty member_log.json...")
        dataIO.save_json(f, {"1524540132" : 0})

def setup(bot):
    check_folders()
    check_files()

    bot.add_cog(stats(bot))