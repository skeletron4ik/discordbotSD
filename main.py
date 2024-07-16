import disnake
from pymongo import MongoClient, errors
from disnake.ext import commands
from datetime import datetime
import os
import asyncio
import time


bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all(), reload=True)
bot.member_cache_flags = disnake.MemberCacheFlags.all()
cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans

class RulesClass:
    def __init__(self, bot):
        self.bot = bot
        self.check_warns.start()  # Запуск циклической задачи при инициализации
        self.rules = {
            "1.1": "1.1> Обман/попытка обмана Администрации сервера, грубое оспаривание действий Администрации сервера",
            "1.2": "1.2> Распространение личной информации без согласия",
            "1.3": "1.3> Обход правил сервера с помощью мультиаккаунта и любым другим способом",
            "1.4": "1.4> Транслирование или отправка контента, предназначенного для лиц старше 18 лет",
            "1.5": "1.5> Использование недопустимого никнейма или аватара",
            "1.6": "1.6> Подделка доказательств против участников/Администрации",
            "2.1": "2.1> Флуд, спам, чрезмерное упоминание ролей или участника",
            "2.2": "2.2> Оскорбления участников и их близких родственников",
            "2.3": "2.3> Оскорбление или неуважительное отношение к Администрации и серверу",
            "2.4": "2.4> Проведение политической или религиозной агитации, обсуждение военных действий, оскорбление стран, наций и субкультур",
            "2.5": "2.5> Реклама сторонних проектов, сайтов, каналов и т.д.",
            "3.1": "3.1> Крики, шумы, помехи, транслирование музыки не через бота, неадекватное поведение, использование программ для изменения голоса",
            "3.2": "3.2> Многочисленные перемещения по голосовым каналам, быстрое включение/выключение демонстрации экрана",
            "3.3": "3.3> AFK-фарм Румбиков ◊"
        }

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!\nID: {bot.user.id}")
    for guild in bot.guilds:
        for member in guild.members:
            values = {
                "id": member.id,
                "guild_id": guild.id,
                "warns": 0,
                "reasons": []
            }
            ban_values = {
                "id": member.id,
                "guild_id": guild.id,
                "ban": 'False',
                'Timestamp': 0,
                "reason": 'None'
            }
            server_values = {
                "_id": guild.id,
                "case": 0
            }

            if collusers.count_documents({"id": member.id, "guild_id": guild.id}) == 0:
                collusers.insert_one(values)
            if collservers.count_documents({"_id": guild.id}) == 0:
                collservers.insert_one(server_values)
            if collbans.count_documents({"id": member.id, "guild_id": guild.id}) == 0:
                collbans.insert_one(ban_values)



@bot.event
async def on_member_join(member):
    values = {
        "id": member.id,
        "guild_id": member.guild.id,
        "warns": 0,
        "reasons": []
    }
    ban_values = {
        "id": member.id,
        "guild_id": member.guild.id,
        "ban": 'False',
        'Timestamp': 0,
        "reasons": 'None'
    }

    if collusers.count_documents({"id": member.id, "guild_id": member.guild.id}) == 0:
        collusers.insert_one(values)
    if collbans.count_documents({"id": member.id, "guild_id": member.guild.id}) == 0:
        collbans.insert_one(ban_values)


@bot.event
async def on_guild_join(guild):
    server_values = {
        "_id": guild.id,
        "case": 0
    }

    if collservers.count_documents({"_id": guild.id}) == 0:
        collservers.insert_one(server_values)


# Загружаем расширения из папки "cogs"
for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")

bot.run("MTI0MzI3ODk3MTYxODA2NjQ2Mw.G0b0Ow.ucu1wwr_RuVQzaOjwSho49-azeKRw7L05afNTM")
