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
colltemp_roles = cluster.server.temp_roles

class WarnsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
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

    @commands.Cog.listener()
    async def on_member_unmute(self, member):
        channel_id = 944562833901899827  # ID канала, куда будет отправлено сообщение
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(f'{member.mention} был размучен и может снова говорить!')
        else:
            print(f'Канал с ID {channel_id} не найден.')

    @tasks.loop(seconds=210)  # Проверка каждые 30 секунд
    async def check_warns(self):
        # Получение текущего времени
        current_timestamp = int(datetime.now().timestamp())

        # Поиск пользователей с истекшим временем предупреждения
        expired_warns = collusers.find({"reasons.timestamp": {"$lte": current_timestamp}})

        for user in expired_warns:
            guild_id = user["guild_id"]
            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

            for reason in user["reasons"]:
                if reason["timestamp"] <= current_timestamp:
                    # Удаление истекших предупреждений из списка и обновление базы данных
                    collusers.update_one(
                        {"id": user["id"], "guild_id": user["guild_id"]},
                        {"$pull": {"reasons": {"timestamp": reason["timestamp"]}}},
                    )
                    collusers.update_one(
                        {"id": user["id"], "guild_id": user["guild_id"]},
                        {"$inc": {"warns": -1}}
                    )

                    embed = disnake.Embed(
                        title="ShadowDragons",
                        url="https://discord.com/invite/KE3psXf",
                        description="",
                        color=0x00ff40
                    )
                    embed.set_author(name=f'С Вас сняли предупреждение!', icon_url='')
                    embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                    embed.add_field(
                        name="",
                        value=f"Срок Вашего предупреждения истёк!",
                        inline=False
                    )
                    embed.set_footer(text="Больше не нарушайте!")

                    member = guild.get_member(user["id"]) or await guild.fetch_member(user["id"])
                    if member:
                        await member.send(embed=embed)

                    channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи


                    embed = disnake.Embed(title="Предупреждение участника было снято!",
                                          description=f"Срок предупреждения участника **{member.name}** ({member.mention}) истек!",
                                          colour=0x00ff40,
                                          timestamp=datetime.now())
                    embed.set_author(name='', icon_url='')
                    embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                    embed.set_footer(text="Снятие предупреждения")
                    await channel.send(embed=embed)

    def get_rule_info(self, причина):
        if причина in self.rules:
            reason = self.rules[str(причина)]
            return reason
        else:
            reason = причина
            return reason

    @check_warns.before_loop
    async def before_check_warns(self):
        await self.bot.wait_until_ready()  # Ожидание готовности бота перед запуском цикла

    @commands.slash_command(name="warn", description="Выдает предупреждение(-я).")
    async def warn(self, inter: disnake.GuildCommandInteraction, участник: disnake.Member, количество: int,
                   причина="Не указана", длительность: str = None):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer()
            except:
                return
            reason = self.get_rule_info(причина)

            if количество < 1:  # Проверка на невалидное количество
                embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
                embed.add_field(name=f'Ошибка', value=f'Введено количество меньше чем ``1``')
                embed.add_field(name="Попробуйте:",
                                value=f'В параметр `количество` указать количество больше 1', inline=False)
                embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
                embed.set_footer(text="Ошибка")
                await inter.response.send_message(embed=embed, ephemeral=True)

            # ID ролей, которые имеют иммунитет к предупреждениям
            immune_roles = [702593498901381184,  # Модератор
                            580790278697254913,  # Гл. Модератор
                            518505773022838797]  # Администратор
            admin_role = inter.guild.get_role(518505773022838797)

            # Проверка, если участник имеет иммунитетную роль и автор не администратор
            if any(role.id in immune_roles for role in участник.roles) and admin_role not in inter.author.roles:
                embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
                embed.add_field(name=f'Ошибка', value=f'Вы не можете выдать предупреждение этому участнику.')
                embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
                embed.set_footer(text="Ошибка")
                await inter.followup.send(embed=embed, ephemeral=True)
                return

            def get_warning_word(count):
                if count % 10 == 1 and count % 100 != 11:
                    return "предупреждение"
                elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
                    return "предупреждения"
                else:
                    return "предупреждений"

            def convert_to_seconds(time_str):
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
                    raise ValueError(f"Invalid time unit: {time_str[-1]}")

            def format_duration(time_str):
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
                    raise ValueError(f"Invalid time unit: {time_str[-1]}")

            warning_word = get_warning_word(количество)

            role = inter.guild.get_role(757930494301044737)
            rolediamond = inter.guild.get_role(1044314368717897868)
            moderator_role = inter.guild.get_role(702593498901381184)

            if длительность:
                try:
                    timestamp = int(datetime.now().timestamp() + convert_to_seconds(длительность))
                    HasRole = format_duration(длительность)
                except ValueError as e:
                    try:
                        await inter.edit_original_response(f"Ошибка в конвертации.")
                    except:
                        await inter.response.send_message(f"Ошибка в конвертации.", ephemeral=True)
            else:
                if role in участник.roles or rolediamond in участник.roles:
                    timestamp = int(datetime.now().timestamp() + 1728000)
                    HasRole = '20 дней'
                else:
                    timestamp = int(datetime.now().timestamp() + 2592000)
                    HasRole = '30 дней'

            warn_info = {
                "reason": reason,
                "timestamp": timestamp
            }

            collservers.update_one(
                {"_id": inter.guild.id},
                {"$inc": {"case": количество}},
                upsert=True
            )
            for i in range(количество):
                collusers.update_one(
                    {"id": участник.id, "guild_id": inter.guild.id},
                    {
                        "$inc": {"warns": 1},
                        "$push": {"reasons": warn_info}
                    },
                    upsert=True
                )

            warns_count = collusers.find_one({"id": участник.id, "guild_id": inter.guild.id})["warns"]
            server_value = collservers.find_one({"_id": inter.guild.id})["case"]

            embed = disnake.Embed(
                description=f"Участник {участник.mention} получил ``{количество}`` {warning_word} на ``{HasRole}`` (<t:{timestamp}:R>).\n Причина: **{reason}**.\n Случай: ``#{server_value}``",
                colour=0xffff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=f"{inter.author.name}",
                             icon_url=f"{inter.author.avatar}")
            embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
            embed.set_footer(text="Предупреждение")
            try:
                await inter.edit_original_response(embed=embed)
            except:
                await inter.response.send_message(embed=embed)

        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

        embed = disnake.Embed(title="", url="",
                              description="", color=0xffff00, timestamp=datetime.now())
        embed.add_field(name="", value=f"Участник **{участник.name}** ({участник.mention}) получил ``{количество}`` {warning_word}",
                        inline=False)
        embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
        embed.add_field(name="Модератор:", value=f"**{inter.author.name}** ({inter.author.mention})", inline=True)
        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
        embed.add_field(name="Длительность:", value=f"{HasRole} (<t:{timestamp}:R>)", inline=True)
        embed.add_field(name="Выдано предупреждений:", value=f"{количество}", inline=True)
        embed.add_field(name="Всего предупреждений:", value=f"{warns_count}", inline=True)
        embed.add_field(name="Причина:", value=f"{reason} (случай #{server_value})", inline=False)
        embed.set_footer(text=f"ID участника: {участник.id}")
        await channel.send(embed=embed)

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="", color=0xffff00)
        embed.set_author(name=f"Вы получили {warning_word}!", icon_url=inter.guild.icon.url)
        embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
        embed.add_field(name="",
                        value=f"Вы получили {warning_word} ``#{warns_count}`` на сервере **{inter.guild.name}**",
                        inline=False)
        embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
        embed.add_field(name="Причина:", value=f"{reason} ", inline=False)
        embed.add_field(name="Истекает через:", value=f"``{HasRole}`` (<t:{timestamp}:R>)", inline=False)
        embed.add_field(name='Выдано предупреждений:', value=количество, inline=True)
        embed.add_field(name='Всего предупреждений:', value=warns_count, inline=True)
        embed.add_field(name="Подать апелляцию:", value=f"<#1044571685900259389>", inline=False)
        embed.set_footer(
            text="Пожалуйста, будьте внимательны! Последующие предупреждения могут привести к более строгим наказаниям.")
        message = await участник.send(embed=embed)

        def create_embed(dur, timestamp_mute):
            embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                                  description="", color=0xff8800)
            embed.set_author(name=f"Вы получили {warning_word} и были замучены",
                             icon_url=inter.guild.icon.url)
            embed.set_thumbnail(url="https://media4.giphy.com/media/4A2MFWNlGaGUJcyhlE/giphy.gif")
            embed.add_field(name="",
                            value=f"Вы получили {warning_word} ``#{warns_count}`` и были замучены на сервере {inter.guild.name}",
                            inline=False)
            embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
            embed.add_field(name=f"Длительность {warning_word}:", value=f"{HasRole} (<t:{timestamp}:R>)", inline=True)
            embed.add_field(name="Длительность мута:", value=f'{dur} (<t:{timestamp_mute}:R>)', inline=True)
            embed.add_field(name="Причина:", value=f"{reason} ", inline=False)
            embed.add_field(name='Выдано предупреждений:', value=количество, inline=True)
            embed.add_field(name='Всего предупреждений:', value=warns_count, inline=True)
            embed.add_field(name="Вам запрещено писать в текстовые каналы и подключаться к голосовым каналам:",
                            value=f"Поскольку количество предупреждений превышает: ``{warns_count}``", inline=False)
            embed.add_field(name="Подать апелляцию:", value=f"<#1044571685900259389>", inline=False)
            embed.set_footer(
                text="Пожалуйста, будьте внимательны! Последующие предупреждения могут привести к более строгим наказаниям.")
            return embed
        def create_embed_log(dur, timestamp_mute):
            embed = disnake.Embed(title="", url="",
                                  description="", color=0xff8800, timestamp=datetime.now())
            embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был замучен!",
                            inline=False)
            embed.set_thumbnail(
                url="https://media4.giphy.com/media/4A2MFWNlGaGUJcyhlE/giphy.gif")
            embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
            embed.add_field(name="Участник:", value=f"*{участник}* ({участник.mention})", inline=True)
            embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
            embed.add_field(name="Время:", value=f"{dur} (<t:{timestamp_mute}:R>)", inline=True)
            embed.add_field(name="Причина:", value=f"Поскольку количество предупреждений превышает {warns_count}", inline=True)
            embed.set_footer(text=f"ID участника: {участник.id}")
            return embed

        if moderator_role in участник.roles:
            if warns_count >= 5:
                await участник.remove_roles(moderator_role)
                embed = disnake.Embed(
                    description=f"У участника {участник.mention} было снято право модератора из-за получения {warns_count} предупреждений.",
                    colour=0xff0000,
                    timestamp=datetime.now()
                )
                embed.set_author(name=f"{inter.author.name}",
                                 icon_url=f"{inter.author.avatar}")
                embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
                embed.set_footer(text="Права модератора сняты")
                await channel.send(embed=embed)
        else:
            channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи
            if warns_count == 2:
                dur = '3 часа'
                timestamp_mute = int(datetime.now().timestamp() + 10800)
                duration = timedelta(hours=3)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 3:
                dur = '6 часов'
                timestamp_mute = int(datetime.now().timestamp() + 21600)
                duration = timedelta(hours=6)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 4:
                dur = '12 часов'
                timestamp_mute = int(datetime.now().timestamp() + 43200)
                duration = timedelta(hours=12)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 5:
                dur = '1 день'
                timestamp_mute = int(datetime.now().timestamp() + 86400)
                duration = timedelta(days=1)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 6:
                dur = '2 дня'
                timestamp_mute = int(datetime.now().timestamp() + 172800)
                duration = timedelta(days=2)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 7:
                dur = '3 дня'
                timestamp_mute = int(datetime.now().timestamp() + 259200)
                duration = timedelta(days=3)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 8:
                dur = '5 дней'
                timestamp_mute = int(datetime.now().timestamp() + 432000)
                duration = timedelta(days=5)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return
            elif warns_count == 9:
                dur = '7 дней'
                timestamp_mute = int(datetime.now().timestamp() + 604800)
                duration = timedelta(days=7)
                await участник.timeout(duration=duration)
                embed = create_embed(dur, timestamp_mute)
                await message.edit(embed=embed)
                embed = create_embed_log(dur, timestamp_mute)
                await channel.send(embed=embed)
                return

            elif warns_count >= 10:
                role = inter.guild.get_role(1229075137374978119)
                channel = inter.guild.get_channel(1042818334644768871)
                timestamp_ban = int(datetime.now().timestamp() + 2592000)
                collbans.update_one({'id': участник.id, 'guild_id': inter.guild.id},
                                    {"$set": {'Timestamp': timestamp_ban, 'ban': 'True', "reason": '10 предупреждений'}})
                await участник.add_roles(role)
                embed = disnake.Embed(title="ShadowDragons",
                                      url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif",
                                      description="", color=0xff0200)
                embed.set_author(name="Вы были заблокированы!", icon_url=inter.guild.icon.url)
                embed.set_thumbnail(url="https://i.imgur.com/o95uhru.gif")
                embed.add_field(name="", value=f"Вы были забанены на сервере **{inter.guild.name}**!",
                                inline=False)
                embed.add_field(name="Причина:",
                                value=f"Ваше количество предупреждений превышает: **10** (``{warns_count}``)",
                                inline=False)
                embed.add_field(name="Истекает через:", value=f"``30 дней`` (<t:{timestamp_ban}:R>)",
                                inline=True)
                embed.set_footer(text="Пожалуйста, больше не нарушайте!")
                await участник.send(embed=embed)

                return

    @commands.slash_command(name='unwarn', description='Позволяет снять предупреждение с игрока')
    async def unwarn(self, inter: disnake.GuildCommandInteraction, участник: disnake.Member,
                     предупреждение: int):
        if inter.type == disnake.InteractionType.application_command:
            await inter.response.defer(ephemeral=True)
            if collusers.count_documents({"id": участник.id, "guild_id": inter.guild.id,
                                          f'reasons.{предупреждение - 1}': {"$exists": True}}) == 0:

                embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
                embed.add_field(name=f'Ошибка', value=f'Предупреждения под номером ``{предупреждение}`` не существует.')
                embed.add_field(name="Попробуйте:", value=f'В параметр `предупреждение` передать существующее предупреждение.', inline=False)
                embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
                embed.set_footer(text="Ошибка")
                try:
                    await inter.edit_original_response(embed=embed)
                except:
                    await inter.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                collusers.update_one(
                    {"id": участник.id, "guild_id": inter.guild.id}, {'$unset': {f'reasons.{предупреждение - 1}': ""}})
                collusers.update_one(
                    {"id": участник.id, "guild_id": inter.guild.id},
                    {'$pull': {"reasons": None}})
                collusers.update_one({"id": участник.id, "guild_id": inter.guild.id}, {'$inc': {'warns': -1}})
                await участник.timeout(duration=None)

                role = inter.guild.get_role(1229075137374978119)
                if role in участник.roles:
                    await участник.remove_roles(role)
                    collbans.Update_one({"id": участник.id, "guild_id": inter.guild.id}, {"$set": {"ban": "False"}})

                embed = disnake.Embed(description=f"Предупреждение ``#{предупреждение}`` участника {участник.mention} было снято.", colour=0x00ff40, timestamp=datetime.now())
                embed.set_author(name=f"{inter.author.name}", icon_url=f"{inter.author.avatar}")
                embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                embed.set_footer(text="Анварн")
                try:
                    await inter.edit_original_response(embed=embed)
                except:
                    await inter.response.send_message(embed=embed)

                embed = disnake.Embed()
                embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf", description="", color=0x00ff40)
                embed.set_author(name=f'С Вас сняли предупреждение!', icon_url=inter.guild.icon.url)
                embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                embed.add_field(name="",value=f"Предупреждение ``#{предупреждение}`` на сервере **{inter.guild.name}** было снято\n **Модератором**: {inter.author.mention}!",inline=False)
                embed.set_footer(text="Приносим извинения за предоствленые неудобства!")
                await участник.send(embed=embed)

                channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

                embed = disnake.Embed(title="", url="",
                                      description="", color=0x00ff40, timestamp=datetime.now())
                embed.add_field(name="", value=f"С участника {участник.name} ({участник.mention}) было снято предупреждение ``#{предупреждение}``!",
                                inline=False)
                embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
                embed.add_field(name="Участник:", value=f"*{участник}* ({участник.mention})", inline=True)
                embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
                embed.set_footer(text=f"ID участника: {участник.id}")
                await channel.send(embed=embed)

    @commands.slash_command(name='warns', description='Показывает количество текущих предупреждений участника.')
    async def warns(self, inter: disnake.GuildCommandInteraction, участник: disnake.Member = None):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer(ephemeral=True)
            except:
                return
            usr = collusers.find_one({'id': inter.author.id, 'guild_id': inter.guild.id})
            if участник is not None:
                usr = collusers.find_one({'id': участник.id, 'guild_id': inter.guild.id})
            else:
                участник = inter.author

            user_data = collusers.find_one({'id': участник.id, 'guild_id': inter.guild.id})

            warns_count = user_data['warns']
            amount = 0
            if warns_count < 1:
                embed = disnake.Embed(title=f"Предупреждения участника **{участник.name}**:", url="",
                                      description="", color=0xffff00, timestamp=datetime.now())
                embed.set_author(name=f"{участник.name}",
                                 icon_url=f"{участник.avatar}")
                embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
                embed.add_field(name=f'', value=f'Предупреждения у участника {участник.mention} отсутствуют.', inline=False)
                try:
                    await inter.edit_original_response(embed=embed)
                except:
                    await inter.response.send_message(embed=embed, ephemeral=True)
                return
            embed = disnake.Embed(title=f"Предупреждения участника **{участник.name}**:", url="",
                                  description="", color=0xffff00, timestamp=datetime.now())
            embed.set_author(name=f"{участник.name}",
                             icon_url=f"{участник.avatar}")
            embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
            embed.add_field(name=f'', value=f'Количество предупреждений у **{участник.mention}**: ``{warns_count}``', inline=False)
            for value in usr['reasons']:
                amount = amount + 1
                embed.add_field(name=f"Предупреждение ``#{amount}``:", value=f'Причина: {value['reason']}', inline=False)
            try:
                await inter.edit_original_response(embed=embed)
            except:
                await inter.followup.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(WarnsCog(bot))
    print("WarnsCog is ready")
