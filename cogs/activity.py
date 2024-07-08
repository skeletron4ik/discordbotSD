import disnake
from pymongo import MongoClient, errors
from disnake.ext import commands, tasks
from datetime import datetime
import os
import asyncio
import time


class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_count = {}
        self.update_leaderboard.start()

    @tasks.loop(seconds=3600)
    async def update_leaderboard(self):
        if self.message_count:
            top_user = max(self.message_count, key=self.message_count.get)  # по ключу в словаре ищем чела
            messages = self.message_count[top_user]
            user = self.bot.get_user(top_user)
            self.message_count = {}  # Обнуляем словарь для статы
            guild = self.bot.get_guild(489867322039992320)
            channel = self.bot.get_channel(944562833901899827)
            tstamp = int(datetime.now().timestamp())
            embed = disnake.Embed(color=0x8A2BE2)
            embed.set_author(name='Самый активный', icon_url=guild.icon.url)
            embed.add_field(name='Участник:', value=f'{user.mention}', inline=True)
            embed.add_field(name='Количество сообщений:', value=f'{messages}', inline=True)
            embed.add_field(name='', value=f'<t:{tstamp - 3600}:t> - <t:{tstamp}:t>', inline=False)
            await channel.send(embed=embed)

    @commands.slash_command(name='topuser', description='Показывает самого активного участника за час.')
    async def topuser(self, ctx):
        top_user = max(self.message_count, key=self.message_count.get)  # по ключу в словаре ищем чела
        messages = self.message_count[top_user]
        user = self.bot.get_user(top_user)
        embed = disnake.Embed(color=0x8A2BE2)
        embed.set_author(name='Самый активный', icon_url=ctx.guild.icon.url)
        embed.add_field(name='Участник:', value=f'{user.mention}', inline=True)
        embed.add_field(name='Количество сообщений:', value=f'{messages}', inline=True)
        await ctx.send(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:  # если не тупой поймешь
            return
        if message.author.id in self.message_count:
            self.message_count[message.author.id] += 1  # Если есть
            print('+=')
        else:
            self.message_count[message.author.id] = 1  # Типо если нет чела в словарике
            print('=')


def setup(bot):
    bot.add_cog(ActivityCog(bot))
    print("ActivityCog is ready")
