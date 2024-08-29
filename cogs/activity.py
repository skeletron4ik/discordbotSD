import disnake
from pymongo import MongoClient, errors
from disnake.ext import commands, tasks
import os
import asyncio
import time
from disnake import RawReactionActionEvent
import datetime
import disnake
from datetime import datetime, timedelta
from main import cluster

collusers = cluster.server.users
collservers = cluster.server.servers


class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_count = {}
        self.update_leaderboard.start()
        self.rep_up_id = 1234218072433365102
        self.rep_down_id = 1234218095116288154
        self.reaction_limit = 10  # Лимит реакций в месяц для каждого участника

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

    async def update_reputation(self, user_id, guild_id, amount):
        collusers.update_one(
            {"id": user_id, "guild_id": guild_id},
            {"$inc": {"reputation": amount}}
        )

    async def check_reaction_limit(self, user_id, guild_id):
        # Проверка лимита реакций для конкретного пользователя
        user_data = collusers.find_one({"id": user_id, "guild_id": guild_id})
        if not user_data:
            return False

        if user_data.get("reaction_count", 0) >= self.reaction_limit:
            return True
        return False

    async def increment_reaction_count(self, user_id, guild_id):
        collusers.update_one(
            {"id": user_id, "guild_id": guild_id},
            {"$inc": {"reaction_count": 1}}
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.emoji.id not in [self.rep_up_id, self.rep_down_id]:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author_id = message.author.id  # ID автора сообщения (точно не чат гпт в переписке)
        guild_id = payload.guild_id
        user_id = payload.user_id  # ID пользователя, который поставил реакцию

        guild = self.bot.get_guild(guild_id)
        author = guild.get_member(author_id)
        user = guild.get_member(user_id)

        # Проверка лимита реакций для данного пользователя
        if await self.check_reaction_limit(user_id, guild_id):
            await message.remove_reaction(payload.emoji, payload.member)
            return

        await self.increment_reaction_count(user_id, guild_id)

        if payload.emoji.id == self.rep_up_id:
            await self.update_reputation(author_id, guild_id, 1)  # Изменяем репутацию автора сообщения
            collusers.find_one_and_update({'id': author.id, 'guild_id': guild.id},
                                          {'$set': {'last_reputation': user.id}})
        elif payload.emoji.id == self.rep_down_id:
            await self.update_reputation(author_id, guild_id, -1)  # Изменяем репутацию автора сообщения

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if payload.emoji.id not in [self.rep_up_id, self.rep_down_id]:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author_id = message.author.id  # ID автора сообщения
        guild_id = payload.guild_id
        if await self.check_reaction_limit(payload.user_id, guild_id):
            return
        if payload.emoji.id == self.rep_up_id:
            await self.update_reputation(author_id, guild_id, -1)  # Возвращаем репутацию автора сообщения
        elif payload.emoji.id == self.rep_down_id:
            await self.update_reputation(author_id, guild_id, 1)  # Возвращаем репутацию автора сообщения

    @commands.slash_command(name='reputation', description='Репутация')
    async def reputation(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        if disnake.InteractionResponse:
            await inter.response.defer(ephemeral=True)
        if member is None:
            member = inter.author
        rep = collusers.find_one({'id': member.id, 'guild_id': inter.guild.id})['reputation']
        if collusers.count_documents({'id': inter.author.id, 'guild_id': inter.guild.id}) == 0:
            last_rep = collusers.find_one({'id': member.id, 'guild_id': inter.guild.id})['last_reputation']
            last_rep = inter.guild.get_member(last_rep)
            last_rep = last_rep.display_name
        else:
            last_rep = 'Нет'
        embed = disnake.Embed(
            title="Репутация пользователя",
            description=f"Информация о репутации для {member.mention}",
            color=disnake.Color.blue()  # Цвет полосы слева
        )

        embed.set_thumbnail(url=member.avatar.url)  # Установка аватарки пользователя

        embed.add_field(name="Пользователь", value=member.display_name, inline=True)
        embed.add_field(name="Репутация", value=f"⭐ {rep}", inline=True)

        embed.add_field(name="\u200B", value="\u200B")  # Пустое поле для разделения
        embed.add_field(
            name="Последняя полученная репутация",
            value=f"⭐ {last_rep}",
            inline=False
        )

        embed.set_footer(text="Используйте эмодзи для управления репутацией")

        await inter.edit_original_message(embed=embed)



def setup(bot):
    bot.add_cog(ActivityCog(bot))
    print("ActivityCog is ready")
