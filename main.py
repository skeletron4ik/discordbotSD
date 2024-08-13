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

rules = {
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

def get_rule_info(rule_code):
    return rules.get(rule_code, rule_code)

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
                "balance": 0,
                "number_of_deal": 0,
                "message_count": 0,
                "time_in_voice": 0,
                "warns": 0,
                "reasons": [],
                "ban": 'False',
                "ban_timestamp": 0,
                "ban_reason": None,
                "number_of_roles": 0,
                "role_ids": []
            }
            server_values = {
                "_id": guild.id,
                "case": 0,
                "booster_timestamp": 0,
                "admin_booster_multiplier": 0,
                "admin_booster_activated_by": [],
                "global_booster_timestamp": 0,
                "global_booster_multiplier": 0,
                "global_booster_activated_by": [],
                "multiplier": 1
            }

            if collusers.count_documents({"id": member.id, "guild_id": guild.id}) == 0:
                collusers.insert_one(values)
            if collservers.count_documents({"_id": guild.id}) == 0:
                collservers.insert_one(server_values)

@bot.event
async def on_member_join(member):
    values = {
        "id": member.id,
        "guild_id": member.guild.id,
        "balance": 0,
        "number_of_deal": 0,
        "message_count": 0,
        "time_in_voice": 0,
        "warns": 0,
        "reasons": [],
        "ban": 'False',
        "ban_timestamp": 0,
        "ban_reason": None,
        "number_of_roles": 0,
        "role_ids": []
    }

    if collusers.count_documents({"id": member.id, "guild_id": member.guild.id}) == 0:
        collusers.insert_one(values)

@bot.event
async def on_guild_join(guild):
    server_values = {
        "_id": guild.id,
        "case": 0,
        "booster_timestamp": 0,
        "admin_booster_multiplier": 0,
        "admin_booster_activated_by": [],
        "global_booster_timestamp": 0,
        "global_booster_multiplier": 0,
        "global_booster_activated_by": [],
        "multiplier": 1
    }

    if collservers.count_documents({"_id": guild.id}) == 0:
        collservers.insert_one(server_values)

# Загружаем расширения из папки "cogs"
for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")

bot.run("MTI0MzI3ODk3MTYxODA2NjQ2Mw.G0b0Ow.ucu1wwr_RuVQzaOjwSho49-azeKRw7L05afNTM")
