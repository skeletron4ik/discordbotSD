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

    @tasks.loop(seconds=30)  # Проверка каждые 30 секунд
    async def check_warns(self):
        # Получение текущего времени
        current_timestamp = int(datetime.now().timestamp())

        # Поиск пользователей с истекшим временем предупреждения
        expired_warns = collusers.find({"причинаs.timestamp": {"$lte": current_timestamp}})

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

                    embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                                          description="**Модерация**",
                                          color=0x002aff)
                    embed.add_field(name="Снятие предупреждения", value="Срок вашего предупреждения истёк! ",
                                    inline=False)
                    embed.set_footer(text="Больше не нарушайте!")

                    member = guild.get_member(user["id"]) or await guild.fetch_member(user["id"])
                    if member:
                        await member.send(embed=embed)

    def get_rule_info(self, причина):
        print('im in get_rule_info')
        if причина in self.rules:
            reason = self.rules[str(причина)]
            print(reason)
            return reason
        else:
            reason = причина
            print('Я не зашел в условие.')
            return reason

    @check_warns.before_loop
    async def before_check_warns(self):
        await self.bot.wait_until_ready()  # Ожидание готовности бота перед запуском цикла

    @commands.slash_command(name="warn", description="Выдает предупреждение.")
    async def warn(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, количество: int, причина="Причина не указана."):
        if inter.response.is_done():
            return

        try:
            await inter.response.defer()
        except disnake.NotFound:
            return
        reason = self.get_rule_info(причина)

        if количество < 1: # Проверка на долбоеба
            exceptWarn = disnake.Embed()
            exceptWarn.add_field(name='**Произошла ошибка**', value='количество меньше чем 1', inline=True)
            exceptWarn.add_field(name='**Возможные пути решения**',
                                 value='В поле ```количество``` указать количество больше 1')
            exceptWarn.set_footer(text="Проверка на долбоеба сработала.")
            await inter.send(embed=exceptWarn, ephemeral=True)
            return

        role = inter.guild.get_role(757930494301044737)
        rolediamond = inter.guild.get_role(1044314368717897868)
        if role in участник.roles or rolediamond in участник.roles:
            timestamp = int(datetime.now().timestamp() + 1728000)
            HasRole = '20 дней'
        else:
            timestamp = int(datetime.now().timestamp() + 2592000)
            HasRole = '30 дней'

        print(timestamp)
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

        warns_count = collusers.find_one({"id": участник.id})["warns"]
        server_value = collservers.find_one({"_id": inter.guild.id})["case"]

        embedGive = disnake.Embed(title='Предупреждение выдано', color=0xae00ff)
        embedGive.add_field(name='**Участники интеракции:**',
                            value=f'Выдал: {inter.author.name} ({inter.author.mention})\nВыдано: {участник.name} ({участник.mention})',
                            inline=False)
        embedGive.add_field(name='**Подробная информация**',
                            value=f'Количество предупреждений у {участник.name} ({участник.mention}): {warns_count}\nВыдано предупреждений: {количество}\nСлучай: #{server_value}',
                            inline=False)

        await inter.send(embed=embedGive)  # Отправляем embed из переменной embedGive

        channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="**Модерация**", color=0xfbff00)
        embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) получил предупреждение", inline=False)
        embed.add_field(name="Модератор:", value=f"{inter.author.name} ({inter.author.mention})", inline=True)
        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
        embed.add_field(name="Длительность:", value=f"{HasRole} (<t:{timestamp}:R>)", inline=True)
        embed.add_field(name="Количество предупреждений:", value=f"{warns_count}", inline=True)
        embed.add_field(name="Причина:", value=f"{reason} (случай #{server_value})", inline=True)
        embed.set_footer(text=f"ID участника: {участник.id} • {current_datetime}")
        await channel.send(embed=embed)

        embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                              description="**Модерация**", color=0x001eff)
        embed.set_author(name="Внимание!",
                         icon_url="https://cdn.pixabay.com/animation/2023/04/28/18/34/18-34-10-554_512.gif")
        embed.add_field(name="", value=f"Вы получили предупреждение #{warns_count} на сервере {inter.guild.name}", inline=False)
        embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
        embed.add_field(name="Длительность:", value=f"{HasRole} <t:{timestamp}:R>", inline=False)
        embed.add_field(name='Выдано предупреждений:', value=количество, inline=True)
        embed.add_field(name='Количество предупреждений:', value=warns_count, inline=True)
        print(причина)
        embed.add_field(name="Причина:", value=f"{reason} ", inline=False)
        embed.set_footer(
            text="Пожалуйста, будьте внимательны! Последующие предупреждения могут привести к более строгим наказаниям.")
        message = await участник.send(embed=embed)




        def embed(dur):
            embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                                  description="**Модерация**", color=0xae00ff)
            embed.set_author(name="Вы были замьючены",
                             icon_url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
            embed.add_field(name="", value=f"Вы получили предупреждение #{warns_count} на сервере {inter.guild.name}",
                            inline=False)
            embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
            embed.add_field(name="Длительность:", value=f"{HasRole} <t:{timestamp}:R>", inline=False)
            embed.add_field(name='Выдано предупреждений:', value=количество, inline=True)
            embed.add_field(name='Количество предупреждений:', value=warns_count, inline=True)
            embed.add_field(name="Причина:", value=f"{reason} ", inline=False)
            embed.add_field(name="Вам запрещено писать в текстовые каналы и подключаться к голосовым каналам:",
                            value=f"Поскольку количество предупреждений: {warns_count}", inline=True)
            embed.add_field(name="Длительность:", value=dur, inline=True)
            embed.set_footer(
                text="Пожалуйста, будьте внимательны! Последующие предупреждения могут привести к более строгим наказаниям.")
            return embed

        if warns_count == 2:
            dur = '3 часа'
            duration = timedelta(hours=3)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 3:
            dur = '6 часа'
            duration = timedelta(hours=6)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 4:
            dur = '12 часов'
            duration = timedelta(hours=12)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 5:
            dur = '1 день'
            duration = timedelta(days=1)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 6:
            dur = '2 дня'
            duration = timedelta(days=2)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 7:
            dur = '3 дня'
            duration = timedelta(days=3)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 8:
            dur = '5 дней'
            duration = timedelta(days=5)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count == 9:
            dur = '7 дней'
            duration = timedelta(days=7)
            await участник.timeout(duration=duration)
            embed = embed(dur)
            await message.edit(embed=embed)
            return
        elif warns_count >= 10:
            role = inter.guild.get_role(1229075137374978119)
            channel = inter.guild.get_channel(1042818334644768871)
            await участник.add_roles(role)
            await участник.send(f'Вы были заблокированы на сервере навсегда! Поскольку у Вас десять предупреждений. Для подачи апелляции создайте тикет в {channel.mention}.')
            return

def setup(bot):
    bot.add_cog(WarnsCog(bot))
    print("ready")
