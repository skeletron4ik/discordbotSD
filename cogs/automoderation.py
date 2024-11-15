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


def create_log_embed(bot, участник, message, dur, reason):
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
    embed.add_field(name='Ваше сообщение удалено', value=f'**Причина:** {message}')
    embed.set_thumbnail(url="https://i.imgur.com/bugnSyX.gif")
    embed.set_footer(text='Автомодерация')
    return embed


def check_flood(user_id, message_text):
    current_time = time.time()  # Текущее время в секундах
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


user_message_times = {}


def check_spam(user_id):
    current_time = time.time()
    if user_id not in user_message_times:
        user_message_times[user_id] = []

    # Очищаем сообщения старше 10 секунд
    user_message_times[user_id] = [
        timestamp for timestamp in user_message_times[user_id] if current_time - timestamp < 10
    ]

    # Добавляем текущее сообщение
    user_message_times[user_id].append(current_time)

    # Если сообщений больше 5 за 10 секунд — это спам
    return len(user_message_times[user_id]) > 3


class AutoModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_data = {}
        self.update.start()
        self.mute_duration = [
            (2, timedelta(minutes=1)),
            (3, timedelta(minutes=10)),
            (4, timedelta(minutes=30)),
            (5, timedelta(hours=1)),
            (6, timedelta(hours=2)),
            (7, timedelta(hours=4)),
            (8, timedelta(hours=8)),
            (9, timedelta(hours=14))
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
        roles = [
            message.guild.get_role(518505773022838797),  # admin
            message.guild.get_role(580790278697254913),  # chief
            message.guild.get_role(702593498901381184),  # moder
            message.guild.get_role(757930494301044737),  # booster
            message.guild.get_role(1044314368717897868),  # diamond
            # message.guild.get_role(1303396950481174611),  # gold
        ]

        if message.author.bot:
            return
        # Проверяем, есть ли у пользователя хотя бы одна из этих ролей
        if any(role in member.roles for role in roles):
            return

        # Проверка на слишком частые сообщения (спам)
        if check_spam(message.author.id):
            try:
                await message.delete()
            except:
                return
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
            else:
                self.user_data[message.author.id] = 1
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)
                    log_embed = create_log_embed(self.bot, message.author, message, timedelta_dur,
                                                 'Слишком частые сообщения')
                    await channel.send(embed=log_embed)
            embed = create_error_embed('Слишком частые сообщения')
            await message.channel.send(content=message.author.mention, embed=embed, delete_after=120)

        forbidden_links = [
            'https://youtu.be', 'https://www.youtube.com',
            'https://youtube.com', 'https://discord.gg', 'discord.gg'
        ]

        if any(link in message.content for link in forbidden_links) and message.channel.id != 1044571685900259389:
            try:
                await message.delete()
            except:
                return

            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
            else:
                self.user_data[message.author.id] = 1
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)
                    log_embed = create_log_embed(self.bot, message.author, message, timedelta_dur,
                                                 'Ссылки или приглашения')
                    await channel.send(embed=log_embed)
            embed = create_error_embed('Ссылки или приглашения')
            await message.channel.send(content=message.author.mention, embed=embed, delete_after=120)

        if check_flood(message.author.id, message.content):
            try:
                await message.delete()
            except:
                return
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
            else:
                self.user_data[message.author.id] = 1
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)
                    log_embed = create_log_embed(self.bot, message.author, message, timedelta_dur,
                                                 'Флуд одинаковыми сообщениями')
                    await channel.send(embed=log_embed)
            embed = create_error_embed('Флуд одинаковыми сообщениями')
            await message.channel.send(content=message.author.mention, embed=embed, delete_after=120)

        letters_of_words = list(message.content)
        for letter in letters_of_words:
            if letter.istitle():
                upper_letter += 1
        message_blank = message.content.replace(" ", "")
        if upper_letter >= 20 and (upper_letter / len(message_blank)) >= 0.8:
            await message.delete()
            embed = create_error_embed('Чрезмерное использование верхнего регистра')
            await message.channel.send(embed=embed, delete_after=120)


def setup(bot):
    bot.add_cog(AutoModerationCog(bot))
    print("AutoModerationCog is ready")
