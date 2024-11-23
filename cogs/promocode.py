import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
from main import rules, get_rule_info  # Список правил
from main import cluster
from ai.process_role import process_role

collpromos = cluster.server.promos
collusers = cluster.server.users
collservers = cluster.server.servers


class Promo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='promo')
    async def promo(self, inter):
        pass

    @promo.sub_command(name='create_role')
    async def create_role(self, inter, название: str, роль: disnake.Role, количество: int, длительность: int):
        # First update
        collpromos.update_one(
            {'_id': inter.guild.id},
            {'$set': {f'promos.{название}': {}}},
            upsert=True
        )

        # Second update
        collpromos.update_one(
            {'_id': inter.guild.id},
            {
                '$set': {
                    f'promos.{название}.role_id': роль.id,
                    f'promos.{название}.type': 'role',
                    f'promos.{название}.activations': количество,
                    f'promos.{название}.on_time': длительность,
                    f'promos.{название}.create_id': inter.author.id,
                    f'promos.{название}.users': []
                }
            },
            upsert=True
        )

        await inter.response.send_message('get pupped')

    @promo.sub_command(name='create_money')
    async def create_money(self, inter, название: str, количество_румбиков: int, количество_активаций: int):
        # First update
        collpromos.update_one(
            {'_id': inter.guild.id},
            {'$set': {f'promos.{название}': {}}},
            upsert=True
        )

        # Second update
        collpromos.update_one(
            {'_id': inter.guild.id},
            {
                '$set': {
                    f'promos.{название}.money': количество_румбиков,
                    f'promos.{название}.type': 'money',
                    f'promos.{название}.activations': количество_активаций,
                    f'promos.{название}.create_id': inter.author.id,
                    f'promos.{название}.users': []
                }
            },
            upsert=True
        )

        await inter.response.send_message('get pupped')

    @promo.sub_command(name='use')
    async def use(self, inter, код: str):
        await inter.response.defer(ephemeral=True)
        result = collpromos.find_one(
            {'_id': inter.guild.id, f'promos.{код}': {'$exists': True}}
        )
        if not result:
            await inter.edit_original_response('Кода не существует')
            return

        exists = collpromos.find_one(
            {'_id': inter.guild.id, f'promos.{код}.users.id': inter.author.id}
        )

        if exists:
            await inter.edit_original_response('Вы уже активировали промик')
            return

        type = collpromos.find_one({'_id': inter.guild.id})['promos'][код]['type']

        if type == 'money':
            money = collpromos.find_one({'_id': inter.guild.id})['promos'][код]['money']
            collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': money}})
            collpromos.update_one({'_id': inter.guild.id}, {'$push': {f'promos.{код}.users': {'id': inter.author.id}}})

            collpromos.update_one(
                {'_id': inter.guild.id},
                {'$inc': {f'promos.{код}.activations': -1}},
                upsert=True
            )

            if collpromos.find_one({'_id': inter.guild.id})['promos'][код]['activations'] <= 0:
                collpromos.update_one(
                    {'_id': inter.guild.id},  # Фильтр по _id
                    {'$unset': {f'promos.{код}': 1}}  # Удаление вложенного поля
                )

            await inter.edit_original_response(f'get pupped + {money}')
        elif type == 'role':
            role_id = collpromos.find_one({'_id': inter.guild.id})['promos'][код]['role_id']
            role = inter.guild.get_role(role_id)
            on_time = collpromos.find_one({'_id': inter.guild.id})['promos'][код]['on_time']
            collpromos.update_one({'_id': inter.guild.id}, {'$push': {f'promos.{код}.users': {'id': inter.author.id}}})

            collpromos.update_one(
                {'_id': inter.guild.id},
                {'$inc': {f'promos.{код}.activations': -1}},
                upsert=True
            )

            if collpromos.find_one({'_id': inter.guild.id})['promos'][код]['activations'] <= 0:
                collpromos.update_one(
                    {'_id': inter.guild.id},  # Фильтр по _id
                    {'$unset': {f'promos.{код}': 1}}  # Удаление вложенного поля
                )

            await process_role(inter, self.bot, 0, on_time, role_id, ephemeral=True)
            await inter.edit_original_response(f'get pupped + {role_id}')

def setup(bot):
    bot.add_cog(Promo(bot))
    print("PromoCog is ready")
