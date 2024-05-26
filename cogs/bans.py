import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient

current_datetime = datetime.today()

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans

class BansCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_ban.start()  # Запуск циклической задачи при инициализации

    @tasks.loop(seconds=70)  # Проверка каждые 15 секунд
    async def check_ban(self):
        current_timestamp = int(datetime.now().timestamp())
        expired_roles = collbans.find({"Timestamp": {"$lte": current_timestamp}})

        for user_data in expired_roles:
            guild_id = user_data["guild_id"]
            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
            member_id = user_data["id"]
            if collbans.find_one({'id': member_id, 'guild_id': guild_id})["ban"] == "True":
                member = guild.get_member(member_id) or await guild.fetch_member(member_id)
                role = guild.get_role(1229075137374978119)
                if role in member.roles:
                        await member.remove_roles(role)
                        collbans.update_one({"id": member_id, "guild_id": guild_id}, {"$set": {'Timestamp': 0, 'ban': 'False'}})
                        embed = disnake.Embed(
                            title="ShadowDragons",
                            url="https://discord.com/invite/KE3psXf",
                            description="**Модерация**",
                            color=0xffff00
                        )
                        embed.add_field(
                            name="Вы были разблокированы:",
                            value="Срок Вашего бана истёк!",
                            inline=False
                        )
                        embed.set_footer(text="Больше не нарушайте!")

                        if member:
                            await member.send(embed=embed)

    @check_ban.before_loop
    async def before_check_warns(self):
        await self.bot.wait_until_ready()  # Ожидание готовности бота перед запуском цикла





    @commands.slash_command(name="ban", description="Блокирует доступ к серверу")
    async def ban(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, длительность: str,
                  причина="Причина не указана."):

        def convert_to_seconds(time_str):
            try:
                value = int(time_str[:-1])  # Получаем числовое значение без последнего символа
            except ValueError:
                raise ValueError("fxck")

            unit = time_str[-1]

            if unit == 'д' or unit =='d':
                return value * 24 * 60 * 60  # Конвертируем дни в секунды
            elif unit == 'ч' or unit =='h':
                return value * 60 * 60  # Конвертируем часы в секунды
            elif unit == 'м' or unit == 'm':
                return value * 60  # Конвертируем минуты в секунды
            elif unit == 'с' or unit =='s':
                return value  # Секунды остаются без изменений
            else:
                raise ValueError("fxck")

        if inter.response.is_done():
            return
        try:
            await inter.response.defer()
        except disnake.NotFound:
            return
        value = convert_to_seconds(длительность)
        if value == 'fxck':
            await inter.send('Произошла ошибка в конвертации.', ephemeral=True)
            return
        role = inter.guild.get_role(1229075137374978119)
        channel = inter.guild.get_channel(1042818334644768871)
        current_timestamp = int(datetime.now().timestamp() + value)
        cur = int(datetime.now().timestamp())

        print(f'{cur} | {current_timestamp} | {value}')

        query = {'id': участник.id, 'guild_id': inter.guild.id}
        update = {'$set': {'ban': 'True', 'Timestamp': current_timestamp, 'reason': причина}} # Что обновляем метод $set т.е. устанавливаем значение

        collbans.update_one(query, update)

        if участник.voice is not None and участник.voice.channel is not None:
            await участник.move_to(None)

        await участник.add_roles(role, reason=причина)

        embed = disnake.Embed(title="ShadowDragons",
                              url="https://discord.com/invite/KE3psXf",
                              description="**Модерация**", color=0xff0000)
        embed.set_author(name=f"Участник был заблокирован!")
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
        embed.add_field(name="Нарушитель:", value=f"{участник.mention}", inline=True)
        embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=True)
        embed.add_field(name="Причина:", value=причина, inline=False)
        embed.add_field(name="Истекает через:", value=f"<t:{current_timestamp}:R>", inline=False)
        embed.set_footer(text=f"ID участника: {участник.id} ' • ' {current_datetime}")
        await inter.send(embed=embed)

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="**Модерация**", color=0xff0000)
        embed.set_author(name=f"Вы были заблокированы!")
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
        embed.add_field(name="", value=f"Вы были забанены на сервере {inter.guild.name}!",
                        inline=False)
        embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
        embed.add_field(name="Причина:", value=причина, inline=False)
        embed.add_field(name="Истекает через:", value=f"<t:{current_timestamp}:R>", inline=False)
        embed.set_footer(
            text="Пожалуйста, будьте внимательны!")
        message = await участник.send(embed=embed)

        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="**Модерация**", color=0xff0000)
        embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был забанен!",
                        inline=False)
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
        embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
        embed.add_field(name="Время:", value=f"{длительность} (<t:{current_timestamp}:R>)", inline=True)
        embed.add_field(name="Причина:", value=причина, inline=True)
        embed.set_footer(text=f"ID участника: {участник.id} \' • \' {current_datetime}")
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(BansCog(bot))
    print("ready")