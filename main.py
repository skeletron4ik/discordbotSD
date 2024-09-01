import disnake
from pymongo import MongoClient, errors
from disnake.ext import commands
from datetime import datetime
import os
import asyncio
import time
from dotenv import load_dotenv
import sys
from disnake.errors import HTTPException
from disnake.utils import format_dt


load_dotenv()
bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all(), reload=True)
bot.member_cache_flags = disnake.MemberCacheFlags.all()
cluster = MongoClient(os.getenv('MONGODB'))
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

async def safe_api_call(api_function, *args, **kwargs):
    try:
        return await api_function(*args, **kwargs)
    except HTTPException as e:
        if e.status == 429:
            retry_after = int(e.response.headers.get("Retry-After", 5))  # Задержка по умолчанию 5 секунд
            await asyncio.sleep(retry_after)
            return await safe_api_call(api_function, *args, **kwargs)
        else:
            raise

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds_remaining = round(error.retry_after)
        # Создаем Embed сообщение для кулдауна
        embed = disnake.Embed(
            title="Подождите немного!",
            description=f"Эта команда находится в кулдауне. Попробуйте снова через **{seconds_remaining} секунд.**",
            color=0xff0000, timestamp=datetime.now()
        )
        embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
        await inter.response.send_message(embed=embed, ephemeral=True)
    else:
        # Обработка других ошибок (опционально)
        embed = disnake.Embed(
            title="Ошибка!",
            description="Произошла ошибка при выполнении команды. Попробуйте снова.",
            color=0xff0000, timestamp=datetime.now()
        )
        embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
        await inter.response.send_message(embed=embed, ephemeral=True)
        # Логирование ошибки в консоль
        raise error

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!\nID: {bot.user.id}")
    for guild in bot.guilds:
        for member in guild.members:
            values = {
                "id": member.id,
                "guild_id": guild.id,
                "nickname": member.display_name,  # Store initial nickname
                "user_name": member.name,  # Store actual username
                "balance": 0,
                "reputation": 0,  # Новое поле для репутации
                "reaction_count": 0,  # Поле для отслеживания количества реакций пользователя
                "number_of_deal": 0,
                "message_count": 0,
                "time_in_voice": 0,
                "warns": 0,
                "reasons": [],
                "ban": 'False',
                "ban_timestamp": 0,
                "ban_reason": None,
                "number_of_roles": 0,
                "role_ids": [],
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
async def on_member_update(before, after):
    updates = {}
    if before.display_name != after.display_name:
        updates["nickname"] = after.display_name
    if before.name != after.name:
        updates["user_name"] = after.name

    if updates:
        collusers.update_one(
            {"id": after.id, "guild_id": after.guild.id},
            {"$set": updates}
        )


@bot.event
async def on_member_join(member):
    values = {
        "id": member.id,
        "guild_id": member.guild.id,
        "nickname": member.display_name,
        "user_name": member.name,
        "balance": 0,
        "reputation": 0,
        "reaction_count": 0,
        "number_of_deal": 0,
        "message_count": 0,
        "time_in_voice": 0,
        "warns": 0,
        "reasons": [],
        "ban": 'False',
        "ban_timestamp": 0,
        "ban_reason": None,
        "number_of_roles": 0,
        "role_ids": [],
    }

    if collusers.count_documents({"id": member.id, "guild_id": member.guild.id}) == 0:
        collusers.insert_one(values)

    # Отправка приветственного эмбед-сообщения
    channel = member.guild.get_channel(1279702475095412808)
    if channel:
        embed = disnake.Embed(
            title="Новый участник!",
            description=f"{member.display_name} ({member.mention}) присоединился на сервер.",
            color=disnake.Color.green(),
            timestamp=datetime.now()
        )
        # Используем относительное время для даты создания аккаунта
        embed.add_field(
            name="Дата регистрации аккаунта:",
            value=f"{format_dt(member.created_at, style='R')}",
            inline=False
        )
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(1279702475095412808)
    if channel:
        embed = disnake.Embed(
            title="Участник покинул сервер",
            description=f"{member.display_name} ({member.mention}) покинул сервер.",
            color=disnake.Color.red(),
            timestamp=datetime.now()
        )
        # Используем относительное время для даты присоединения к серверу
        embed.add_field(
            name="Дата присоединения к серверу:",
            value=f"{format_dt(member.joined_at, style='R')}",
            inline=False
        )
        await channel.send(embed=embed)


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

try:
    bot.run(os.getenv('TOKEN'))
except disnake.errors.HTTPException:
    print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
    sys("python main.py")
    sys('kill 1')
