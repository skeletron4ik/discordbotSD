import disnake
from pymongo import MongoClient, errors, collection
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
import os
import asyncio
import time
import random
import math
import re
from main import cluster

collusers = cluster.server.users
collservers = cluster.server.servers

user_last_messages = {}
flood_threshold = 20

def create_log_embed(bot, channel, участник, message, dur, reason):

    embed = disnake.Embed(title="", url="",
                          description="", color=0xff8800, timestamp=datetime.now())
    embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был замучен!",
                    inline=False)
    embed.set_thumbnail(
        url="https://media4.giphy.com/media/4A2MFWNlGaGUJcyhlE/giphy.gif")
    embed.add_field(name="Модератор:", value=f"*{bot.user.name}* ({bot.user.mention})", inline=True)
    embed.add_field(name="Участник:", value=f"*{участник}* ({участник.mention})", inline=True)
    embed.add_field(name="Канал:", value=f"{message.channel.mention}", inline=True)
    embed.add_field(name="Время:", value=f"{dur}", inline=True)
    embed.add_field(name="Причина:", value=reason, inline=True)
    embed.set_footer(text=f"ID участника: {участник.id}")
    return embed

def create_error_embed(message: str) -> disnake.Embed:
    embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
    embed.add_field(name='Ваше сообщение удалено', value=f'Причина: {message}')
    embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
    embed.set_footer(text='Автомодерация')
    return embed
def check_flood(user_id, message_text):
    current_time = time.time()  # Текущее время в секундах
    print('qqq')
    if user_id in user_last_messages:
        last_message_time, last_message_text, message_count = user_last_messages[user_id]

        # Проверяем, прошло ли время меньше, чем flood_threshold и одно и то же ли сообщение
        if current_time - last_message_time < flood_threshold and message_text == last_message_text:
            message_count += 1  # Увеличиваем счетчик одинаковых сообщений
        else:
            message_count = 1  # Если прошло больше времени или сообщение другое, сбрасываем счетчик

        # Если количество одинаковых сообщений больше или равно threshold, считаем флудом
        if message_count >= 3:
            return True  # Флуд обнаружен

    else:
        message_count = 1  # Если это первое сообщение, устанавливаем счетчик в 1

        # Обновляем данные пользователя (время, текст и счетчик)
    user_last_messages[user_id] = (current_time, message_text, message_count)
    return False  # Флуд не обнаружен

class AutoModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = {}
        self.update.start()
        self.mute_duration = [
            (2, timedelta(minutes=10)),
            (3, timedelta(minutes=30)),
            (4, timedelta(minutes=60)),
            (5, timedelta(hours=2)),
            (6, timedelta(hours=4)),
            (7, timedelta(hours=6)),
            (8, timedelta(hours=10)),
        ]

    @tasks.loop(hours=24)
    async def update(self):
        self.user_data = {}

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild is None:
            return

        member = message.guild.get_member(message.author.id)
        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи
        upper_letter = 0
        booster = message.guild.get_role(757930494301044737)
        diamond = message.guild.get_role(1044314368717897868)

        if booster in member.roles or diamond in member.roles:
            return

        if message.author.bot:
            return

        if 'https://youtu.be' in message.content or 'https://www.youtube.com' in message.content or 'https://youtube.com' in message.content or 'https://discord.gg' in message.content or 'discord.gg' in message.content and not message.channel.id == 1044571685900259389:
            await message.delete()
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
            else:
                self.user_data[message.author.id] = 1
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)
                    log_embed = create_log_embed(self.bot, channel, message.author, message.channel, timedelta_dur, 'Ссылки или приглашения.')
                    await channel.send(embed=log_embed)
            embed = create_error_embed('Ссылки или приглашения.')
            message_reply = await message.channel.send(content=message.author.mention, embed=embed, delete_after=10)

        if message.channel.id != 489867322039992323 and message.channel.id != 633033345600847872 and message.channel.id != 1279413707981455422:
            return

        if check_flood(message.author.id, message.content):
            await message.delete()
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
            else:
                self.user_data[message.author.id] = 1
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)
                    log_embed = create_log_embed(self.bot, channel, message.author, message.channel, timedelta_dur, 'Флуд')
                    await channel.send(embed=log_embed)
            embed = create_error_embed('Флуд.')
            message_reply = await message.channel.send(content=message.author.mention,embed=embed, delete_after=10)

        letters_of_words = list(message.content)
        for letter in letters_of_words:
            if letter.istitle():
                upper_letter += 1
        if upper_letter >= 8:
            await message.delete()
            embed = create_error_embed('Капс.')
            print(upper_letter, message.content, letters_of_words)
            message_reply = await message.channel.send(embed=embed, delete_after=10)


def setup(bot):
    bot.add_cog(AutoModerationCog(bot))
    print("AutoModerationCog is ready")
