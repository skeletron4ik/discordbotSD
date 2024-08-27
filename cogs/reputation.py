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

cooldowns = {}

class RepCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: disnake.RawReactionActionEvent):
        guild = self.bot.get_guild(reaction.guild_id)
        message = self.bot.get_message(reaction.message_id)
        user = self.bot.get_user(reaction.user_id)
        up_emoji = disnake.utils.get(guild.emojis, name='rep_up')
        down_emoji = disnake.utils.get(guild.emojis, name='rep_down')
        now = datetime.now()
        print('3')
        if user.bot:
            await message.clear_reactions()
            print('5')
            return
        if message.author.id == user.id:
            await message.clear_reactions()
            print('2')
            return

        if user.id in cooldowns:
            last_used = cooldowns[user.id]
            if now - last_used < timedelta(minutes=1):
                timeleft = timedelta(minutes=1) - (now - last_used)
                print(timeleft)
                await message.remove_reaction(up_emoji, user.id)
                await message.remove_reaction(down_emoji, user.id)
                return
        if reaction.emoji.id == 1234218072433365102:
            print('here')
            collusers.find_one_and_update({'id': message.author.id, 'guild_id': guild.id},
                                          {'$inc': {'reputation': 1}})
            collusers.find_one_and_update({'id': message.author.id, 'guild_id': guild.id},
                                          {'$set': {'last_reputation': user.id}})
        elif reaction.emoji.id == 1234218095116288154:
            print('here 2')
            collusers.find_one_and_update({'id': message.author.id, 'guild_id': guild.id},
                                          {'$inc': {'reputation': -1}})
        else:
            print('xuyna')


    @commands.slash_command(name='reputation', description='Репутация')
    async def reputation(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        if disnake.InteractionNotResponded:
            await inter.response.defer(ephemeral=True)
        if member is None:
            member = inter.author
        rep = collusers.find_one({'id': member.id, 'guild_id': inter.guild.id})['reputation']
        if collusers.count_documents({'id': inter.author.id, 'guild_id': inter.guild.id}) == 0:
            last_rep = collusers.find_one({'id': member.id, 'guild_id': inter.guild.id})['last_reputation']
            last_rep = inter.guild.get_member(last_rep)
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
    bot.add_cog(RepCog(bot))
    print('RepCog is Ready')
