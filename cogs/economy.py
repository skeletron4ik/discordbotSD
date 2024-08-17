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
voice_timestamps = {}
mute_timestamps = {}
total_time = {}
emoji = "<:rumbick:1271089081601753118>"

def format_duration(value):
    if value == 1:
        return "1 румбик"
    elif 2 <= value <= 4:
        return f"`{value}` румбика"
    else:
        return f"`{value}` румбиков"
def format_rumbick(value):
    emoji = "<:rumbick:1271089081601753118>"
    return f"{value} {emoji}"

def create_error_embed(message: str) -> disnake.Embed:
    embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
    embed.add_field(name='Произошла ошибка', value=f'Ошибка: {message}')
    embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
    embed.set_footer(text='Ошибка')
    return embed



class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_booster.start()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            if message.channel.id == 1070322967634006057:
                if message.embeds:
                    message_embed = str(message.embeds[0].description)
                    if 'Bump done!' in str(
                            message_embed) or 'Время фиксации апа:' in message_embed or 'Ви успішно лайкнули сервер.' in message_embed or 'Вы успешно лайкнули сервер.' in message_embed:
                        author_interaction = message.interaction.author
                    elif 'Server bumped by' in message_embed:
                        mention_pattern = r"<@!?(\d+)>"
                        mentions = re.findall(mention_pattern, message_embed)
                        print(mentions[0])
                        author_interaction = await message.author.guild.fetch_member(mentions[0])
                        print(author_interaction)
                    collusers.find_one_and_update({'id': author_interaction.id}, {'$inc': {'balance': 5}})
                    embed = disnake.Embed(color=0x4169E1)
                    embed.add_field(name=f'**Успешный бамп!**',
                                    value=f'{author_interaction.mention}, Вы успешно бампнули сервер\n'
                                          f' и за это получаете `5` румбиков.')
                    embed.set_footer(text=f'Bumped by {author_interaction.display_name}',
                                     icon_url=author_interaction.avatar.url)
                    embed.set_author(name=message.author.guild.name, icon_url=message.author.guild.icon.url)
                    await message.channel.send(content=author_interaction.mention, embed=embed)
        else:
            now = datetime.now()
            user_id = message.author.id
            if len(message.content) > 3:

                if user_id in cooldowns:
                    last_used = cooldowns[user_id]
                    if now - last_used < timedelta(minutes=1):
                        time_left = timedelta(minutes=1) - (now - last_used)
                        return

                multiplier = collservers.find_one({'_id': message.author.guild.id})['multiplier']
                money_to_give = random.uniform(0.1, 1)
                money_to_give1 = money_to_give * multiplier
                money_to_give2 = round(money_to_give1, 2)
                collusers.find_one_and_update({'id': message.author.id}, {'$inc': {'balance': money_to_give2}})
                collusers.find_one_and_update({'id': message.author.id}, {'$inc': {'message_count': 1}})
                cooldowns[user_id] = now
                print(money_to_give2)
                print(money_to_give1)

    @commands.slash_command(name='balance', description='Показывает баланс участника',
                            aliases=['баланс', 'счет', 'остаток', 'credit', 'amount', 'sum'])
    async def balance(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member = None):
        await inter.response.defer()

        if участник is None:
            участник = inter.author

        user_data = collusers.find_one({"id": участник.id})
        if user_data:
            balance = round(user_data.get('balance', 0), 2)
            balance_formatted = format_rumbick(balance)

            embed = disnake.Embed(title=f'', color=0x00ff00)
            embed.set_author(name=f"{участник.display_name}", icon_url=f"{участник.avatar.url}")
            embed.set_thumbnail(
                url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
            embed.add_field(name='Баланс:', value=f'{balance_formatted}', inline=False)
            embed.set_footer(text=f'Баланс', icon_url=inter.guild.icon.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)
        else:
            await inter.edit_original_response(content="Не удалось найти данные пользователя.", ephemeral=True)

    @commands.slash_command(name='pay', description='Перевод румбиков другому участнику',
                            aliases=['перевод', 'give', 'transfer'])
    async def pay(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, количество: int):
        # Проверка на минимальную сумму перевода
        if количество < 10:
            error_message = "Вы не можете перевести меньше 10 румбиков."
            embed = create_error_embed(error_message)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        # Проверка на попытку перевести самому себе
        if участник.id == inter.author.id:
            embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
            error_message = "Вы не можете перевести румбики самому себе."
            embed = create_error_embed(error_message)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.defer()

        # Определение исключительных ролей на комиссию
        excluded_roles = {
            518505773022838797,  # Администратор
            580790278697254913,  # Гл. Модератор
            702593498901381184,  # Модератор
            1044314368717897868,  # Diamond
            757930494301044737  # Server Booster
        }

        balance = collusers.find_one({"id": inter.author.id})['balance']

        # Проверка на наличие роли-исключения у отправителя
        is_sender_excluded = any(role.id in excluded_roles for role in inter.author.roles)

        if balance >= количество:
            # Вычисление комиссии (если отправитель не исключен)
            if is_sender_excluded:
                amount_after_commission = количество
                commission_amount = 0
            else:
                commission = 0.05  # 5% комиссии
                amount_after_commission = количество * (1 - commission)
                commission_amount = количество - amount_after_commission

            # Обновление баланса отправителя и получателя
            collusers.find_one_and_update({'id': inter.author.id}, {"$inc": {"balance": -количество}})
            collusers.find_one_and_update({'id': участник.id}, {"$inc": {"balance": amount_after_commission}})
            collusers.find_one_and_update({'id': участник.id}, {'$inc': {'number_of_deal': 1}})
            collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'number_of_deal': 1}})

            formatted_amount = format_rumbick(количество)
            formatted_amount_after_commission = format_rumbick(amount_after_commission)
            formatted_commission_amount = format_rumbick(commission_amount)

            embed = disnake.Embed(title=f'Сделка `{inter.author.display_name}` ⇾ `{участник.display_name}`',
                                  color=0x00ff00)
            embed.set_author(name=f"{участник.display_name}", icon_url=f"{участник.avatar.url}")
            embed.set_thumbnail(
                url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
            embed.add_field(name='Отправитель', value=f'{inter.author.mention}', inline=True)
            embed.add_field(name='Получатель:', value=f'{участник.mention}', inline=True)
            embed.add_field(name='Сумма сделки:', value=f'{formatted_amount}', inline=True)

            if commission_amount > 0:
                embed.add_field(name='Комиссия:', value=f'5% ({formatted_commission_amount})', inline=True)
                embed.add_field(name='Итоговая сумма:', value=f'{formatted_amount_after_commission}', inline=True)
            else:
                embed.add_field(name='Комиссия:', value=f'0%', inline=True)

            embed.set_footer(text=f'Получатель: {участник.name}', icon_url=участник.avatar.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)

        else:
            unformatted = int(количество) - balance
            formatted = format_duration(unformatted)
            error_message = f"У Вас не хватает еще {formatted} для перевода."
            embed = create_error_embed(error_message)
            await inter.followup.send(embed=embed, ephemeral=True)

    @commands.slash_command(name='change-balance', description="Изменяет баланс участника", aliases=['деньги', 'givemoney', 'setmoney'])
    async def money(
            self,
            inter: disnake.ApplicationCommandInteraction,
            участник: disnake.Member,
            действие: str = commands.Param(choices=["добавить (+)", "отнять (-)", "установить (=)"]),
            количество: float = 0.0
    ):
        # Получение текущего баланса участника
        user_data = collusers.find_one({'id': участник.id})
        current_balance = round(user_data.get('balance', 0.0), 2)

        if действие == "добавить (+)":
            new_balance = round(current_balance + количество, 2)
            collusers.find_one_and_update({'id': участник.id}, {'$inc': {'balance': количество}})
            embed = disnake.Embed(title=f'', color=0x00ff00)
            embed.set_author(name=f"{inter.user.display_name}", icon_url=f"{inter.user.avatar.url}")
            embed.set_thumbnail(
                url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
            embed.add_field(name='', value=f'Вы **добавили** {количество}{emoji} к балансу {участник.mention}, теперь его текущий баланс {new_balance}{emoji}', inline=False)
            embed.set_footer(text=f'Баланс участника {участник.display_name} изменен', icon_url=участник.avatar.url)
            embed.timestamp = datetime.now()
            await inter.response.send_message(embed=embed, ephemeral=True)

        elif действие == "отнять (-)":
            new_balance = round(current_balance - количество, 2)
            collusers.find_one_and_update({'id': участник.id}, {'$inc': {'balance': -количество}})
            embed = disnake.Embed(title=f'', color=0x00ff00)
            embed.set_author(name=f"{inter.user.display_name}", icon_url=f"{inter.user.avatar.url}")
            embed.set_thumbnail(
                url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
            embed.add_field(name='', value=f'Вы **отняли** {количество}{emoji} от баланса {участник.mention}, теперь его текущий баланс {new_balance}{emoji}',
                            inline=False)
            embed.set_footer(text=f'Баланс участника {участник.display_name} изменен', icon_url=участник.avatar.url)
            embed.timestamp = datetime.now()
            await inter.response.send_message(embed=embed, ephemeral=True)

        elif действие == "установить (=)":
            new_balance = round(количество, 2)
            collusers.find_one_and_update({'id': участник.id}, {'$set': {'balance': количество}})
            embed = disnake.Embed(title=f'', color=0x00ff00)
            embed.set_author(name=f"{inter.user.display_name}", icon_url=f"{inter.user.avatar.url}")
            embed.set_thumbnail(
                url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
            embed.add_field(name='', value=f'Вы **установили** баланс {участник.mention} на {количество}{emoji}  ',
                            inline=False)
            embed.set_footer(text=f'Баланс участника {участник.display_name} изменен', icon_url=участник.avatar.url)
            embed.timestamp = datetime.now()
            await inter.response.send_message(embed=embed, ephemeral=True)

        channel = await self.bot.fetch_channel(944562833901899827)
        log_embed = disnake.Embed(title='', color=0x00ff00)
        log_embed.set_thumbnail(
            url="https://64.media.tumblr.com/31756ec986051798604d9697fa0e7d99/tumblr_pxuqjiK9Hn1sftgzko1_400.gif")
        log_embed.add_field(name=f'', value=f'Баланс участника **{участник.display_name}** был изменен', inline=False)
        log_embed.add_field(name='Администратор:', value=f'{inter.user.mention}', inline=True)
        log_embed.add_field(name='Участник:', value=f'{участник.mention}', inline=True)
        log_embed.add_field(name='',value='', inline=False)
        log_embed.add_field(name='Действие:', value=действие, inline=True)
        log_embed.add_field(name='Количество:', value=f'{количество}{emoji}', inline=True)
        log_embed.add_field(name='', value='', inline=False)
        log_embed.add_field(name='Баланс до изменения:', value=f'{current_balance}{emoji}', inline=True)
        log_embed.add_field(name='Текущий баланс:', value=f'{new_balance}{emoji}', inline=True)
        log_embed.set_footer(text=f'ID Участника: {участник.id}', icon_url=участник.avatar.url)
        log_embed.timestamp = datetime.now()
        await channel.send(embed=log_embed)


    @commands.slash_command(name='store', description='Магазин ролей и специальных возможностей за Румбики',
                            aliases=['shop', 'магазин', 'лавка', 'рынок'])
    async def store(self, inter: disnake.ApplicationCommandInteraction):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer(ephemeral=True)
            except:
                return
        diamond = inter.guild.get_role(1044314368717897868)
        user_data = collusers.find_one({"id": inter.author.id})
        if user_data:
            balance = round(user_data.get('balance', 0), 2)
            balance_formatted = format_rumbick(balance)
        else:
            balance_formatted = '0'
        embed = disnake.Embed(title='', color=0x4169E1)
        embed.set_author(name='Магазин сервера', icon_url=inter.guild.icon.url)
        embed.set_thumbnail(url='https://i.gifer.com/origin/63/6309237109affef229b14c3c5dc7308b_w200.gif')
        embed.add_field(name='Для просмотра дополнительной информации и цен о товаре, выберете его в выпадающем меню выбора товаров!', value=f'', inline=False)
        embed.add_field(name=f'**1. 💎 Diamond**',
                        value=f'Даёт эксклюзивные возможности. Подробнее с возможностями можно ознакомиться при выборе товара.\n**Цена покупки:** ``399``{emoji} | ``699``{emoji} | ``949``{emoji}\n **Содержит в себе:** Роль - {diamond.mention}',
                        inline=False)
        embed.add_field(name=f'**2. 🙋‍♂️ Смена никнейма**',
                        value=f'Даёт единоразовую возможность сменить свой отображаемый никнейм на сервере.\n**Цена покупки:** ``49``{emoji}\n**Содержит в себе:** Возможность смены __отображаемого__ никнейма на сервере.',
                        inline=False)
        embed.add_field(name=f'**3. 🚀 Глобальный бустер румбиков x2**',
                        value=f'Вдвое увеличивает зароботок с активнисти в голосовых каналах и текстовых чатах.\n**Цена покупки:** ``399``{emoji} | ``999``{emoji} | ``1899``{emoji}\n**Содержит в себе:** Глобальный бустер румбиков x2.',
                        inline=False)
        embed.add_field(name='', value='')
        embed.add_field(name='', value=f'**Ваш текущий баланс:** {balance_formatted}', inline=False)


        options = [
            disnake.SelectOption(label=f"💎 Diamond", description="Даёт эксклюзивные возможности", value="1"),
            disnake.SelectOption(label="🙋‍♂️ Возможность сменить никнейм",
                                 description="Вы получаете возможность один раз сменить никнейм",
                                 value="2"),
            disnake.SelectOption(label="🚀 Глобальный бустер румбиков x2",
                                 description="Увеличивает зароботок Румбиков вдвое", value="3"),
        ]

        # Создаем select menu
        select_menu = disnake.ui.Select(
            placeholder="Выбрать предмет для покупки...",
            min_values=1,
            max_values=1,
            options=options,
        )

        async def select_callback(interaction: disnake.MessageInteraction):
            global embed1
            if select_menu.values[0] == "1":
                embed1 = disnake.Embed(color=0x4169E1)
                embed1.set_author(name=f'Выберите длительность {diamond.name}', icon_url=inter.guild.icon.url)
                embed1.set_thumbnail(url='https://i.gifer.com/origin/63/6309237109affef229b14c3c5dc7308b_w200.gif')
                embed1.add_field(name='',
                                 value=f'{diamond.mention} - Привилегия на сервере, открывает недоступные для обычных пользователей функции.',
                                 inline=False)
                embed1.add_field(name='',
                                 value='```🟢 Отдельное отображение от остальных участников\n🟢 Голосовой канал, в который могут заходить только участники с этой ролью\n🟢 Доступ к Журналу аудита\n🟢 Возможность изменять свой никнейм\n🟢 На Вас не работает автомодерация сообщений\n🟢 Отключен кулдаун между использованиям команд\n🟢 При нарушениях длительность Ваших предупреждений уменьшается на 10 дней\n🟢 Комиссия 0% на перевод Румбиков```')
                embed1.add_field(name='', value='')
                embed1.add_field(name='**Стоимость**',
                                 value=f'* {diamond.mention}\n * {diamond.mention} (на 30 дней) - 399{emoji}\n * {diamond.mention} (на 60 дней) - ~~799~~ 699{emoji} **Скидка -15%**\n * {diamond.mention} (на 90 дней) - ~~1199~~ 949{emoji} **Скидка -20%**',
                                 inline=False)
                embed1.add_field(name='Обратите внимание:',
                                 value=f'Если у вас уже есть роль {diamond.mention}, при повторной покупке её срок действия будет продлён.',
                                 inline=False)
                embed1.add_field(name='', value='')
                embed1.add_field(name='', value=f'**Ваш текущий баланс:** {balance_formatted}', inline=False)

                components = [
                    disnake.ui.Button(label=f"💎 Купить на 30 дней", style=disnake.ButtonStyle.secondary,
                                      emoji=diamond.emoji, custom_id='30'),
                    disnake.ui.Button(label=f"💎 Купить на 60 дней", style=disnake.ButtonStyle.primary,
                                      emoji=diamond.emoji, custom_id='60'),
                    disnake.ui.Button(label=f"💎 Купить на 90 дней", style=disnake.ButtonStyle.green,
                                      emoji=diamond.emoji, custom_id='90')
                ]

                # Обрабатываем нажатие кнопки
                async def process_role(interaction, cost, duration, role_id, ephemeral=False):
                    user_id = interaction.author.id
                    guild_id = interaction.author.guild.id
                    diamond_role_id = 1044314368717897868  # Specific ID for the "Diamond" role

                    # Проверяем баланс
                    user_data = collusers.find_one({'id': user_id})
                    if user_data['balance'] < cost:
                        error_message = "У вас не хватает румбиков для покупки."
                        embed = create_error_embed(error_message)
                        await interaction.send(embed=embed, ephemeral=ephemeral)
                        return

                    # Обновляем баланс и сделки
                    collusers.update_many({'id': user_id}, {'$inc': {'number_of_deal': 1}})
                    collusers.find_one_and_update({'id': user_id}, {'$inc': {'balance': -cost}})

                    # Получаем роль по ID (Diamond)
                    role = disnake.utils.get(interaction.guild.roles, id=role_id)
                    if role is None:
                        error_message = "Роль не найдена. Пожалуйста свяжитесь с Администратором."
                        embed = create_error_embed(error_message)
                        await inter.response.send_message(embed=embed, ephemeral=True)
                        return

                    # Получаем пользователя (author of interaction)
                    member = interaction.author

                    # Вычисляем новый срок длительности роли
                    new_expiry = int((datetime.now() + timedelta(seconds=duration)).timestamp())

                    # Проверяем наличие роли Diamond у участника
                    if role.id == diamond_role_id and role in member.roles:
                        # Retrieve the current expiry time for the role from the database
                        role_info = collusers.find_one(
                            {"id": user_id, "guild_id": guild_id, "role_ids.role_ids": role.id},
                            {"role_ids.$": 1}
                        )
                        if role_info and "role_ids" in role_info:
                            current_expiry = role_info["role_ids"][0]["expires_at"]
                            remaining_time = max(0, current_expiry - int(datetime.now().timestamp()))
                            new_expiry = int(datetime.now().timestamp()) + remaining_time + duration

                        # Обновляем срок длительности роли в базе
                        collusers.update_one(
                            {"id": user_id, "guild_id": guild_id, "role_ids.role_ids": role.id},
                            {"$set": {"role_ids.$.expires_at": new_expiry}}
                        )
                        embed = disnake.Embed(
                            description=f"**Срок действия роли {role.name} продлен до:** <t:{new_expiry}:R>.\n ",
                            colour=0x00ff00,
                            timestamp=datetime.now()
                        )
                        embed.set_author(name="Срок действия роли продлен!",
                                         icon_url="https://i.imgur.com/vlX2dxG.gif")
                        embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                        embed.set_footer(text="Продление прошло успешно",
                                         icon_url=interaction.guild.icon.url)
                        await interaction.send(embed=embed, ephemeral=ephemeral)

                    else:
                        # Выдаем роль участнику
                        await interaction.author.add_roles(role)
                        embed = disnake.Embed(
                            description=f"**Вы приобрели роль {role.name}, которая заканчивается: <t:{new_expiry}:R>.\n Теперь Вам доступны следующие функции:**\n```🟢 Отдельное отображение от остальных участников\n🟢 Голосовой канал, в который могут заходить только участники с этой ролью\n🟢 Доступ к Журналу аудита\n🟢 Возможность изменять свой никнейм\n🟢 На Вас не работает автомодерация сообщений\n🟢 Отключен кулдаун между использованиям команд\n🟢 При нарушениях длительность Ваших предупреждений уменьшается на 10 дней\n🟢 Комиссия 0% на перевод Румбиков```",
                            colour=0x00ff00,
                            timestamp=datetime.now()
                        )
                        embed.set_author(name="Вы успешно приобрели роль Diamond!",
                                         icon_url="https://i.imgur.com/vlX2dxG.gif")
                        embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                        embed.set_footer(text="Покупка прошла успешно",
                                         icon_url=interaction.guild.icon.url)
                        await interaction.send(embed=embed, ephemeral=ephemeral)

                        # Обновляем базу с новой длительностью роли
                        collusers.update_one(
                            {"id": user_id, "guild_id": guild_id},
                            {
                                "$push": {"role_ids": {"role_ids": role.id, "expires_at": new_expiry}},
                                "$inc": {"number_of_roles": 1}
                            },
                            upsert=True
                        )

                    # Создаем и отправлем embed в логи
                    channel = await self.bot.fetch_channel(944562833901899827)
                    log_embed = disnake.Embed(color=0x00d5ff, timestamp=datetime.now())
                    log_embed.add_field(name="",
                                        value=f"Участник **{interaction.author.name}** ({interaction.author.mention}) получил роль ``{role.name}``",
                                        inline=False)
                    log_embed.set_thumbnail(
                        url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                    log_embed.add_field(name="Модератор:", value=f"**Магазин** ({interaction.author.mention})",
                                        inline=True)
                    log_embed.add_field(name="Канал:", value=f"{interaction.channel.mention}", inline=True)
                    log_embed.add_field(name="Длительность:", value=f"(<t:{new_expiry}:R>)", inline=True)
                    log_embed.set_footer(text=f"ID участника: {interaction.author.id}")
                    await channel.send(embed=log_embed)

                async def button_callback(interaction: disnake.MessageInteraction):
                    button_id = interaction.component.custom_id
                    diamond_role_id = 1044314368717897868  # ID роли "Diamond"

                    if button_id == '30':
                        await process_role(interaction, cost=399, duration=2678400, role_id=diamond_role_id,
                                           ephemeral=True)
                    elif button_id == '60':
                        await process_role(interaction, cost=699, duration=5097600, role_id=diamond_role_id,
                                           ephemeral=True)
                    elif button_id == '90':
                        await process_role(interaction, cost=949, duration=7776000, role_id=diamond_role_id,
                                           ephemeral=True)

                for button in components:
                    button.callback = button_callback

                view = disnake.ui.View(timeout=None)
                for button in components:
                    view.add_item(button)

                await interaction.response.send_message(embed=embed1, ephemeral=True, view=view)

            if select_menu.values[0] == "2":
                nikname_price = 49
                if collusers.find_one({'id': inter.author.id})['balance'] < nikname_price:
                    error_message = "У вас не хватает румбиков для покупки."
                    embed = create_error_embed(error_message)
                    await inter.edit_original_response(embed=embed)
                    return
                collusers.update_many({'id': inter.author.id}, {'$inc': {'number_of_deal': 1}})
                collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -nikname_price}})
                components = disnake.ui.TextInput(
                    label=f"Никнейм",
                    custom_id="nickname",
                    style=disnake.TextInputStyle.short,
                    placeholder="Введите новый никнейм",
                    required=True,
                    min_length=1,
                    max_length=32,
                )

                modal = disnake.ui.Modal(
                    title="Смена никнейма",
                    custom_id="my_modal",
                    components=[components]
                )
                await interaction.response.send_modal(modal=modal)


            if select_menu.values[0] == "3":
                global_booster_price_map = {
                    '1_day': 399,
                    '3_days': 999,
                    '7_days': 1899
                }

                options = [
                    disnake.ui.Button(label="🚀 Активировать на 1 день", style=disnake.ButtonStyle.secondary,
                                      custom_id='1_day'),
                    disnake.ui.Button(label="🚀 Активировать на 3 дня", style=disnake.ButtonStyle.primary, custom_id='3_days'),
                    disnake.ui.Button(label="🚀 Активировать на 7 дней", style=disnake.ButtonStyle.success, custom_id='7_days')
                ]

                def get_day_word(day_count):
                    if day_count == 1:
                        return 'день'
                    elif day_count in [2, 3, 4]:
                        return 'дня'
                    else:
                        return 'дней'

                async def button_callback(interaction: disnake.MessageInteraction):
                    button_id = interaction.component.custom_id
                    cost = global_booster_price_map[button_id]
                    duration_map = {
                        '1_day': 86400,
                        '3_days': 259200,
                        '7_days': 604800
                    }
                    duration = duration_map[button_id]
                    day_count = int(button_id.split('_')[0])

                    if collusers.find_one({'id': interaction.author.id})['balance'] < cost:
                        error_message = "У вас не хватает румбиков для покупки."
                        embed = create_error_embed(error_message)
                        await interaction.send(embed=embed, ephemeral=True)
                        return

                    # Получение данных сервера
                    server_data = collservers.find_one({'_id': interaction.author.guild.id})
                    current_timestamp = server_data['global_booster_timestamp']
                    current_time = int(datetime.now().timestamp())
                    admin_multiplier = server_data['admin_booster_multiplier']

                    if current_timestamp != 0 and current_timestamp > current_time:
                        # Продление бустера
                        new_timestamp = current_timestamp + duration
                        extend_embed = disnake.Embed(
                            description=f"**Срок действия активного глобального бустера Румбиков продлён на {day_count} {get_day_word(day_count)}.**\n Теперь все участники смогут дольше наслаждаться бустером.",
                            color=0x00ff00,
                            timestamp=datetime.now()
                        )
                        extend_embed.set_author(name="Бустер румбиков продлён!",
                                                icon_url="https://i.imgur.com/vlX2dxG.gif")
                        extend_embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                        extend_embed.set_footer(text="Покупка прошла успешно",
                                                icon_url=interaction.guild.icon.url)

                        await interaction.send(embed=extend_embed, ephemeral=True)

                        # Обновление списка активировавших бустер
                        collservers.find_one_and_update(
                            {'_id': interaction.author.guild.id},
                            {'$addToSet': {'global_booster_activated_by': interaction.author.id}}
                        )
                    else:
                        # Покупка бустера и обновление множителя
                        new_timestamp = current_time + duration
                        purchase_embed = disnake.Embed(
                            description=f"**Вы успешно приобрели бустер румбиков x2 на {day_count} {get_day_word(day_count)}.**\n Теперь все участники будут получать вдвое больше Румбиков за активность в чатах и голосовых каналах.",
                            color=0x00ff00,
                            timestamp=datetime.now()
                        )
                        purchase_embed.set_author(name="Бустер румбиков приобретён!",
                                                  icon_url="https://i.imgur.com/vlX2dxG.gif")
                        purchase_embed.set_thumbnail(url="https://www.emojiall.com/images/240/telegram/2705.gif")
                        purchase_embed.set_footer(text="Покупка прошла успешно",
                                                  icon_url=interaction.guild.icon.url)
                        await interaction.send(embed=purchase_embed, ephemeral=True)

                        # Проверка и обновление глобального множителя бустера
                        if admin_multiplier == 1 or admin_multiplier == 0:
                            new_multiplier = 2  # Если админский бустер 1x или 0x, то устанавливаем 2
                        else:
                            new_multiplier = admin_multiplier + 1  # Добавляем только 1 к текущему админскому множителю

                        collservers.find_one_and_update(
                            {'_id': interaction.author.guild.id},
                            {'$set': {'multiplier': new_multiplier}}
                        )

                        # Обновление списка активировавших бустер
                        collservers.find_one_and_update(
                            {'_id': interaction.author.guild.id},
                            {'$addToSet': {'global_booster_activated_by': interaction.author.id}}
                        )

                    # Обновление информации о бустере в базе данных
                    collservers.find_one_and_update(
                        {'_id': interaction.author.guild.id},
                        {
                            '$set': {
                                'global_booster_timestamp': new_timestamp,
                                'global_booster_multiplier': 2
                            }
                        }
                    )

                    # Обновление баланса пользователя и количества сделок
                    collusers.update_many({'id': interaction.author.id}, {'$inc': {'number_of_deal': 1}})
                    collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -cost}})

                    # Уведомление в канале сервера
                    channel = interaction.author.guild.get_channel(944562833901899827)
                    if current_timestamp != 0 and current_timestamp > current_time:
                        # Уведомление о продлении бустера
                        server_embed = disnake.Embed(
                            title="Бустер румбиков x2 продлён!",
                            description=f"{interaction.author.mention} продлил глобальный бустер румбиков ``x2`` на ``{day_count} {get_day_word(day_count)}``!\nНовый срок окончания бустера: <t:{new_timestamp}:R>.\n **Поблагодарим добряка в чате!**",
                            color=0x00ff00,
                            timestamp=datetime.now()
                        )
                        server_embed.set_author(name=f"{inter.user.display_name}", icon_url=f"{inter.user.avatar.url}")
                        server_embed.set_thumbnail(url='https://i.imgur.com/vlX2dxG.gif')
                        server_embed.set_footer(text=f'Продление глобального бустера', icon_url=inter.guild.icon.url)
                    else:
                        # Уведомление о покупке бустера
                        server_embed = disnake.Embed(
                            title="Бустер румбиков x2 активирован",
                            description=f"{interaction.author.mention} активировал глобальный бустер румбиков ``x2`` на ``{day_count} {get_day_word(day_count)}``!\nБустер закончится <t:{new_timestamp}:R>.\n **Поблагодарим добряка в чате!**",
                            color=0x00ff00,
                            timestamp=datetime.now()
                        )
                        server_embed.set_author(name=f"{inter.user.display_name}", icon_url=f"{inter.user.avatar.url}")
                        server_embed.set_thumbnail(url='https://i.imgur.com/vlX2dxG.gif')
                        server_embed.set_footer(text=f'Активация глобального бустера', icon_url=inter.guild.icon.url)
                    await channel.send(embed=server_embed)

                for button in options:
                    button.callback = button_callback

                view = disnake.ui.View(timeout=None)
                for button in options:
                    view.add_item(button)

                embed = disnake.Embed(color=0x4169E1)
                embed.set_author(name=f'Выберите длительность Бустера', icon_url=inter.guild.icon.url)
                embed.set_thumbnail(url='https://i.gifer.com/origin/63/6309237109affef229b14c3c5dc7308b_w200.gif')
                embed.add_field(name='', value='**Глобальный бустер румбиков** — Вдвое увеличивает заработок с активности в голосовых каналах и текстовых чатах.')
                embed.add_field(name='Выберите желаемую длительность для активации глобального бустера румбиков x2:',
                                value='', inline=False)
                embed.add_field(name='**Стоимость:**',
                                value=f'* Глобальный бустер х2\n * Бустер (на 1 день) - 399{emoji}\n * Бустер (на 3 дня) - ~~1200~~ 999{emoji} **Скидка -17%**\n * Бустер (на 7 дней) - ~~2799~~ 1899{emoji} **Скидка -33%**',
                                inline=False)
                embed.add_field(name='Обратите внимание:',
                                value=f'Если глобальный бустер румбиков уже активен, при повторной покупке его срок действия будет продлён.',
                                inline=False)
                embed.add_field(name='', value='')
                embed.add_field(name='', value=f'**Ваш текущий баланс:** {balance_formatted}', inline=False)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        select_menu.callback = select_callback

        # Создаем view и добавляем в него select menu
        view = disnake.ui.View()
        view.add_item(select_menu)

        # Отправляем сообщение с view

        await inter.edit_original_response(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global time_in_voice, multiplier

        if member.bot:
            return

        channel = member.guild.get_channel(944562833901899827)
        afk_channel_id = 516299058348818433
        now = int(datetime.now().timestamp())

        # Check if the user is in mute before entering the channel
        if after.channel is not None and after.self_mute and member.id not in mute_timestamps:
            mute_timestamps[member.id] = now

        # Mute status changed
        if before.self_mute != after.self_mute:
            if after.self_mute:
                mute_timestamps[member.id] = now
                print(f'{member} замутился в {now}')
            else:
                if member.id in mute_timestamps:
                    muted_duration = now - mute_timestamps.pop(member.id)
                    if member.id in total_time:
                        total_time[member.id] += muted_duration
                    else:
                        total_time[member.id] = muted_duration
                    print(f'{member} размутился в {now}, мьют продолжался {muted_duration} секунд')

        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            voice_timestamps[member.id] = now
            print(f'{member} зашел в войс в {now}')

        # User switched voice channels
        elif before.channel is not None and after.channel is not None:
            join_time = voice_timestamps.pop(member.id, None)
            if join_time:
                leave_time = now
                duration = leave_time - join_time

                # Calculate mute time
                if member.id in mute_timestamps:
                    muted_duration = leave_time - mute_timestamps.pop(member.id)
                    duration -= muted_duration
                    print(f'{member} сменил канал в {leave_time}, время мьюта {muted_duration}')

                if member.id in total_time:
                    total_time[member.id] += duration
                else:
                    total_time[member.id] = duration

                # Save time spent in previous channel before moving to AFK
                if after.channel.id == afk_channel_id:
                    minutes = round(duration / 60, 2)
                    rumbiks = round(duration / 60 * 0.1, 2)

                    multiplier = collservers.find_one({'_id': member.guild.id})['multiplier']
                    if rumbiks > 0.01:
                        collusers.find_one_and_update({'id': member.id}, {'$inc': {'balance': rumbiks * multiplier}})
                    if multiplier > 1:
                        rumbikswithboost = rumbiks * multiplier
                    else:
                        rumbikswithboost = None
                    collusers.find_one_and_update({'id': member.id}, {'$inc': {'time_in_voice': minutes}})
                    time_in_voice = collusers.find_one({'id': member.id})['time_in_voice']

                    # Prepare time format in seconds, minutes, and hours
                    hours, rem = divmod(total_time[member.id], 3600)
                    minutes, seconds = divmod(rem, 60)

                    embed = disnake.Embed(color=0xe70404)
                    embed.add_field(
                        name='**Голосовая активность**',
                        value=(
                            f'Участник: `{member.display_name}` ({member.mention})\n'
                            f'Время в войсе: с <t:{join_time}:T> до <t:{leave_time}:T>\n'
                            f'Время в войсе (без учёта мута): `{duration} секунд`\n'
                            f'Общее время в войсе: `{int(hours)} ч, {int(minutes)} мин, {int(seconds)} сек`\n'
                            f'Выданные румбики: `{rumbiks}`\n'
                            f'{f"Выданные румбики с учетом бустера `{rumbikswithboost}`" if multiplier > 1 else ""}\n'
                            f'Общее время в войсе: `{time_in_voice}` минут'
                        )
                    )
                    embed.set_footer(text=member.name, icon_url=member.avatar.url)
                    embed.set_author(name='Shadow Dragons Economy', icon_url=member.guild.icon.url)
                    thread = member.guild.get_thread(1270673733178101801)
                    await thread.send(embed=embed)
                voice_timestamps[member.id] = now

        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            join_time = voice_timestamps.pop(member.id, None)
            if join_time:
                leave_time = now
                duration = leave_time - join_time

                # Calculate mute time
                if member.id in mute_timestamps:
                    muted_duration = leave_time - mute_timestamps.pop(member.id)
                    duration -= muted_duration
                    print(f'{member} вышел из войса в {leave_time}, время мьюта {muted_duration}')

                if member.id in total_time:
                    total_time[member.id] += duration
                else:
                    total_time[member.id] = duration

                # Handle leaving voice channel other than AFK
                if before.channel.id != afk_channel_id:
                    minutes = round(total_time[member.id] / 60, 2)
                    rumbiks = round(duration / 60 * 0.1, 2)

                    multiplier = collservers.find_one({'_id': member.guild.id})['multiplier']
                    if rumbiks > 0.01:
                        collusers.find_one_and_update({'id': member.id}, {'$inc': {'balance': rumbiks * multiplier}})
                    if multiplier > 1:
                        rumbikswithboost = rumbiks * multiplier
                    else:
                        rumbikswithboost = None
                    collusers.find_one_and_update({'id': member.id}, {'$inc': {'time_in_voice': minutes}})
                    time_in_voice = collusers.find_one({'id': member.id})['time_in_voice']

                    # Prepare time format in seconds, minutes, and hours
                    hours, rem = divmod(total_time[member.id], 3600)
                    minutes, seconds = divmod(rem, 60)

                    embed = disnake.Embed(color=0xe70404)
                    embed.add_field(
                        name='**Голосовая активность**',
                        value=(
                            f'Участник: `{member.display_name}` ({member.mention})\n'
                            f'Время в войсе: с <t:{join_time}:T> до <t:{leave_time}:T>\n'
                            f'Время в войсе (без учёта мута): `{duration} секунд`\n'
                            f'Общее время в войсе: `{int(hours)} ч, {int(minutes)} мин, {int(seconds)} сек`\n'
                            f'Выданные румбики: `{rumbiks}`\n'
                            f'{f"Выданные румбики с учетом бустера `{rumbikswithboost}`" if multiplier > 1 else ""}\n'
                            f'Общее время в войсе: `{time_in_voice}` минут'
                        )
                    )
                    embed.set_footer(text=member.name, icon_url=member.avatar.url)
                    embed.set_author(name='Shadow Dragons Economy', icon_url=member.guild.icon.url)
                    thread = member.guild.get_thread(1270673733178101801)
                    await thread.send(embed=embed)
            else:
                print(f'{member} вышел из войса, но время входа не найдено.')

    class TopEnum(disnake.enums.Enum):
        Румбики = "Румбики"

    def get_top_users(self):
        top_records = collusers.find().sort('balance', -1).limit(10)
        return [(record['id'], record['balance']) for record in top_records]

    @commands.slash_command(name='top', description='Топ пользователи', aliases=['топ', 'лучшие'])
    async def top(self, inter: disnake.ApplicationCommandInteraction,
                  тип: TopEnum = commands.Param(description="Выберите тип топа")):
        if тип == 'Румбики':
            embed = disnake.Embed(title="Топ участников по румбикам", description="", color=0x4169E1)
            top_records = collusers.find().sort('balance', -1).limit(10)
            top_users = self.get_top_users()
            for idx, (user_id, balance) in enumerate(top_users, start=1):
                member = inter.guild.get_member(user_id)
                if member:
                    balance = round(balance, 2)
                    embed.add_field(name=f"{idx}. {member.display_name}", value=f"Баланс: {balance}", inline=False)
                else:
                    balance = round(balance, 2)
                    embed.add_field(name=f"{idx}. Неизвестный участник (ID: {user_id})", value=f"Баланс: {balance}",
                                    inline=False)

            await inter.response.send_message(embed=embed, ephemeral=True)

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
            raise ValueError(f"Invalid time unit: {time_str[-1]}")

    @tasks.loop(seconds=60)
    async def check_booster(self):
        server_id = 489867322039992320
        server_data = collservers.find_one({'_id': server_id})

        timestamp_booster = server_data['booster_timestamp']
        global_timestamp_booster = server_data['global_booster_timestamp']
        global_booster_multiplier = server_data['global_booster_multiplier']
        admin_booster_multiplier = server_data['admin_booster_multiplier']
        timestamp_now = int(datetime.now().timestamp())

        # Проверяем, истек ли админский бустер, но глобальный не активен
        if timestamp_booster != 0 and global_timestamp_booster == 0:
            if timestamp_booster < timestamp_now:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_activated_by': []}})
                print('Admin booster expired, no global booster active.')
                return

        # Проверяем, истек ли глобальный бустер, но админский не активен
        elif timestamp_booster == 0 and global_timestamp_booster != 0:
            if timestamp_now > global_timestamp_booster:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_activated_by': []}})
                print('Global booster expired, no admin booster active.')
                return

        # Проверяем, истекли ли оба бустера
        elif timestamp_booster != 0 and global_timestamp_booster != 0:
            if timestamp_now > global_timestamp_booster and timestamp_now > timestamp_booster:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_activated_by': []}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_activated_by': []}})
                print('Both boosters expired.')
                return

            # Проверяем, истек ли глобальный бустер, но админский еще активен
            elif timestamp_now > global_timestamp_booster and timestamp_now < timestamp_booster:
                new_multiplier = admin_booster_multiplier  # Устанавливаем множитель равный admin_booster_multiplier
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': new_multiplier}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_activated_by': []}})
                print('Global booster expired, admin booster still active.')
                return

            # Проверяем, истек ли админский бустер, но глобальный еще активен
            elif timestamp_now > timestamp_booster and timestamp_now < global_timestamp_booster:
                new_multiplier = global_booster_multiplier  # Устанавливаем множитель равный global_booster_multiplier
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': new_multiplier}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_activated_by': []}})
                print('Admin booster expired, global booster still active.')
                return

        # Новые условия: если админский бустер истекает, заменить multiplier на global_booster_multiplier
        if timestamp_booster != 0 and timestamp_now > timestamp_booster:
            if global_timestamp_booster == 0 or timestamp_now > global_timestamp_booster:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': 1}})
            else:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': global_booster_multiplier}})

            collservers.find_one_and_update({'_id': server_id}, {'$set': {'booster_timestamp': 0}})
            collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_multiplier': 0}})
            collservers.find_one_and_update({'_id': server_id}, {'$set': {'admin_booster_activated_by': []}})
            print('Admin booster expired.')
            return

        # Новые условия: если глобальный бустер истекает, заменить multiplier на admin_booster_multiplier
        if global_timestamp_booster != 0 and timestamp_now > global_timestamp_booster:
            if timestamp_booster == 0 or timestamp_now > timestamp_booster:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': 1}})
            else:
                collservers.find_one_and_update({'_id': server_id}, {'$set': {'multiplier': admin_booster_multiplier}})

            collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_timestamp': 0}})
            collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_multiplier': 0}})
            collservers.find_one_and_update({'_id': server_id}, {'$set': {'global_booster_activated_by': []}})
            print('Global booster expired.')
            return

    @commands.slash_command(name='booster', description='Включает бустер румбиков')
    async def booster(self, inter: disnake.ApplicationCommandInteraction, multiplier: int, expiry: str):
        try:
            expiry = self.convert_to_seconds(expiry)
        except:
            embed = disnake.Embed(color=0xe70404)
            embed.add_field(name='Произошла ошибка', value='Ошибка в конвертации в секунды')
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        timestamp = int(datetime.now().timestamp()) + expiry
        server_data = collservers.find_one({'_id': inter.author.guild.id})
        global_booster_active = server_data['global_booster_timestamp'] != 0 and server_data[
            'global_booster_timestamp'] > int(datetime.now().timestamp())

        if global_booster_active:
            # Уменьшаем общий множитель на 1 при активном глобальном бустере
            new_multiplier = server_data['multiplier'] + int(multiplier) - 1
        else:
            new_multiplier = int(multiplier)

        collservers.find_one_and_update(
            {'_id': inter.author.guild.id},
            {
                '$set': {
                    'multiplier': new_multiplier,
                    'booster_timestamp': int(timestamp),
                    'admin_booster_multiplier': int(multiplier)
                },
                '$addToSet': {'admin_booster_activated_by': inter.author.id}
            }
        )

        embed = disnake.Embed(color=0x4169E1)
        embed.add_field(name='**Бустер активирован**',
                        value=f'Множитель: {multiplier}\n Общий множитель: {new_multiplier}\nДата окончания: <t:{timestamp}:R>')
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="boosters", description="Показывает текущие активные бустеры")
    async def boosters(self, inter: disnake.ApplicationCommandInteraction):
        server_id = inter.guild_id
        server_data = collservers.find_one({'_id': server_id})

        # Извлечение информации о бустерах
        admin_booster_multiplier = server_data.get('admin_booster_multiplier', 0)
        admin_booster_activated_by = server_data.get('admin_booster_activated_by', [])
        booster_timestamp = server_data.get('booster_timestamp', 0)

        global_booster_multiplier = server_data.get('global_booster_multiplier', 0)
        global_booster_activated_by = server_data.get('global_booster_activated_by', [])
        global_booster_timestamp = server_data.get('global_booster_timestamp', 0)

        multiplier = server_data.get('multiplier', 1)


        embed = disnake.Embed(title="Активные Бустеры Румбиков на данный момент:", color=0x00ff00)
        embed.set_thumbnail(url='https://i.imgur.com/vlX2dxG.gif')
        embed.set_footer(text=f'Активные бустеры румбиков', icon_url=inter.guild.icon.url)
        embed.timestamp = datetime.now()

        # Серверный бустер (администраторский)
        if booster_timestamp > int(datetime.now().timestamp()):
            users_admin_booster = ', '.join([f'<@{user_id}>' for user_id in admin_booster_activated_by])
            time_remaining_admin = f"<t:{booster_timestamp}:R>"
            embed.add_field(
                name="Ивентовый бустер:",
                value=f"**Активировал:** {users_admin_booster}\n"
                      f"**Множитель:** ``x{admin_booster_multiplier}``\n"
                      f"**Истекает через:** {time_remaining_admin}",
                inline=False
            )

        # Глобальный бустер
        if global_booster_timestamp > int(datetime.now().timestamp()):
            users_global_booster = ', '.join([f'<@{user_id}>' for user_id in global_booster_activated_by])
            time_remaining_global = f"<t:{global_booster_timestamp}:R>"
            embed.add_field(
                name="Глобальный бустер",
                value=f"**Активировал:** {users_global_booster}\n"
                      f"**Множитель:** ``x{global_booster_multiplier}``\n"
                      f"**Истекает через:** {time_remaining_global}",
                inline=False
            )
            embed.add_field(name='', value='')

        # Общий множитель
        embed.add_field(
            name="",
            value=f"```Текущий общий множитель: x{multiplier}```",
            inline=False
        )

        # Если нет активных бустеров
        if len(embed.fields) == 1:  # Only the multiplier field exists
            embed.description = "На данный момент нет активных бустеров."
            embed.clear_fields()  # Clear the multiplier field if no boosters are active

        await inter.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "my_modal":
            nickname = inter.text_values["nickname"]
            await inter.author.edit(nick=nickname)
            await inter.response.send_message('Никнейм изменён.', ephemeral=True)
        elif inter.custom_id == "knb":
            figure = inter.text_values['figurez']
            decline = disnake.utils.get(inter.author.guild.emojis, name='773229388573310996')
            if figure == 'К' or figure == 'Н' or figure == 'Б':

                bet = inter.text_values['bet']
                message = await inter.response.send_message('В процессе..')
                balance = collusers.find_one({'id': inter.author.id})['balance']
                cost = bet
                cost = int(cost)
                bet = format_duration(int(bet))
                author = inter.author
                if cost < 10:
                    await inter.response.send_message(
                        f'{decline}  `{inter.author.display_name}`, не указывайте значения от **0** до **10**.',
                        ephemeral=True)
                    return
                if balance < cost:
                    err = format_duration(cost - balance)
                    await inter.response.send_message(f'{decline}  `{inter.author.display_name}`, Вам не хватает {err}.',
                                                      ephemeral=True)
                    return
                collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': -cost}})
                embed = disnake.Embed(title='Rock-Paper-Scissors', color=0x4169E1)
                embed.set_author(name=inter.author.guild.name, icon_url=inter.author.guild.icon.url)
                embed.set_footer(text=f'Использовал команду: `{inter.author.id}`', icon_url=inter.author.avatar.url)
                embed.add_field(name='Информация об игре', value=f'Ставка: {bet}', inline=True)

                options = [
                    disnake.SelectOption(label='🎱 Камень', description="Фигура камень", value="1"),
                    disnake.SelectOption(label="🧻 Бумага",
                                         description="Фигура ножницы",
                                         value="2"),
                    disnake.SelectOption(label="✂ Ножницы",
                                         description="Фигура бумага", value="3"),
                ]

                # Создаем select menu
                select_menu = disnake.ui.Select(
                    placeholder="Выбрать фигуру..",
                    min_values=1,
                    max_values=1,
                    options=options,
                )

                async def select_callback(interaction: disnake.MessageInteraction):
                    balance_interaction = collusers.find_one({'id': interaction.author.id})['balance']
                    if author.id == interaction.author.id:
                        await interaction.response.send_message(
                            f'{decline} `{interaction.author.display_name}`, Вы не можете играть сами с собой.',
                            ephemeral=True)
                        return
                    if collusers.find_one({'id': interaction.author.id})['balance'] < cost:
                        err = format_duration(cost - balance_interaction)
                        await interaction.response.send_message(
                            f'{decline} `{interaction.author.display_name}`, Вам не хватает {err}.', ephemeral=True)
                        return
                    collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -cost}})
                    if select_menu.values[0] == "1":  # Первый выбор игрока
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на камень, поэтому ичья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал бумагу, а {interaction.author.mention} выбрал камень.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{interaction.author.mention} выбрал камень, а {author.mention} выбрал ножницы.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)

                    elif select_menu.values[0] == "2":  # Второй выбор игрока
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{interaction.author.mention} выбрал камень, а {author.mention} выбрал ножницы.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на бумагу, поэтому ничья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал ножницы, а {interaction.author.mention} выбрал бумагу.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)

                    elif select_menu.values[0] == "3":  # Третий выбор игрока (предположим, что это "Ножницы")
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал камень, а {interaction.author.mention} выбрал ножницы.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{interaction.author.mention} выбрал ножницы, а {author.mention} выбрал бумагу.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost * 2}})
                            await inter.edit_original_response(embed=embed, view=None)
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на ножницы, поэтому ничья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})
                            await inter.edit_original_response(embed=embed, view=None)

                select_menu.callback = select_callback

                # Создаем view и добавляем в него select menu
                view = disnake.ui.View(timeout=None)
                view.add_item(select_menu)

                await inter.edit_original_message(embed=embed, view=view, content=None)
            else:
                await inter.response.send_message(
                    f'{decline} {inter.author.display_name}, Вы выбрали не существующую фигуру.', ephemeral=True)
                return

    class FigureEnum(disnake.enums.Enum):
        Камень = "Камень"
        Ножницы = "Ножницы"
        Бумага = "Бумага"
    @commands.slash_command(name='rps', description='Популярная игра, камень-ножницы-бумага')
    async def rps(self, inter: disnake.ApplicationCommandInteraction):
        components = disnake.ui.TextInput(
            label=f"Выбери фигуру",
            custom_id="figurez",
            style=disnake.TextInputStyle.short,
            placeholder="К, Н, Б",
            required=True,
            min_length=1,
            max_length=1,
        )

        betz = disnake.ui.TextInput(
            label=f"Ставка",
            custom_id="bet",
            style=disnake.TextInputStyle.short,
            placeholder="10",
            required=True,
            min_length=1,
            max_length=16,
        )

        modal = disnake.ui.Modal(
            title="Rock-Paper-Scissors",
            custom_id="knb",
            components=[components, betz]
        )

        await inter.response.send_modal(modal=modal)


    @commands.slash_command(name='embed')
    async def embed(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(description=f'**Успешный Up!**\n'
                                          f'Время фиксации апа:')
        await inter.response.send_message(embed=embed)

    @commands.user_command(name='balance', dm_permission=False, nsfw=True)
    async def balinuser(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        await self.balance(inter, user)

def setup(bot):
    bot.add_cog(EconomyCog(bot))
    print("EconomyCog is ready")
