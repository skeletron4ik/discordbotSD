import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans

class BansCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_ban.start()

    @tasks.loop(seconds=210)
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
                    iconurl = await self.bot.fetch_guild(guild_id)
                    iconurlz = iconurl.icon_url
                    embed = disnake.Embed(
                        title="ShadowDragons",
                        url="https://discord.com/invite/KE3psXf",
                        description="",
                        color=0x00ff40
                    )
                    embed.set_author(name='Вы были разблокированы!', icon_url=iconurlz)
                    embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                    embed.add_field(
                        name="",
                        value="Срок Вашего бана истёк!",
                        inline=False
                    )
                    embed.set_footer(text="Больше не нарушайте!")

                    if member:
                        await member.send(embed=embed)

                    channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи
                    участник = await self.bot.fetch_user(member_id)
                    embed = disnake.Embed(title="Участник был разбанен!",
                                          description=f"Срок бана участника **{участник}** ({участник.mention}) истек!",
                                          colour=0x00ff40,
                                          timestamp=datetime.now())
                    embed.set_author(name='Участник разблокирован',icon_url=iconurlz)
                    embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                    embed.set_footer(text="Разбан")
                    await channel.send(embed=embed)

    @check_ban.before_loop
    async def before_check_warns(self):
        await self.bot.wait_until_ready()

    def get_rule_info(self, причина):
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
        return rules.get(причина, причина)

    def format_duration(self, time_str):
        try:
            value = int(time_str[:-1])
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")

        unit = time_str[-1]
        if unit == 'д' or unit == 'd':
            if value == 1:
                return "1 день"
            elif 2 <= value <= 4:
                return f"{value} дня"
            else:
                return f"{value} дней"
        elif unit == 'ч' or unit == 'h':
            if value == 1:
                return "1 час"
            elif 2 <= value <= 4:
                return f"{value} часа"
            else:
                return f"{value} часов"
        elif unit == 'м' or unit == 'm':
            if value == 1:
                return "1 минуту"
            elif 2 <= value <= 4:
                return f"{value} минуты"
            else:
                return f"{value} минут"
        elif unit == 'с' or unit == 's':
            if value == 1:
                return "1 секунду"
            elif 2 <= value <= 4:
                return f"{value} секунды"
            else:
                return f"{value} секунд"
        else:
            raise ValueError(f"Invalid time unit: {unit}")

    def convert_to_seconds(self, time_str):
        try:
            value = int(time_str[:-1])
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")

        unit = time_str[-1]
        if unit == 'д' or unit == 'd':
            return value * 24 * 60 * 60
        elif unit == 'ч' or unit == 'h':
            return value * 60 * 60
        elif unit == 'м' or unit == 'm':
            return value * 60
        elif unit == 'с' or unit == 's':
            return value
        else:
            raise ValueError(f"Invalid time unit: {unit}")

    @commands.slash_command(name="ban", description="Блокирует доступ к серверу")
    async def ban(self, inter: disnake.GuildCommandInteraction, участник: disnake.Member, длительность: str, причина="Не указана"):
        if inter.type == disnake.InteractionType.application_command:
            await inter.response.defer()
            причина = self.get_rule_info(причина)

            try:
                formatted_duration = self.format_duration(длительность)
                value = self.convert_to_seconds(длительность)
            except ValueError as e:
                embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
                embed.add_field(name=f'Ошибка',
                                value=f'Ошибка: {e}\n Длительность указывается в:\n ``д/d-дни, ч/h-часы, м/m-минуты, с/s-секунды``')
                embed.set_thumbnail(url="https://i.imgur.com/o95uhru.gif")
                embed.set_footer(text='Ошибка')
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            role = inter.guild.get_role(1229075137374978119)
            channel = inter.guild.get_channel(1042818334644768871)
            current_timestamp = int(datetime.now().timestamp() + value)
            cur = int(datetime.now().timestamp())

            query = {'id': участник.id, 'guild_id': inter.guild.id}
            update = {'$set': {'ban': 'True', 'Timestamp': current_timestamp, 'reason': причина}}

            collbans.update_one(query, update)

            if участник.voice is not None and участник.voice.channel is not None:
                await участник.move_to(None)

            await участник.add_roles(role, reason=причина)
            embed = disnake.Embed(
                description=f"Участник {участник.mention} был забанен на ``{formatted_duration}``\n Причина: **{причина}**.",
                colour=0xff0000,
                timestamp=datetime.now())

            embed.set_author(name=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")

            embed.set_thumbnail(
                url="https://media1.giphy.com/media/tMf6IV7q9m3pbKPybv/giphy.gif?cid=6c09b952x9el5v0keemitb9f7pe09b04fetyq2ft84dhizs1&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=s")

            embed.set_footer(text="Бан")
            await inter.response.send_message(embed=embed)
        else:
            await inter.response.send_message('Интеракция не поддерживается!')

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="", color=0xff0000, timestamp=datetime.now())
        embed.set_author(name="Вы были заблокированы!", icon_url=inter.guild.icon_url)
        embed.set_thumbnail(url="https://media1.giphy.com/media/tMf6IV7q9m3pbKPybv/giphy.gif?cid=6c09b952x9el5v0keemitb9f7pe09b04fetyq2ft84dhizs1&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=s")
        embed.add_field(name="", value=f"Вы были забанены на сервере **{inter.guild.name}**!",
                        inline=False)
        embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
        embed.add_field(name="Причина:", value=причина, inline=False)
        embed.add_field(name="Истекает через:", value=f"<t:{current_timestamp}:R>", inline=False)
        embed.add_field(name="Подать апелляцию:", value=f"<#1044571685900259389>", inline=False)
        embed.set_footer(text="Пожалуйста, будьте внимательны!")
        await участник.send(embed=embed)

        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

        embed = disnake.Embed(title="", url="",
                              description="", color=0xff0000, timestamp=datetime.now())
        embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был забанен!",
                        inline=False)
        embed.set_thumbnail(url="https://media1.giphy.com/media/tMf6IV7q9m3pbKPybv/giphy.gif?cid=6c09b952x9el5v0keemitb9f7pe09b04fetyq2ft84dhizs1&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=s")
        embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
        embed.add_field(name="Участник:", value=f"*{участник}* ({участник.mention})", inline=True)
        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
        embed.add_field(name="Время:", value=f"{formatted_duration} (<t:{current_timestamp}:R>)", inline=True)
        embed.add_field(name="Причина:", value=причина, inline=True)
        embed.set_footer(text=f"ID участника: {участник.id}")
        await channel.send(embed=embed)

    @commands.slash_command(name='unban', description='Позволяет снять блокировку с пользователя.')
    async def unban(self, inter: disnake.GuildCommandInteraction, участник: disnake.Member):
        bans = collbans.find_one({'id': участник.id, 'guild_id': inter.guild.id})['ban']
        if bans == 'False':
            embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
            embed.add_field(name=f'Ошибка',
                            value=f'Участник сервера **{участник.mention}** не находится в блокировке.')
            embed.set_thumbnail(url="https://i.imgur.com/o95uhru.gif")
            embed.set_footer(text="Ошибка")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        query = {'id': участник.id, 'guild_id': inter.guild.id}
        task = {'$set': {'ban': False, 'Timestamp': 0, 'reason': None}}
        collbans.update_one(query, task)
        await участник.remove_roles(inter.guild.get_role(1229075137374978119))
        embed = disnake.Embed(
            description=f"Участник {участник.mention} был разбанен.",
            colour=0x00ff40,
            timestamp=datetime.now())

        embed.set_author(name=f"{inter.author.name}",
                         icon_url=f"{inter.author.avatar}")

        embed.set_thumbnail(
            url="https://www.emojiall.com/images/240/telegram/2705.gif")

        embed.set_footer(text="Разбан")
        await inter.response.send_message(embed=embed)

        embed = disnake.Embed(title="ShadowDragons",
                              url="https://discord.com/invite/KE3psXf",
                              description="",
                              colour=0x00ff40,
                              timestamp=datetime.now())

        embed.set_author(name="Вы были разбанены!",
                         icon_url=inter.guild.icon_url)

        embed.add_field(name="",
                        value=f"Блокировка на сервере **{inter.guild.name}** была снята\n **Модератором**: {inter.author.mention}!",
                        inline=False)
        embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
        embed.set_footer(text="Приносим извинения за предоствленые неудобства!")

        await участник.send(embed=embed)

        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

        embed = disnake.Embed(title="", url="",
                              description="", color=0x00ff40, timestamp=datetime.now())
        embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был разбанен!",
                        inline=False)
        embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
        embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
        embed.add_field(name="Участник:", value=f"*{участник}* ({участник.mention})", inline=True)
        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
        embed.set_footer(text=f"ID участника: {участник.id}")
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(BansCog(bot))
    print("BansCog is ready")
