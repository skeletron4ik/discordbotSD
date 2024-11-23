import disnake
from disnake.ext import commands
import random
from pymongo import MongoClient, errors, collection
from main import cluster
from datetime import datetime, timedelta
from ai.process_role import process_role
import asyncio

last_spin_times = {}

collusers = cluster.server.users
collservers = cluster.server.servers


def check_value(inter):
    result = collusers.update_one(
        {"id": inter.author.id, "guild_id": inter.guild.id, "tries": {"$exists": False}},
        {"$set": {"tries": 0}}  # Значение для поля age
    )


def format_duration(value):
    if value == 1:
        return "1 румбик"
    elif 2 <= value <= 4:
        return f"`{value}` румбика"
    else:
        return f"`{value}` румбиков"


def create_error_embed(message: str) -> disnake.Embed:
    embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
    embed.add_field(name='Произошла ошибка', value=f'Ошибка: {message}')
    embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
    embed.set_footer(text='Ошибка')
    return embed


emoji = "<a:rumbick_gif:1276856664842047518>"


class RouletteCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.allowed_channel_id = 1279413707981455422

    @commands.slash_command(
        name="roulette",
        description="Игра в рулетку"
    )
    async def roulette(self, inter):
        pass

    @roulette.sub_command(name='buy', description='Купить крутку')
    async def buy(self, inter):

        check_value(inter)

        balance = collusers.find_one({'id': inter.author.id, 'guild_id': inter.author.guild.id})['balance']

        if balance < 49:
            nomoney = format_duration(49 - balance)
            embed = create_error_embed(f'Вам не хватает {nomoney}.')
            await inter.response.edit_original_response(embed=embed)
            return

        collusers.find_one_and_update({'id': inter.author.id, 'guild_id': inter.author.guild.id},
                                      {'$inc': {'balance': -49}})

        collusers.find_one_and_update({'id': inter.author.id, 'guild_id': inter.author.guild.id},
                                      {'$inc': {'tries': 1}})

        embed = disnake.Embed(
            description=f"**Вы приобрели крутку, которая используется по команде `/roulette start`.",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        embed.set_author(name="Вы успешно приобрели крутку!",
                         icon_url="https://i.imgur.com/vlX2dxG.gif")
        embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
        embed.set_footer(text="Покупка прошла успешно",
                         icon_url=inter.guild.icon.url)
        await inter.send(embed=embed, ephemeral=True)

    @roulette.sub_command(name='tries', description='Количество круток')
    async def tries(self, inter: disnake.ApplicationCommandInteraction):

        check_value(inter)

        tries = collusers.find_one({'id': inter.author.id, 'guild_id': inter.author.guild.id})['tries']
        await inter.send(f'Ваши крутки: {tries}')

    @roulette.sub_command(namee='start', description='Прокрутить рулетку')
    async def start(self, inter: disnake.ApplicationCommandInteraction):

        check_value(inter)

        if collusers.find_one({'id': inter.author.id, 'guild_id': inter.author.guild.id})['tries'] <= 0:
            await inter.send('У Вас нет попыток.')
            return

        roulette_options = [
            {'name': 'Мут на 10 минут 🔇', 'chance': 5, 'field': 'mute', 'value': 10},
            {'name': f'20 💰', 'chance': 0, 'field': 'currency', 'value': 20},
            {'name': f'50 💰', 'chance': 0, 'field': 'currency', 'value': 50},
            {'name': 'Gold на 1 день ⭐️', 'chance': 0, 'field': 'gold', 'value': 86400},
            {'name': 'Diamond на 1 день 💎', 'chance': 0, 'field': 'diamond', 'value': 86400},
            {'name': 'Gold на 7 дней ⭐️', 'chance': 0, 'field': 'gold', 'value': 604800},
            {'name': 'Diamond на 7 дней 💎', 'chance': 0, 'field': 'diamond', 'value': 604800},
            {'name': f'100 💰', 'chance': 0, 'field': 'currency', 'value': 100},
            {'name': 'Gold на 30 дней ⭐️', 'chance': 0, 'field': 'gold', 'value': 2592000},
            {'name': 'Diamond на 30 дней 💎', 'chance': 0, 'field': 'diamond', 'value': 2592000},
            {'name': f'500 💰', 'chance': 0, 'field': 'currency', 'value': 500},
            {'name': f'1000 💰', 'chance': 0, 'field': 'currency', 'value': 1000},
            {'name': 'Gold навсегда ⭐️', 'chance': 95, 'field': 'gold', 'value': 2592000000},
        ]
        # Создаём взвешенный список элементов
        weighted_items = []
        for option in roulette_options:
            weighted_items.extend([option] * option['chance'])

        # Если шансы всех элементов равны 0, возвращаем None
        if not weighted_items:
            return None

        # Выбираем случайный элемент
        selected_option = random.choice(weighted_items)
        # Возвращаем все ключевые поля
        prize = {
            "name": selected_option['name'],
            "field": selected_option['field'],
            "value": selected_option['value']
        }

        # Обработка приза на основе его типа
        if prize['field'] == 'currency':
            collusers.find_one_and_update(
                {'id': inter.author.id, 'guild_id': inter.author.guild.id},
                {'$inc': {'balance': prize['value']}}
            )
        elif prize['field'] == 'gold':
            await process_role(inter, self.bot, 0, prize['value'], 1303396950481174611, ephemeral=True)
        elif prize['field'] == 'diamond':
            await process_role(inter, self.bot, 0, prize['value'], 1044314368717897868, ephemeral=True)
        elif prize['field'] == 'mute':
            try:
                dur = timedelta(minutes=prize['value'])
                print('im here')
                await inter.author.timeout(duration=dur)
            except:
                pass

        # Отправка сообщения с результатом
        await inter.send(f'Выпал: {prize["name"]}')


def setup(bot):
    bot.add_cog(RouletteCog(bot))
    print('Roulette Cog is Ready!')
