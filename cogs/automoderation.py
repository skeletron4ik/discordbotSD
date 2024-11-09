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
        self.mute_duration = [
            (2, timedelta(minutes=10)),
            (3, timedelta(minutes=30)),
            (4, timedelta(minutes=60)),
            (5, timedelta(hours=2)),
            (6, timedelta(hours=4)),
            (7, timedelta(hours=6)),
            (8, timedelta(hours=10)),
        ]



    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        if 'https://youtu.be' in message.content or 'https://www.youtube.com' in message.content or 'https://youtube.com' in message.content or 'https://discord.gg' in message.content or 'discord.gg' in message.content and not message.channel.id == 1044571685900259389:
            await message.delete()
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
                print('1')
            else:
                self.user_data[message.author.id] = 1
                print('2')
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)

            message_reply = await message.channel.send(
                f"{message.author.mention}, удалю твоё сообщение, запрещено отправлять ссылки", delete_after=5)
        if message.channel.id != 489867322039992323 and message.channel.id != 633033345600847872 and message.channel.id != 1279413707981455422:
            return
        print('11')
        if check_flood(message.author.id, message.content):
            await message.delete()
            if message.author.id in self.user_data:
                self.user_data[message.author.id] += 1
                print('1')
            else:
                self.user_data[message.author.id] = 1
                print('2')
            print(self.user_data)
            for count, timedelta_dur in self.mute_duration:
                if count == self.user_data[message.author.id]:
                    await message.author.timeout(duration=timedelta_dur)

            message_reply = await message.channel.send(
                f"{message.author.mention}, удалю твоё сообщение, не флуди!", delete_after=5)


def setup(bot):
    bot.add_cog(AutoModerationCog(bot))
    print("AutoModerationCog is ready")
