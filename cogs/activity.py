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
            if top_user == 'Никто':
                user = 'Никто'
            user = self.bot.get_user(top_user)
            user = user.mention
            self.message_count = {}  # Обнуляем словарь для статы
            self.message_count['Никто'] = 0
            guild = self.bot.get_guild(489867322039992320)
            channel = self.bot.get_channel(944562833901899827)
            tstamp = int(datetime.now().timestamp())
            embed = disnake.Embed(color=0xd800f5)
            embed.set_author(name='Самый активный', icon_url=guild.icon.url)
            embed.set_thumbnail(url="https://i.imgur.com/64ibjZo.gif")
            embed.add_field(name='Участник:', value=f'{user}', inline=True)
            embed.add_field(name='Количество сообщений:', value=f'{messages}', inline=True)
            embed.add_field(name='', value=f'<t:{tstamp - 3600}:t> - <t:{tstamp}:t>', inline=False)
            await channel.send(embed=embed)

    @commands.slash_command(name='topuser', description='Показывает самого активного участника за час.')
    async def topuser(self, inter: disnake.ApplicationCommandInteraction):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer()
            except:
                return

            top_user = max(self.message_count, key=self.message_count.get)  # по ключу в словаре ищем чела
            messages = self.message_count[top_user]
            if top_user == 'Никто':
                user = 'Никто'
            user = self.bot.get_user(top_user)
            user = user.mention
            embed = disnake.Embed(color=0xd800f5)
            embed.set_author(name='Самый активный', icon_url=inter.guild.icon.url)
            embed.set_thumbnail(url="https://i.imgur.com/64ibjZo.gif")
            embed.add_field(name='Участник:', value=f'{user}', inline=True)
            embed.add_field(name='Количество сообщений:', value=f'{messages}', inline=True)
            try:
                await inter.edit_original_response(embed=embed)
            except:
                await inter.response.send_message(embed=embed, ephemeral=True)
        else:
            await inter.send('error')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:  # если не тупой поймешь
            return
        if message.author.id in self.message_count:
            self.message_count[message.author.id] += 1  # Если есть
        else:
            self.message_count[message.author.id] = 1  # Типо если нет чела в словарике


def setup(bot):
    bot.add_cog(ActivityCog(bot))
    print("ActivityCog is ready")