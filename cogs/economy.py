import disnake
from pymongo import MongoClient, errors
from disnake.ext import commands
from datetime import datetime, timedelta
import os
import asyncio
import time
import random
import math

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers
cooldowns = {}


def format_duration(value):
    if value == 1:
        return "1 румбик"
    elif 2 <= value <= 4:
        return f"`{value}` румбика"
    else:
        return f"`{value}` румбиков"


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        now = datetime.now()
        user_id = message.author.id
        if len(message.content) > 3:

            if user_id in cooldowns:
                last_used = cooldowns[user_id]
                if now - last_used < timedelta(minutes=1):
                    time_left = timedelta(minutes=1) - (now - last_used)
                    return

            money_to_give = random.uniform(0.1, 1)
            money_to_give = round(money_to_give, 2)
            collusers.find_one_and_update({'id': message.author.id}, {'$inc': {'balance': money_to_give}})

            cooldowns[user_id] = now
            print(money_to_give)

    @commands.slash_command(name='balance', description='Показывает баланс игрока', aliases=['баланс'])
    async def balance(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        await inter.response.defer()
        if member is None:
            member = inter.author
        embed = disnake.Embed(title=f'Информация о пользователе `{member.display_name}`', color=0x4169E1)

        if member is None:
            embed.timestamp = datetime.now()
            member = inter.author
            balance = collusers.find_one({"id": member.id})['balance']
            num_of_deals = collusers.find_one({'id': member.id})['number_of_deal']
            balance = round(balance, 2)
            balance = format_duration(balance)

            embed.add_field(name='Баланс:', value=f'{balance}', inline=True)
            embed.add_field(name='Количество сделок: ',value=f'`{num_of_deals}`', inline=True)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar.url)
            await inter.edit_original_response(embed=embed)
        else:
            embed.timestamp = datetime.now()
            balance = collusers.find_one({"id": member.id})['balance']
            num_of_deals = collusers.find_one({'id': member.id})['number_of_deal']
            balance = round(balance, 2)
            balance = format_duration(balance)

            embed.add_field(name='Баланс:', value=f'{balance}', inline=True)
            embed.add_field(name='Количество сделок: ', value=f'`{num_of_deals}`', inline=True)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar.url)
            await inter.edit_original_response(embed=embed)

    @commands.slash_command(name='transfer', description='Перевод румбиков участнику.', aliases=['перевод', 'give'])
    async def transfer(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, количество: int):
        if disnake.InteractionResponse:
            await inter.response.defer()
        balance = collusers.find_one({"id": inter.author.id})['balance']

        if balance > количество:
            collusers.find_one_and_update({'id': inter.author.id}, {"$inc": {"balance": -количество}})
            collusers.find_one_and_update({'id': member.id}, {"$inc": {"balance": количество}})
            collusers.find_one_and_update({'id': member.id}, {'$inc': {'number_of_deal': 1}})
            collusers.update_many({'id': inter.author.id}, {'$inc': {'number_of_deal': 1}})

            количество = format_duration(количество)

            embed = disnake.Embed(title=f'Сделка `{inter.author.display_name}` и `{member.display_name}`', color=0x4169E1)
            embed.set_author(name=f'Отправитель: {inter.author.display_name}', icon_url=inter.author.avatar.url)
            embed.add_field(name=f'Отправитель', value=f'`{inter.author.display_name}`', inline=True)
            embed.add_field(name=f'Получатель:', value=f'`{member.display_name}`', inline=True)
            embed.add_field(name=f'Сумма сделки:', value=f'{количество}', inline=False)
            embed.set_footer(text=f'Получатель: {member.name}', icon_url=member.avatar.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)

        else:
            unformatted = int(количество) - balance
            formatted = format_duration(unformatted)
            embed = disnake.Embed(title='Произошла ошибка', color=0x4169E1)
            embed.add_field(name=f'Отправитель', value=f'`{inter.author.display_name}`', inline=True)
            embed.add_field(name=f'Получатель:', value=f'`{member.display_name}`', inline=True)
            embed.add_field(name=f'Сумма сделки:', value=f'`{количество}`', inline=False)
            embed.add_field(name=f'Причина возникновения ошибки:', value=f'У отправителя не хватает {formatted}.',
                            inline=False)
            embed.set_footer(text=f'Использовал комманду: {inter.author.name}', icon_url=inter.author.avatar.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)

    @commands.slash_command(name='givemoney')
    async def givemoney(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, количество: int):
        member = участник
        collusers.find_one_and_update({'id': member.id}, {'$inc': {'balance': количество}})

        await inter.response.send_message('сделано', ephemeral=True)


def setup(bot):
    bot.add_cog(EconomyCog(bot))
    print("Economy is ready")
